# Copilot Instructions for Graphiti

## Project Overview
Graphiti is a Python framework for building temporally-aware knowledge graphs for AI agents. Key characteristics:
- Bi-temporal data model tracking both event occurrence and data ingestion times
- Hybrid retrieval combining semantic embeddings, BM25, and graph traversal
- Real-time incremental updates without batch recomputation
- Support for custom entity definitions via Pydantic models

## Core Architecture

### Main Components
1. **Core Library** (`graphiti_core/`)
   - `graphiti.py` - Main orchestration class
   - `driver/` - Neo4j and FalkorDB database adapters
   - `embedder/` - Embedding clients (OpenAI, Azure, Gemini)
   - `llm_client/` - LLM integrations (OpenAI, Anthropic, Gemini, Groq)
   - `nodes.py`, `edges.py` - Core graph data structures
   - `search/` - Hybrid search implementation

2. **REST API** (`server/`)
   - FastAPI service in `graph_service/main.py`
   - API endpoints in `routers/`
   - Data contracts in `dto/`

3. **MCP Server** (`mcp_server/`)
   - Model Context Protocol server in `graphiti_mcp_server.py`
   - Docker deployment with Neo4j integration

## Development Workflow

### Environment Setup
```bash
# Install dependencies with extras
uv sync --extra dev

# Common development commands (from project root)
make format  # ruff import sorting + formatting
make lint    # ruff + pyright type checking
make test    # run test suite
make check   # run all checks
```

### Integration Testing
- Integration tests are marked with `_int` suffix
- Require database connections (Neo4j/FalkorDB)
- Configure via environment variables:
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - `OPENAI_API_KEY` for LLM/embeddings
  - Provider-specific: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.

## Project Conventions

### Third-Party Integration Pattern
1. Add optional dependencies in `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   your-service = ["your-package>=1.0.0"]
   dev = ["your-package>=1.0.0"]  # Include in dev extras
   ```

2. Use TYPE_CHECKING imports:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from your_package import SomeType
   else:
       try:
           from your_package import SomeType
       except ImportError:
           raise ImportError('Install with: pip install graphiti-core[your-service]')
   ```

### File Organization
- LLM clients → `graphiti_core/llm_client/`
- Embedding clients → `graphiti_core/embedder/`
- Database drivers → `graphiti_core/driver/`
- Integration tests → `tests/*_int.py`

## Memory Design (MCP Server)
- Episodes represent content snippets (text/messages/JSON)
- Nodes represent entities with temporal metadata
- Facts capture relationships between entities
- Graph search combines semantic, keyword, and traversal methods
- Use `group_id` to organize knowledge domains

## Documentation Links
- [Main Documentation](https://help.getzep.com/graphiti)
- [Quick Start Guide](https://help.getzep.com/graphiti/graphiti/quick-start)
- [LangGraph Integration](https://help.getzep.com/graphiti/graphiti/lang-graph-agent)
