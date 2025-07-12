#!/usr/bin/env python3
"""
Test script to verify Gemini configuration in MCP server
"""

import os
import sys

# Add the parent directory to the path so we can import the MCP server modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graphiti_mcp_server import (
    GraphitiLLMConfig, 
    GraphitiEmbedderConfig,
    is_gemini_model,
    get_api_key_env_var,
    GEMINI_AVAILABLE
)

def test_gemini_detection():
    """Test Gemini model detection"""
    print("=== Testing Gemini Model Detection ===")
    
    test_cases = [
        ("gemini-2.5-flash", True),
        ("gemini-2.0-flash", True),
        ("Gemini-1.5-pro", True),
        ("gpt-4.1-mini", False),
        ("claude-3-sonnet", False),
        ("", False),
    ]
    
    for model, expected in test_cases:
        result = is_gemini_model(model)
        status = "✓" if result == expected else "✗"
        print(f"{status} {model}: {result} (expected: {expected})")

def test_api_key_detection():
    """Test API key environment variable detection"""
    print("\n=== Testing API Key Detection ===")
    
    test_cases = [
        ("gemini-2.5-flash", "GOOGLE_API_KEY"),
        ("gpt-4.1-mini", "OPENAI_API_KEY"),
        ("claude-3-sonnet", "OPENAI_API_KEY"),
    ]
    
    for model, expected in test_cases:
        result = get_api_key_env_var(model)
        status = "✓" if result == expected else "✗"
        print(f"{status} {model}: {result} (expected: {expected})")

def test_llm_config():
    """Test LLM configuration with Gemini"""
    print("\n=== Testing LLM Configuration ===")
    
    # Set test environment variables
    os.environ['GOOGLE_API_KEY'] = 'test-google-key'
    os.environ['MODEL_NAME'] = 'gemini-2.5-flash'
    
    try:
        config = GraphitiLLMConfig.from_env()
        print(f"✓ Model: {config.model}")
        print(f"✓ API Key: {config.api_key[:10]}..." if config.api_key else "✗ No API Key")
        print(f"✓ Small Model: {config.small_model}")
        
        # Test client creation
        if GEMINI_AVAILABLE:
            try:
                client = config.create_client()
                print(f"✓ Client created: {type(client).__name__}")
            except Exception as e:
                print(f"✗ Client creation failed: {e}")
        else:
            print("⚠ Gemini not available - install with: pip install 'graphiti-core[google-genai]'")
            
    except Exception as e:
        print(f"✗ LLM Config failed: {e}")

def test_embedder_config():
    """Test Embedder configuration with Gemini"""
    print("\n=== Testing Embedder Configuration ===")
    
    # Set test environment variables
    os.environ['GOOGLE_API_KEY'] = 'test-google-key'
    os.environ['EMBEDDER_MODEL_NAME'] = 'embedding-001'
    
    try:
        config = GraphitiEmbedderConfig.from_env()
        print(f"✓ Model: {config.model}")
        print(f"✓ API Key: {config.api_key[:10]}..." if config.api_key else "✗ No API Key")
        
        # Test client creation
        if GEMINI_AVAILABLE:
            try:
                client = config.create_client()
                if client:
                    print(f"✓ Client created: {type(client).__name__}")
                else:
                    print("✗ No client created")
            except Exception as e:
                print(f"✗ Client creation failed: {e}")
        else:
            print("⚠ Gemini not available")
            
    except Exception as e:
        print(f"✗ Embedder Config failed: {e}")

def main():
    print("Testing Gemini Support in MCP Server")
    print("=" * 50)
    
    print(f"Gemini Available: {GEMINI_AVAILABLE}")
    
    test_gemini_detection()
    test_api_key_detection()
    test_llm_config()
    test_embedder_config()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == '__main__':
    main()
