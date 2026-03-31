# AgriCore-MCP: Project Context

This document provides a comprehensive overview of the AgriCore-MCP server, defining its architecture, features, and how its distinct code components interact. It is designed to quickly onboard any LLM or external agent assisting with the codebase.

## 1. Project Overview
AgriCore-MCP is an open-source, dual-engine Model Context Protocol (MCP) server. It acts as an agricultural data bank designed to expose dynamic "Tools" to external autonomous AI agents, ensuring these agents receive verified, constraint-checked agronomic data.

The project solves the problem of "LLM Hallucinations" in farming advice by splitting data into two parallel engines:
- **Engine Alpha**: A deterministic rules engine for biological absolutes and regulatory constraints.
- **Engine Beta**: A semantic RAG engine for fuzzy, localized community guidelines.

## 2. Core Architecture
The system follows a standard MCP server architecture over standard input/output (stdio), utilizing the official Python `mcp` SDK to register and expose functions to external agents.

When a query arrives, the system uses an **Intelligent Router** that operates asynchronously to call both Engine Alpha and Engine Beta in parallel via a thread pool, ensuring latency constraints are met (< 500ms).

### Key Files and Component Breakdown

#### `src/server_main.py`
- **Role**: The main entry point and Transport Layer.
- **Mechanisms**: 
  - Uses `mcp.server.stdio_server` for communication.
  - Registers three key MCP tools using Pydantic schemas: `evaluate_hard_constraints`, `search_guidelines`, and `comprehensive_ag_consult`.
  - Initializes global singleton instances of the engines and the router.

#### `src/rules_engine.py` (Engine Alpha)
- **Role**: The Deterministic Rules Engine evaluating "Hard Constraints" (e.g., minimum germination temperatures).
- **Mechanisms**: 
  - Recursively loads JSON files from `data/rules/` on startup.
  - Uses the zero-hallucination `json-logic-py` to evaluate dynamic environment variables (like `soil_temp_f`) against strict schemas. 
  - Bypasses Python `eval()` entirely to prevent RCE vulnerabilities.

#### `src/rag_engine.py` (Engine Beta)
- **Role**: The Semantic RAG Engine serving localized "Fuzzy Guidelines" (e.g., managing blight, companion planting).
- **Mechanisms**: 
  - Uses a serverless vector database (`LanceDB`) combined with `llama-index`.
  - Uses an accurate, localized HuggingFace embedding model (`BAAI/bge-small-en-v1.5`) so external APIs are not required.
  - Applies strict Metadata Filters (e.g., crop tags, hardiness zones) dynamically *before* semantic similarity search utilizing `FilterOperator.IN`.

#### `src/router.py` (The Synthesizer)
- **Role**: Combines Engine Alpha and Engine Beta.
- **Mechanisms**: 
  - Exports `comprehensive_ag_consult`, the primary target for LLM interactions.
  - Uses `asyncio.to_thread` and `asyncio.gather` to execute the CPU-bound logic evaluation and vector searches concurrently, avoiding blocking the main MCP server event loop.
  - Merges the responses into a structured Markdown output.

#### `src/build_index.py` (The Data Pipeline)
- **Role**: Developer utility script to ingest community knowledge.
- **Mechanisms**: 
  - Reads open-source, community-submitted Markdown files containing YAML front-matter from `data/guidelines/`.
  - Chunks the Markdown and creates offline vector embeddings, loading them into the local LanceDB directory.

#### `test_client.py`
- **Role**: A standalone local script testing the behavior of the three main engines. It runs simulated queries to prove the outputs without actively booting the full stdio MCP stream.

## 3. Data Schemas

### Deterministic Schemas
Rules stored natively in JSON (loaded by Alpha).
```json
{
  "rule_id": "rule_corn_germination_001",
  "category": "planting",
  "target_crop": "corn",
  "logic_evaluator": { "and": [ {">=": [{"var": "soil_temp_f"}, 50]} ] },
  "response_pass": "...",
  "response_fail": "..."
}
```

### Guideline Schemas
Community-driven Markdown files containing YAML metadata headers (loaded by Bata/`build_index.py`).
```yaml
---
id: "guide_tomato_blight_ne_01"
crop_tags: ["tomato"]
hardiness_zones: ["5a", "6b"]
---
```

## 4. Dependencies and Environment
- The environment is managed rigorously using `uv`.
- **Key dependencies**: `mcp`, `json-logic-py`, `lancedb`, `llama-index`, `llama-index-vector-stores-lancedb`, `llama-index-embeddings-huggingface`. 
- **System Constraints**: Operates solely with zero-external-dependencies for logic and vector retrieval; it strictly requires no external API tokens at runtime (e.g., no Pinecone, OpenAI needed for retrieval/logic).

**This context should provide an AI agent exactly the high-level architecture needed to build upon, debug, or extend the functionalities of the AgriCore-MCP system.**
