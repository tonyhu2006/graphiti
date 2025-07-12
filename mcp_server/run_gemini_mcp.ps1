# PowerShell script to run Graphiti MCP Server with Gemini
# Replace YOUR_GOOGLE_API_KEY with your actual Google API key

Write-Host "Setting up environment for Gemini MCP Server..." -ForegroundColor Green

# Set Google API key (REPLACE WITH YOUR ACTUAL KEY)
$env:GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"

# Set Neo4j connection parameters
$env:NEO4J_URI = "bolt://localhost:7687"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "password"

# Set embedder model to use Gemini
$env:EMBEDDER_MODEL_NAME = "embedding-001"

Write-Host "Starting Graphiti MCP Server with Gemini..." -ForegroundColor Yellow
Write-Host "Model: gemini-2.5-flash" -ForegroundColor Cyan
Write-Host "Embedder: embedding-001" -ForegroundColor Cyan
Write-Host "Transport: sse" -ForegroundColor Cyan

# Check if Google API key is set
if ($env:GOOGLE_API_KEY -eq "YOUR_GOOGLE_API_KEY") {
    Write-Host "WARNING: Please set your actual Google API key in the script!" -ForegroundColor Red
    Write-Host "Edit this file and replace YOUR_GOOGLE_API_KEY with your real API key." -ForegroundColor Red
    Read-Host "Press Enter to continue anyway (will fail without real API key)"
}

# Run the MCP server
uv run graphiti_mcp_server.py --model gemini-2.5-flash --transport sse
