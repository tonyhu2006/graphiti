@echo off
REM Batch script to run Graphiti MCP Server with Gemini
REM Replace YOUR_GOOGLE_API_KEY with your actual Google API key

echo Setting up environment for Gemini MCP Server...

REM Set Google API key (REPLACE WITH YOUR ACTUAL KEY)
set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY

REM Set Neo4j connection parameters
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=password

REM Set embedder model to use Gemini
set EMBEDDER_MODEL_NAME=embedding-001

echo Starting Graphiti MCP Server with Gemini...
echo Model: gemini-2.5-flash
echo Embedder: embedding-001
echo Transport: sse

uv run graphiti_mcp_server.py --model gemini-2.5-flash --transport sse

pause
