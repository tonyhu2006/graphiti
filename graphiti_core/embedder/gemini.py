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

from collections.abc import Iterable
from typing import TYPE_CHECKING

import aiohttp

if TYPE_CHECKING:
    from google import genai
    from google.genai import types
else:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            'google-genai is required for GeminiEmbedder. '
            'Install it with: pip install graphiti-core[google-genai]'
        ) from None

from pydantic import Field

from .client import EmbedderClient, EmbedderConfig

DEFAULT_EMBEDDING_MODEL = 'embedding-001'


class GeminiEmbedderConfig(EmbedderConfig):
    embedding_model: str = Field(default=DEFAULT_EMBEDDING_MODEL)
    api_key: str | None = None
    base_url: str | None = None  # Support for custom endpoints like Gemini Balance


class GeminiEmbedder(EmbedderClient):
    """
    Google Gemini Embedder Client
    """

    def __init__(
        self,
        config: GeminiEmbedderConfig | None = None,
        client: 'genai.Client | None' = None,
    ):
        """
        Initialize the GeminiEmbedder with the provided configuration and client.

        Args:
            config (GeminiEmbedderConfig | None): The configuration for the GeminiEmbedder, including API key, model, base URL, temperature, and max tokens.
            client (genai.Client | None): An optional async client instance to use. If not provided, a new genai.Client is created.
        """
        if config is None:
            config = GeminiEmbedderConfig()

        self.config = config

        if client is None:
            # Check if base_url is provided for custom endpoints (like Gemini Balance)
            if hasattr(config, 'base_url') and config.base_url:
                self.base_url = config.base_url
                self.use_custom_endpoint = True
                # Still create a genai client for fallback
                self.client = genai.Client(api_key=config.api_key)
            else:
                self.base_url = None
                self.use_custom_endpoint = False
                self.client = genai.Client(api_key=config.api_key)
        else:
            self.client = client
            self.base_url = getattr(config, 'base_url', None)
            self.use_custom_endpoint = bool(self.base_url)

    async def _call_custom_embedding_endpoint(
        self,
        input_data: str | list[str]
    ) -> list[float] | list[list[float]]:
        """
        Call a custom endpoint (like Gemini Balance) for embeddings using OpenAI-compatible API format.

        Args:
            input_data: The input data to create embeddings for

        Returns:
            Embedding vector(s)
        """
        # Prepare the request payload in OpenAI format
        payload = {
            "model": self.config.embedding_model or DEFAULT_EMBEDDING_MODEL,
            "input": input_data,
        }

        # Make the API call
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        # Use the OpenAI-compatible embeddings endpoint
        url = f"{self.base_url.rstrip('/')}/v1/embeddings"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Embedding API call failed with status {response.status}: {error_text}")

                result = await response.json()

                # Extract embeddings from OpenAI format response
                if "data" in result and len(result["data"]) > 0:
                    if isinstance(input_data, str):
                        # Single embedding
                        return result["data"][0]["embedding"]
                    else:
                        # Multiple embeddings
                        return [item["embedding"] for item in result["data"]]
                else:
                    raise ValueError("No valid embeddings received from API")

    async def create(
        self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> list[float]:
        """
        Create embeddings for the given input data using Google's Gemini embedding model.

        Args:
            input_data: The input data to create embeddings for. Can be a string, list of strings,
                       or an iterable of integers or iterables of integers.

        Returns:
            A list of floats representing the embedding vector.
        """
        # Check if we should use custom endpoint
        if self.use_custom_endpoint and self.base_url:
            # Convert input_data to string if needed for custom endpoint
            if isinstance(input_data, str):
                text_input = input_data
            elif isinstance(input_data, list) and all(isinstance(item, str) for item in input_data):
                text_input = input_data[0]  # Take first string for single embedding
            else:
                # For other types, convert to string representation
                text_input = str(input_data)

            result = await self._call_custom_embedding_endpoint(text_input)
            return result if isinstance(result, list) and isinstance(result[0], float) else result[0]

        # Original Gemini API implementation
        result = await self.client.aio.models.embed_content(
            model=self.config.embedding_model or DEFAULT_EMBEDDING_MODEL,
            contents=[input_data],  # type: ignore[arg-type]  # mypy fails on broad union type
            config=types.EmbedContentConfig(output_dimensionality=self.config.embedding_dim),
        )

        if not result.embeddings or len(result.embeddings) == 0 or not result.embeddings[0].values:
            raise ValueError('No embeddings returned from Gemini API in create()')

        return result.embeddings[0].values

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        # Check if we should use custom endpoint
        if self.use_custom_endpoint and self.base_url:
            result = await self._call_custom_embedding_endpoint(input_data_list)
            return result if isinstance(result[0], list) else [result]

        # Original Gemini API implementation
        result = await self.client.aio.models.embed_content(
            model=self.config.embedding_model or DEFAULT_EMBEDDING_MODEL,
            contents=input_data_list,  # type: ignore[arg-type]  # mypy fails on broad union type
            config=types.EmbedContentConfig(output_dimensionality=self.config.embedding_dim),
        )

        if not result.embeddings or len(result.embeddings) == 0:
            raise Exception('No embeddings returned')

        embeddings = []
        for embedding in result.embeddings:
            if not embedding.values:
                raise ValueError('Empty embedding values returned')
            embeddings.append(embedding.values)
        return embeddings
