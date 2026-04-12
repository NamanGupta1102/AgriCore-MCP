import logging
import os
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from rag_engine import RagEngine
from reference_catalog import (
    INDEX_REFERENCE,
    RAG_AND_LIGHT_REFERENCE,
    build_engine_alpha_env_context_reference_from_rules,
)
from router import IntelligentRouter
from rules_engine import RulesEngine

# Shared copy for JSON Schema (tools) and optional Pydantic export models
_DESC_ACTION_CATEGORY = (
    "Action type evaluated against Engine Alpha JSON rules. "
    "Must match the `category` field in rules (e.g. planting, fertilizing, harvesting)."
)
_DESC_TARGET_PLANT = (
    "Plant or crop identifier. Use a concise lowercase slug matching rules/RAG data: "
    "rules bind via `target_plant` or `target_crop` (e.g. basil, corn, wheat_winter, tomato, monstera). "
    "Avoid prose like 'sweet basil' unless your corpus uses that exact tag."
)
_DESC_ENV_CONTEXT = (
    "Facts for Engine Alpha JSON Logic. Keys are rule-specific—include every value the user gave (°F as numbers, "
    "booleans as true/false). Read MCP resource `agricore://reference/engine-alpha-env-context` for variables per rule."
)
_DESC_CONSULT_QUERY = (
    "The user's full question in natural language. Include setting (indoor/outdoor, container, zone) "
    "so semantic search can retrieve the right guideline chunks."
)
_DESC_GUIDELINES_QUERY = (
    "Specific agricultural question for community guideline search only (no hard rules)."
)
_DESC_LIGHT_LEVEL = (
    "Light environment used to filter guideline metadata. "
    "Prefer: direct or full_sun (outdoor sun), bright_indirect, low, partial_shade, part_shade, or all if unknown "
    "(synonyms expanded server-side). Full table: MCP resource `agricore://reference/rag-metadata-and-light-levels`."
)
_DESC_METADATA_FILTERS_CONSULT = (
    "Optional LanceDB metadata filters for this call only. Keys: plant_tags (string), category (string). "
    "Do not pass light_levels here—it is set automatically from light_level."
)
_DESC_METADATA_FILTERS_SEARCH = (
    "Optional filters: plant_tags, light_levels, category. "
    "Values are exact-matched in storage except light_levels (synonym expansion applies)."
)

# Hints for MCP clients / LLMs (JSON Schema descriptions on each parameter)
_READ_ONLY = ToolAnnotations(readOnlyHint=True)

ActionCategory = Annotated[
    str,
    Field(
        description=_DESC_ACTION_CATEGORY,
        examples=["planting", "fertilizing", "harvesting"],
    ),
]

TargetPlant = Annotated[
    str,
    Field(
        description=_DESC_TARGET_PLANT,
        examples=["basil", "corn", "wheat_winter", "tomato", "monstera"],
    ),
]

EnvContext = Annotated[
    dict,
    Field(description=_DESC_ENV_CONTEXT),
]

ConsultQuery = Annotated[
    str,
    Field(description=_DESC_CONSULT_QUERY, min_length=2),
]

GuidelinesQuery = Annotated[
    str,
    Field(description=_DESC_GUIDELINES_QUERY, min_length=2),
]

LightLevel = Annotated[
    str,
    Field(
        description=_DESC_LIGHT_LEVEL,
        examples=["direct", "full_sun", "bright_indirect", "low", "all"],
    ),
]

OptionalMetadataFilters = Annotated[
    Optional[dict],
    Field(default=None, description=_DESC_METADATA_FILTERS_CONSULT),
]

OptionalSearchFilters = Annotated[
    Optional[dict],
    Field(default=None, description=_DESC_METADATA_FILTERS_SEARCH),
]

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Railway / cloud: listen on all interfaces; PORT from environment (default 8000)
_BIND_HOST = os.environ.get("BIND_HOST", "0.0.0.0")
_PORT = int(os.environ.get("PORT", "8000"))

# Initialize the MCP Server via FastMCP to support decorators
app = FastMCP(
    "AgriCore MCP-Server",
    host=_BIND_HOST,
    port=_PORT,
)

# Initialize Engine Alpha (loads JSON rules globally at startup)
rules_engine_instance = RulesEngine(
    rules_dir=os.path.join(os.path.dirname(__file__), "..", "data", "rules")
)

# Initialize Engine Beta (LlamaIndex + LanceDB)
rag_engine_instance = RagEngine(
    db_dir=os.path.join(os.path.dirname(__file__), "..", "data", ".lancedb")
)

# Initialize the Intelligent Router (Sprint 5: synthesis layer)
router_instance = IntelligentRouter(rules_engine_instance, rag_engine_instance)

@app.resource(
    "agricore://reference/index",
    title="AgriCore reference index",
    description="Lists MCP resource URIs for Engine Alpha env keys and RAG metadata.",
    mime_type="text/markdown",
)
def resource_reference_index() -> str:
    return INDEX_REFERENCE


@app.resource(
    "agricore://reference/engine-alpha-env-context",
    title="Engine Alpha env_context variables",
    description="Per-rule JSON Logic variable names derived from loaded rules in data/rules.",
    mime_type="text/markdown",
)
def resource_engine_alpha_env_context() -> str:
    return build_engine_alpha_env_context_reference_from_rules(rules_engine_instance.rules)


@app.resource(
    "agricore://reference/rag-metadata-and-light-levels",
    title="RAG filters and light_level vocabulary",
    description="Metadata filter keys for search_guidelines / comprehensive_ag_consult and allowed light_level values.",
    mime_type="text/markdown",
)
def resource_rag_metadata() -> str:
    return RAG_AND_LIGHT_REFERENCE


@app.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> Response:
    """Liveness probe for Railway and other orchestrators."""
    return JSONResponse({"status": "ok", "service": "agricore-mcp"})


@app.custom_route("/.well-known/mcp", methods=["GET"])
async def well_known_mcp(_request: Request) -> Response:
    """Minimal discovery hint for MCP-aware clients (path layout matches SSE defaults)."""
    return JSONResponse(
        {
            "name": "AgriCore MCP",
            "transport": "sse",
            "sse_path": "/sse",
            "message_path": "/messages/",
        }
    )


# 1. Pydantic Input Schema Definition (documentation / future schema export)
class EvaluateHardConstraintsInput(BaseModel):
    action_category: str = Field(description=_DESC_ACTION_CATEGORY)
    target_plant: str = Field(description=_DESC_TARGET_PLANT)
    env_context: dict = Field(description=_DESC_ENV_CONTEXT)


class ComprehensiveConsultInput(BaseModel):
    query: str = Field(description=_DESC_CONSULT_QUERY)
    action_category: str = Field(description=_DESC_ACTION_CATEGORY)
    target_plant: str = Field(description=_DESC_TARGET_PLANT)
    env_context: dict = Field(description=_DESC_ENV_CONTEXT)
    light_level: str = Field(description=_DESC_LIGHT_LEVEL)
    metadata_filters: Optional[dict] = Field(default=None, description=_DESC_METADATA_FILTERS_CONSULT)


class SearchGuidelinesInput(BaseModel):
    query: str = Field(description=_DESC_GUIDELINES_QUERY)
    metadata_filters: Optional[dict] = Field(default=None, description=_DESC_METADATA_FILTERS_SEARCH)


# 2. Registering the Tool
@app.tool(title="Evaluate hard constraints", annotations=_READ_ONLY)
def evaluate_hard_constraints(
    action_category: ActionCategory,
    target_plant: TargetPlant,
    env_context: EnvContext,
) -> str:
    """
    Engine Alpha only: deterministic PASS/FAIL against loaded JSON rules (no community text).

    **When to use:** User needs a strict go/no-go check from encoded thresholds, or you already have
    structured env facts and want rules without RAG.

    **When not to use:** General how-to questions with no matching rule will return PASS with
    “No strict rules found”—prefer `comprehensive_ag_consult` for full answers.

    **Returns:** Markdown with `### HARD CONSTRAINTS`, Status PASS or FAIL, and reasoning text.

    **Reference:** MCP resource `agricore://reference/engine-alpha-env-context` lists variables per rule.
    """
    logging.info(f"evaluating hard constraints for {action_category} on {target_plant}")
    result_markdown = rules_engine_instance.evaluate(action_category, target_plant, env_context)
    return result_markdown


@app.tool(title="Search community guidelines", annotations=_READ_ONLY)
def search_guidelines(
    query: GuidelinesQuery,
    metadata_filters: OptionalSearchFilters = None,
) -> str:
    """
    Engine Beta only: semantic search over ingested Markdown guidelines (LanceDB).

    **When to use:** Companion planting, disease Q&A, soil tips—fuzzy retrieval without hard rules.

    **Returns:** Markdown headed `COMMUNITY GUIDELINES` with sourced snippets, or a message if nothing matched.

    **Reference:** `agricore://reference/rag-metadata-and-light-levels`.
    """
    logging.info(f"searching guidelines for query: '{query}' with filters: {metadata_filters}")
    result_markdown = rag_engine_instance.search(query, metadata_filters)
    return result_markdown


@app.tool(title="Full consult (rules + guidelines)", annotations=_READ_ONLY)
async def comprehensive_ag_consult(
    query: ConsultQuery,
    action_category: ActionCategory,
    target_plant: TargetPlant,
    env_context: EnvContext,
    light_level: LightLevel,
    metadata_filters: OptionalMetadataFilters = None,
) -> str:
    """
    **Preferred default:** Runs Engine Alpha and Engine Beta **in parallel**, then returns one Markdown document.

    **When to use:** Almost any user question where both compliance-style rules (if present) and practical
    guideline text should appear together.

    **Parameters:** `light_level` is copied into RAG metadata as `light_levels` automatically—do not duplicate
    in `metadata_filters`.

    **Returns:** Markdown starting with `# AGRICORE: COMPREHENSIVE CONSULT`, then hard constraints, then community guidelines.

    **Reference:** `agricore://reference/index` (overview), plus env and RAG URIs above.
    """
    logging.info(f"[Router] Comprehensive consult for '{action_category}' on '{target_plant}'")

    # Auto-populate light_levels from light_level so callers use a clean API
    combined_filters = dict(metadata_filters) if metadata_filters else {}
    combined_filters.setdefault("light_levels", light_level)

    result_markdown = await router_instance.comprehensive_ag_consult(
        action_category, target_plant, env_context, query, combined_filters
    )
    return result_markdown


def main() -> None:
    """Start the MCP server over HTTP/SSE (FastMCP built-in transport)."""
    logging.info(
        "Starting AgriCore MCP-Server (SSE) on http://%s:%s (GET /sse, POST /messages/)",
        app.settings.host,
        app.settings.port,
    )
    app.run(transport="sse")


if __name__ == "__main__":
    main()
