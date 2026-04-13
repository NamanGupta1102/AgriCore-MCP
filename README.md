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

### MCP Resources (LLM reference)

Static reference material is exposed as resources so agents can **ListResources** / **ReadResource** without bloating tool definitions:

| URI | Content |
|-----|---------|
| `agricore://reference/index` | Index of reference URIs |
| `agricore://reference/engine-alpha-env-context` | Per-rule `env_context` / JSON Logic variable names (from loaded `data/rules`) |
| `agricore://reference/rag-metadata-and-light-levels` | RAG filter keys and `light_level` vocabulary |

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Git
- **[uv](https://docs.astral.sh/uv/)** (recommended for environments and `uv run`)

### 2. Clone & Set Up Environment

**Recommended (uv):** Dependencies and Python version are pinned in [`pyproject.toml`](pyproject.toml) and [`uv.lock`](uv.lock). The repo includes [`.python-version`](.python-version) (3.12) so `uv` picks the same runtime locally as in Docker.

```bash
git clone https://github.com/NamanGupta1102/AgriCore-MCP
cd AgriCore-MCP

# Runtime dependencies only (creates/updates .venv from uv.lock)
uv sync

# Include dev tools (e.g. pytest)
uv sync --group dev
```

Optional: activate the venv (`source .venv/bin/activate` or `.venv\Scripts\activate`) or skip activation and use **`uv run`** for every command (e.g. `uv run pytest`, `uv run python main.py`).

**Classic pip:** [`requirements.txt`](requirements.txt) is generated from the lockfile (`uv export --no-dev`) for `pip install -r requirements.txt` if you do not use uv.

### 3. Build the Vector Index

This only needs to be run once after cloning, or after adding new guidelines:

```bash
uv run python src/build_index.py
```

### 4. Run the Demo

```bash
uv run python test_client.py
```

### 5. Start the MCP Server

**Local (SSE over HTTP, default `http://127.0.0.1:8000`):**

```bash
# Recommended: root entry (Railway-compatible), using the uv-managed venv
uv run python main.py

# Equivalent after: uv sync && source .venv/bin/activate
python main.py

# Or run the module under src/ directly
uv run python src/server_main.py
# Or on Windows:
start_server.bat
```

Set **`PORT`** (default `8000`) and optional **`BIND_HOST`** (default `0.0.0.0`) for cloud. Health: **`GET /health`**. MCP SSE: **`GET /sse`**, messages: **`POST /messages/`**. Discovery hint: **`GET /.well-known/mcp`**.

**Web playground (human demo):** With the server running, open **`/`** for a static HTML UI (dark theme) that explains AgriCore and calls **`POST /api/preview`** with JSON (`query`, optional `plant`, `light_level`, `top_k`, and optional Engine Alpha fields). This uses the same RAG and rules engines as the MCP tools; **MCP clients and agents should still use `/sse`**, not the preview API, for protocol compliance.

### Railway

1. Use the included **`Dockerfile`** + **`railway.json`** (`builder: DOCKERFILE`). The image uses **`uv sync --frozen`** from **`uv.lock`**, then runs **`python src/build_index.py`** *after* the final `COPY`, so **`data/.lancedb`** is not wiped (Nixpacks alone ran a second `COPY . /app` after the index build and removed `.lancedb` because it is not in Git).
2. **Start:** `python main.py` — healthcheck **`/health`**.
3. Ensure **`data/rules`** and **`data/guidelines`** are tracked in Git (your `.gitignore` may ignore `/data`; force-add or narrow ignores if deploys miss rules/guidelines).
4. Use a plan with enough **RAM** for sentence-transformers + LanceDB (build and runtime; free tiers may OOM or be slow).

---

## Running Tests

```bash
uv sync --group dev   # once, if pytest is not installed yet
uv run pytest -v
```

Tests are in `tests/`. Engine Beta tests require the embedding model download on first run.

---

## Project Structure

```
AgriCore-MCP/
├── main.py                # Production/Railway entry — runs FastMCP SSE on PORT
├── railway.json           # Railway deploy: startCommand + /health check
├── web/                   # Static playground UI (/, /assets/*) + same-origin /api/preview
├── src/
│   ├── server_main.py     # MCP server entry — tools + reference resources
│   ├── reference_catalog.py # Markdown for MCP resources (env keys, RAG metadata)
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
├── .python-version        # Python pin for uv (matches Docker base image)
├── pyproject.toml         # Project metadata, dependencies, pytest settings
├── uv.lock                # Locked dependency versions (use with uv sync)
├── requirements.txt       # pip fallback (generated: uv export --no-dev)
└── test_client.py         # End-to-end demo script
```

---

## Dataset references

Public Kaggle datasets the project may draw from or align with when expanding guidelines and care content (not bundled in-repo):

- [Indoor house plants dataset with care instructions](https://www.kaggle.com/datasets/prakash27x/indoor-house-plants-dataset-with-care-instructions)
- [Plants growth and care recommendations](https://www.kaggle.com/datasets/aribashafaqat/plants-growth-and-care-recommendations/data)
- [Gardening Q and A](https://www.kaggle.com/datasets/gabriellaamorim/gardening-q-and-a)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add rules and guidelines.

---

## License

MIT
