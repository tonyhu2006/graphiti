"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import logging
import typing
from typing import TYPE_CHECKING, ClassVar

import aiohttp
from pydantic import BaseModel

from ..prompts.models import Message
from .client import MULTILINGUAL_EXTRACTION_RESPONSES, LLMClient
from .config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from .errors import RateLimitError

if TYPE_CHECKING:
    from google import genai
    from google.genai import types
else:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        # If gemini client is not installed, raise an ImportError
        raise ImportError(
            'google-genai is required for GeminiClient. '
            'Install it with: pip install graphiti-core[google-genai]'
        ) from None


logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gemini-2.5-flash'
DEFAULT_SMALL_MODEL = 'models/gemini-2.5-flash-lite-preview-06-17'


class GeminiClient(LLMClient):
    """
    GeminiClient is a client class for interacting with Google's Gemini language models.

    This class extends the LLMClient and provides methods to initialize the client
    and generate responses from the Gemini language model.

    Attributes:
        model (str): The model name to use for generating responses.
        temperature (float): The temperature to use for generating responses.
        max_tokens (int): The maximum number of tokens to generate in a response.
        thinking_config (types.ThinkingConfig | None): Optional thinking configuration for models that support it.
    Methods:
        __init__(config: LLMConfig | None = None, cache: bool = False, thinking_config: types.ThinkingConfig | None = None):
            Initializes the GeminiClient with the provided configuration, cache setting, and optional thinking config.

        _generate_response(messages: list[Message]) -> dict[str, typing.Any]:
            Generates a response from the language model based on the provided messages.
    """

    # Class-level constants
    MAX_RETRIES: ClassVar[int] = 2

    def __init__(
        self,
        config: LLMConfig | None = None,
        cache: bool = False,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        thinking_config: types.ThinkingConfig | None = None,
        client: 'genai.Client | None' = None,
    ):
        """
        Initialize the GeminiClient with the provided configuration, cache setting, and optional thinking config.

        Args:
            config (LLMConfig | None): The configuration for the LLM client, including API key, model, temperature, and max tokens.
            cache (bool): Whether to use caching for responses. Defaults to False.
            thinking_config (types.ThinkingConfig | None): Optional thinking configuration for models that support it.
                Only use with models that support thinking (gemini-2.5+). Defaults to None.
            client (genai.Client | None): An optional async client instance to use. If not provided, a new genai.Client is created.
        """
        if config is None:
            config = LLMConfig()

        super().__init__(config, cache)

        self.model = config.model

        if client is None:
            # Check if base_url is provided for custom endpoints (like Gemini Balance)
            if config.base_url:
                # For custom endpoints, we'll use a different approach
                # Store the base_url for later use in API calls
                self.base_url = config.base_url
                self.use_custom_endpoint = True
                # Still create a genai client for fallback, but we'll override the API calls
                self.client = genai.Client(api_key=config.api_key)
            else:
                self.base_url = None
                self.use_custom_endpoint = False
                self.client = genai.Client(api_key=config.api_key)
        else:
            self.client = client
            self.base_url = getattr(config, 'base_url', None)
            self.use_custom_endpoint = bool(self.base_url)

        self.max_tokens = max_tokens
        self.thinking_config = thinking_config

    async def _call_custom_endpoint(
        self,
        messages: list[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        response_model: type[BaseModel] | None = None,
    ) -> dict[str, typing.Any]:
        """
        Call a custom endpoint (like Gemini Balance) using OpenAI-compatible API format.

        Args:
            messages: List of messages to send
            model: Model name to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            response_model: Optional Pydantic model for structured output

        Returns:
            Response dictionary
        """
        # Convert Graphiti messages to OpenAI format
        openai_messages = []
        system_message = None

        for message in messages:
            if message.role == "system":
                system_message = message.content
            else:
                openai_messages.append({
                    "role": message.role,
                    "content": message.content
                })

        # If we have a system message, add it as the first message
        if system_message:
            openai_messages.insert(0, {
                "role": "system",
                "content": system_message
            })

        # Prepare the request payload
        payload = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add response format for structured output
        if response_model:
            payload["response_format"] = {"type": "json_object"}

        # Make the API call
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        # Use the OpenAI-compatible endpoint
        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API call failed with status {response.status}: {error_text}")

                result = await response.json()

                # Extract the content from OpenAI format response
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]

                    # Try to parse as JSON if response_model is specified
                    if response_model:
                        try:
                            parsed_content = json.loads(content)
                            return parsed_content
                        except json.JSONDecodeError:
                            # If JSON parsing fails, return the raw content
                            return {"content": content}
                    else:
                        return {"content": content}
                else:
                    raise Exception("No valid response received from API")

    def _check_safety_blocks(self, response) -> None:
        """Check if response was blocked for safety reasons and raise appropriate exceptions."""
        # Check if the response was blocked for safety reasons
        if not (hasattr(response, 'candidates') and response.candidates):
            return

        candidate = response.candidates[0]
        if not (hasattr(candidate, 'finish_reason') and candidate.finish_reason == 'SAFETY'):
            return

        # Content was blocked for safety reasons - collect safety details
        safety_info = []
        safety_ratings = getattr(candidate, 'safety_ratings', None)

        if safety_ratings:
            for rating in safety_ratings:
                if getattr(rating, 'blocked', False):
                    category = getattr(rating, 'category', 'Unknown')
                    probability = getattr(rating, 'probability', 'Unknown')
                    safety_info.append(f'{category}: {probability}')

        safety_details = (
            ', '.join(safety_info) if safety_info else 'Content blocked for safety reasons'
        )
        raise Exception(f'Response blocked by Gemini safety filters: {safety_details}')

    def _check_prompt_blocks(self, response) -> None:
        """Check if prompt was blocked and raise appropriate exceptions."""
        prompt_feedback = getattr(response, 'prompt_feedback', None)
        if not prompt_feedback:
            return

        block_reason = getattr(prompt_feedback, 'block_reason', None)
        if block_reason:
            raise Exception(f'Prompt blocked by Gemini: {block_reason}')

    def _get_model_for_size(self, model_size: ModelSize) -> str:
        """Get the appropriate model name based on the requested size."""
        if model_size == ModelSize.small:
            return self.small_model or DEFAULT_SMALL_MODEL
        else:
            return self.model or DEFAULT_MODEL

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        """
        Generate a response from the Gemini language model.

        Args:
            messages (list[Message]): A list of messages to send to the language model.
            response_model (type[BaseModel] | None): An optional Pydantic model to parse the response into.
            max_tokens (int): The maximum number of tokens to generate in the response.
            model_size (ModelSize): The size of the model to use (small or medium).

        Returns:
            dict[str, typing.Any]: The response from the language model.

        Raises:
            RateLimitError: If the API rate limit is exceeded.
            Exception: If there is an error generating the response or content is blocked.
        """
        try:
            # Get the appropriate model for the requested size
            model = self._get_model_for_size(model_size)

            # Check if we should use custom endpoint
            if self.use_custom_endpoint and self.base_url:
                return await self._call_custom_endpoint(
                    messages=messages,
                    model=model,
                    temperature=self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    response_model=response_model,
                )

            # Original Gemini API implementation
            gemini_messages: typing.Any = []
            # If a response model is provided, add schema for structured output
            system_prompt = ''
            if response_model is not None:
                # Get the schema from the Pydantic model
                pydantic_schema = response_model.model_json_schema()

                # Create instruction to output in the desired JSON format
                system_prompt += (
                    f'Output ONLY valid JSON matching this schema: {json.dumps(pydantic_schema)}.\n'
                    'Do not include any explanatory text before or after the JSON.\n\n'
                )

            # Add messages content
            # First check for a system message
            if messages and messages[0].role == 'system':
                system_prompt = f'{messages[0].content}\n\n {system_prompt}'
                messages = messages[1:]

            # Add the rest of the messages
            for m in messages:
                m.content = self._clean_input(m.content)
                gemini_messages.append(
                    types.Content(role=m.role, parts=[types.Part.from_text(text=m.content)])
                )

            # Create generation config
            generation_config = types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=max_tokens or self.max_tokens,
                response_mime_type='application/json' if response_model else None,
                response_schema=response_model if response_model else None,
                system_instruction=system_prompt,
                thinking_config=self.thinking_config,
            )

            # Generate content using the simple string approach
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=gemini_messages,
                config=generation_config,
            )

            # Check for safety and prompt blocks
            self._check_safety_blocks(response)
            self._check_prompt_blocks(response)

            # If this was a structured output request, parse the response into the Pydantic model
            if response_model is not None:
                try:
                    if not response.text:
                        raise ValueError('No response text')

                    validated_model = response_model.model_validate(json.loads(response.text))

                    # Return as a dictionary for API consistency
                    return validated_model.model_dump()
                except Exception as e:
                    raise Exception(f'Failed to parse structured response: {e}') from e

            # Otherwise, return the response text as a dictionary
            return {'content': response.text}

        except Exception as e:
            # Check if it's a rate limit error based on Gemini API error codes
            error_message = str(e).lower()
            if (
                'rate limit' in error_message
                or 'quota' in error_message
                or 'resource_exhausted' in error_message
                or '429' in str(e)
            ):
                raise RateLimitError from e

            logger.error(f'Error in generating LLM response: {e}')
            raise

    async def generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int | None = None,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        """
        Generate a response from the Gemini language model with retry logic and error handling.
        This method overrides the parent class method to provide a direct implementation with advanced retry logic.

        Args:
            messages (list[Message]): A list of messages to send to the language model.
            response_model (type[BaseModel] | None): An optional Pydantic model to parse the response into.
            max_tokens (int | None): The maximum number of tokens to generate in the response.
            model_size (ModelSize): The size of the model to use (small or medium).

        Returns:
            dict[str, typing.Any]: The response from the language model.
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        retry_count = 0
        last_error = None

        # Add multilingual extraction instructions
        messages[0].content += MULTILINGUAL_EXTRACTION_RESPONSES

        while retry_count <= self.MAX_RETRIES:
            try:
                response = await self._generate_response(
                    messages=messages,
                    response_model=response_model,
                    max_tokens=max_tokens,
                    model_size=model_size,
                )
                return response
            except RateLimitError:
                # Rate limit errors should not trigger retries (fail fast)
                raise
            except Exception as e:
                last_error = e

                # Check if this is a safety block - these typically shouldn't be retried
                if 'safety' in str(e).lower() or 'blocked' in str(e).lower():
                    logger.warning(f'Content blocked by safety filters: {e}')
                    raise

                # Don't retry if we've hit the max retries
                if retry_count >= self.MAX_RETRIES:
                    logger.error(f'Max retries ({self.MAX_RETRIES}) exceeded. Last error: {e}')
                    raise

                retry_count += 1

                # Construct a detailed error message for the LLM
                error_context = (
                    f'The previous response attempt was invalid. '
                    f'Error type: {e.__class__.__name__}. '
                    f'Error details: {str(e)}. '
                    f'Please try again with a valid response, ensuring the output matches '
                    f'the expected format and constraints.'
                )

                error_message = Message(role='user', content=error_context)
                messages.append(error_message)
                logger.warning(
                    f'Retrying after application error (attempt {retry_count}/{self.MAX_RETRIES}): {e}'
                )

        # If we somehow get here, raise the last error
        raise last_error or Exception('Max retries exceeded with no specific error')
