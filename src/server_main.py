import asyncio
import logging
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import json
import os
from typing import Optional

# Import our custom engines
from rules_engine import RulesEngine
from rag_engine import RagEngine
from router import IntelligentRouter
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Initialize the MCP Server via FastMCP to support decorators
app = FastMCP("AgriCore MCP-Server")

# Initialize Engine Alpha (loads JSON rules globally at startup)
rules_engine_instance = RulesEngine(rules_dir=os.path.join(os.path.dirname(__file__), "..", "data", "rules"))

# Initialize Engine Beta (LlamaIndex + LanceDB)
rag_engine_instance = RagEngine(db_dir=os.path.join(os.path.dirname(__file__), "..", "data", ".lancedb"))

# Initialize the Intelligent Router (Sprint 5: synthesis layer)
router_instance = IntelligentRouter(rules_engine_instance, rag_engine_instance)

# 1. Pydantic Input Schema Definition
class EvaluateHardConstraintsInput(BaseModel):
    action_category: str = Field(description="The category of action (e.g., 'planting', 'fertilizing', 'harvesting').")
    target_plant: str = Field(description="The specific houseplant being evaluated (e.g., 'monstera', 'pothos').")
    env_context: dict = Field(description="A dictionary of current environmental variables. MUST include 'room_temp_f' if known, 'air_temp_f', and boolean 'frost_risk'.")

class ComprehensiveConsultInput(BaseModel):
    query: str = Field(description="The overarching natural language question from the user.")
    action_category: str = Field(description="The category of action (e.g., 'planting', 'fertilizing', 'harvesting').")
    target_plant: str = Field(description="The specific houseplant being evaluated (e.g., 'monstera', 'pothos').")
    env_context: dict = Field(description="A dictionary of current environmental variables. MUST include 'room_temp_f' if known, 'air_temp_f', and boolean 'frost_risk'.")
    light_level: str = Field(description="The light level of the environment (e.g., 'low', 'bright_indirect', 'direct'). Used to filter community guidelines to relevant advice.")
    metadata_filters: Optional[dict] = Field(default=None, description="Optional additional filters for the RAG search. Valid keys: 'plant_tags', 'category'. (light_levels is auto-populated from light_level.)")

class SearchGuidelinesInput(BaseModel):
    query: str = Field(description="The specific natural language question regarding agricultural practices.")
    metadata_filters: Optional[dict] = Field(default=None, description="Optional filters to narrow the RAG search. Valid keys: 'plant_tags', 'light_levels', 'category'.")

# 2. Registering the Tool
@app.tool()
def evaluate_hard_constraints(
    action_category: str,
    target_plant: str,
    env_context: dict
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
    metadata_filters: Optional[dict] = None
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
    metadata_filters: Optional[dict] = None
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

from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn
from mcp.server.sse import SseServerTransport

# Initialize SSE Transport
sse = SseServerTransport("/messages")

async def handle_sse(request):
    """Handles the initial SSE connection from the client."""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await app._mcp_server.run(streams[0], streams[1], app._mcp_server.create_initialization_options())

# Create Starlette application
starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages", app=sse.handle_post_message)
    ]
)

if __name__ == "__main__":
    logging.info("Starting AgriCore MCP-Server on http://127.0.0.1:7860 via SSE...")
    try:
        uvicorn.run(starlette_app, host="127.0.0.1", port=7860)
    except KeyboardInterrupt:
        logging.info("Server received shutdown signal. Exiting gracefully.")
    except Exception as e:
        logging.error(f"Fatal server failure: {e}")
