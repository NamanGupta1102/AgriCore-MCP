# AgriCore MCP

**An open-source Model Context Protocol (MCP) server that provides LLMs and autonomous agents with accurate, community-verified agricultural knowledge.**

AgriCore MCP enforces a **Hybrid Intelligence Model** — separating hard biological absolutes (binary rules) from fuzzy localized knowledge (semantic guidelines) — to eliminate agricultural hallucinations from AI-powered farming tools.

---

## Architecture

```
                    ┌─────────────────────────────┐
  Agent / LLM ────▶ │   AgriCore MCP Server        │
                    │   (SSE / HTTP transport)      │
                    └───────────┬─────────────────-┘
                                │
              ┌─────────────────┴──────────────────┐
              ▼                                      ▼
   ┌──────────────────────┐          ┌──────────────────────────┐
   │  Engine Alpha        │          │  Engine Beta             │
   │  Deterministic Rules │          │  Semantic RAG            │
   │  (JSON-Logic)        │          │  (LanceDB + LlamaIndex)  │
   └──────────────────────┘          └──────────────────────────┘
          ▲                                    ▲
          │                                    │
   data/rules/*.json                 data/guidelines/*.md
```

### Exposed MCP Tools

| Tool | Description |
|---|---|
| `evaluate_hard_constraints` | Binary PASS/FAIL rule check via JSON-Logic (Engine Alpha) |
| `search_guidelines` | Semantic vector search over community Markdown guidelines (Engine Beta) |
| `comprehensive_ag_consult` | **⭐ Recommended.** Fires both engines concurrently and returns a unified strategy document |

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Git

### 2. Clone & Set Up Environment

```bash
git clone https://github.com/NamanGupta1102/AgriCore-MCP
cd AgriCore-MCP

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Build the Vector Index

This only needs to be run once after cloning, or after adding new guidelines:

```bash
python src/build_index.py
```

### 4. Run the Demo

```bash
python test_client.py
```

### 5. Start the MCP Server

**Local (SSE over HTTP, default `http://127.0.0.1:8000`):**

```bash
# Recommended: root entry (Railway-compatible)
python main.py

# Or run the module under src/ directly
python src/server_main.py
# Or on Windows:
start_server.bat
```

Set **`PORT`** (default `8000`) and optional **`BIND_HOST`** (default `0.0.0.0`) for cloud. Health: **`GET /health`**. MCP SSE: **`GET /sse`**, messages: **`POST /messages/`**. Discovery hint: **`GET /.well-known/mcp`**.

### Railway

1. Connect the repo and use the included **`railway.json`** (config-as-code overrides dashboard settings):
   - **Build:** `pip install -r requirements.txt && python src/build_index.py` (generates **`data/.lancedb`** in the image).
   - **Start:** `python main.py` — healthcheck **`/health`**.
2. Alternatively, commit a prebuilt **`data/.lancedb`** and set **`build.buildCommand`** to `null` in `railway.json` if you want Nixpacks defaults only.
3. Use a plan with enough **RAM** for sentence-transformers + LanceDB (build and runtime; free tiers may OOM or be slow).

---

## Running Tests

```bash
pytest -v
```

Tests are in `tests/`. Engine Beta tests require the embedding model download on first run.

---

## Project Structure

```
AgriCore-MCP/
├── main.py                # Production/Railway entry — runs FastMCP SSE on PORT
├── railway.json           # Railway deploy: startCommand + /health check
├── src/
│   ├── server_main.py     # MCP server entry point — registers all tools
│   ├── rules_engine.py    # Engine Alpha: JSON-Logic rule evaluator
│   ├── rag_engine.py      # Engine Beta: LanceDB + LlamaIndex semantic retrieval
│   ├── router.py          # Intelligent Router: concurrent synthesis of both engines
│   └── build_index.py     # Standalone ingestion script: Markdown → LanceDB vectors
├── data/
│   ├── rules/             # JSON rule files (contributor-submitted)
│   ├── guidelines/        # Markdown guideline files (contributor-submitted)
│   └── .lancedb/          # Generated vector database (do not edit manually)
├── tests/
│   ├── conftest.py        # Shared pytest fixtures
│   ├── fixtures/          # Test-only data (mock rules, stubs)
│   ├── test_alpha.py      # Engine Alpha unit tests
│   └── test_beta.py       # Engine Beta unit tests
├── context/               # Project design documents and specifications
├── requirements.txt       # Pinned Python dependencies
├── pyproject.toml         # Package config and pytest settings
└── test_client.py         # End-to-end demo script
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add rules and guidelines.

---

## License

MIT
