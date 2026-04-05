import asyncio
import logging
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Import our custom engines
from rules_engine import RulesEngine
from rag_engine import RagEngine
from router import IntelligentRouter

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
    action_category: str = Field(
        description="The category of action (e.g., 'planting', 'fertilizing', 'harvesting')."
    )
    target_plant: str = Field(
        description="The specific houseplant being evaluated (e.g., 'monstera', 'pothos')."
    )
    env_context: dict = Field(
        description="A dictionary of current environmental variables. MUST include 'room_temp_f' if known, 'air_temp_f', and boolean 'frost_risk'."
    )


class ComprehensiveConsultInput(BaseModel):
    query: str = Field(description="The overarching natural language question from the user.")
    action_category: str = Field(
        description="The category of action (e.g., 'planting', 'fertilizing', 'harvesting')."
    )
    target_plant: str = Field(
        description="The specific houseplant being evaluated (e.g., 'monstera', 'pothos')."
    )
    env_context: dict = Field(
        description="A dictionary of current environmental variables. MUST include 'room_temp_f' if known, 'air_temp_f', and boolean 'frost_risk'."
    )
    light_level: str = Field(
        description="The light level of the environment (e.g., 'low', 'bright_indirect', 'direct'). Used to filter community guidelines to relevant advice."
    )
    metadata_filters: Optional[dict] = Field(
        default=None,
        description="Optional additional filters for the RAG search. Valid keys: 'plant_tags', 'category'. (light_levels is auto-populated from light_level.)",
    )


class SearchGuidelinesInput(BaseModel):
    query: str = Field(description="The specific natural language question regarding agricultural practices.")
    metadata_filters: Optional[dict] = Field(
        default=None,
        description="Optional filters to narrow the RAG search. Valid keys: 'plant_tags', 'light_levels', 'category'.",
    )


# 2. Registering the Tool
@app.tool()
def evaluate_hard_constraints(
    action_category: str,
    target_plant: str,
    env_context: dict,
) -> str:
    """
    Evaluates hard environmental constraints for a specific agricultural action.
    This guarantees zero-hallucination compliance with minimum thresholds (Engine Alpha).
    """
    logging.info(f"evaluating hard constraints for {action_category} on {target_plant}")
    result_markdown = rules_engine_instance.evaluate(action_category, target_plant, env_context)
    return result_markdown


@app.tool()
def search_guidelines(
    query: str,
    metadata_filters: Optional[dict] = None,
) -> str:
    """
    Searches community agricultural guidelines using a Semantic RAG vector database.
    Useful for fuzzy guidance, companion planting, disease management, etc. (Engine Beta).
    """
    logging.info(f"searching guidelines for query: '{query}' with filters: {metadata_filters}")
    result_markdown = rag_engine_instance.search(query, metadata_filters)
    return result_markdown


@app.tool()
async def comprehensive_ag_consult(
    query: str,
    action_category: str,
    target_plant: str,
    env_context: dict,
    light_level: str,
    metadata_filters: Optional[dict] = None,
) -> str:
    """
    [RECOMMENDED] Synthesizes hard environmental constraints and localized semantic guidelines
    into a single, complete agricultural strategy document.
    Calls both Engine Alpha (zero-hallucination rules) and Engine Beta (RAG community knowledge) in one pass,
    running them concurrently for minimum latency.
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
