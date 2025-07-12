#!/usr/bin/env python3
"""
Test script to verify Gemini support in MCP server
"""

import os
import sys
import subprocess

def test_gemini_mcp():
    """Test Gemini MCP server configuration"""
    
    # Set environment variables for testing
    os.environ['GOOGLE_API_KEY'] = 'test-key'  # You'll need to replace with real key
    os.environ['NEO4J_URI'] = 'bolt://localhost:7687'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'password'
    
    # Test command
    cmd = [
        sys.executable, 
        'mcp_server/graphiti_mcp_server.py',
        '--model', 'gemini-2.5-flash',
        '--transport', 'sse',
        '--help'  # Just test argument parsing
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print("Command executed successfully!")
        print("Return code:", result.returncode)
        if result.stdout:
            print("STDOUT:", result.stdout[:500])
        if result.stderr:
            print("STDERR:", result.stderr[:500])
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

if __name__ == '__main__':
    success = test_gemini_mcp()
    print(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
