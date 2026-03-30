import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from pydantic import BaseModel, Field
import json
import os
from typing import Optional

# Import our custom engines
from rules_engine import RulesEngine
from rag_engine import RagEngine
from router import IntelligentRouter
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Initialize the MCP Server
app = Server("AgriCore MCP-Server")

# Initialize Engine Alpha (loads JSON rules globally at startup)
rules_engine_instance = RulesEngine(rules_dir=os.path.join(os.path.dirname(__file__), "..", "data", "rules"))

# Initialize Engine Beta (LlamaIndex + LanceDB)
rag_engine_instance = RagEngine(db_dir=os.path.join(os.path.dirname(__file__), "..", "data", ".lancedb"))

# Initialize the Intelligent Router (Sprint 5: synthesis layer)
router_instance = IntelligentRouter(rules_engine_instance, rag_engine_instance)

# 1. Pydantic Input Schema Definition
class EvaluateHardConstraintsInput(BaseModel):
    action_category: str = Field(description="The category of action (e.g., 'planting', 'fertilizing', 'harvesting').")
    target_crop: str = Field(description="The specific crop being evaluated (e.g., 'corn', 'wheat_winter').")
    env_context: dict = Field(description="A dictionary of current environmental variables. MUST include 'soil_temp_f' if known, 'air_temp_f', and boolean 'frost_risk'.")

class ComprehensiveConsultInput(BaseModel):
    query: str = Field(description="The overarching natural language question from the user.")
    action_category: str = Field(description="The category of action (e.g., 'planting', 'fertilizing', 'harvesting').")
    target_crop: str = Field(description="The specific crop being evaluated (e.g., 'corn', 'wheat_winter').")
    env_context: dict = Field(description="A dictionary of current environmental variables. MUST include 'soil_temp_f' if known, 'air_temp_f', and boolean 'frost_risk'.")
    location_zone: str = Field(description="The USDA hardiness zone of the farm (e.g., '6b'). Used to filter community guidelines to regionally relevant advice.")
    metadata_filters: Optional[dict] = Field(default=None, description="Optional additional filters for the RAG search. Valid keys: 'crop_tags', 'category'. (hardiness_zones is auto-populated from location_zone.)")

class SearchGuidelinesInput(BaseModel):
    query: str = Field(description="The specific natural language question regarding agricultural practices.")
    metadata_filters: Optional[dict] = Field(default=None, description="Optional filters to narrow the RAG search. Valid keys: 'crop_tags', 'hardiness_zones', 'category'.")

# 2. Registering the Tool
@app.tool()
def evaluate_hard_constraints(
    action_category: str,
    target_crop: str,
    env_context: dict
) -> str:
    """
    Evaluates hard environmental constraints for a specific agricultural action.
    This guarantees zero-hallucination compliance with minimum thresholds (Engine Alpha).
    """
    logging.info(f"evaluating hard constraints for {action_category} on {target_crop}")
    result_markdown = rules_engine_instance.evaluate(action_category, target_crop, env_context)
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
    target_crop: str,
    env_context: dict,
    location_zone: str,
    metadata_filters: Optional[dict] = None
) -> str:
    """
    [RECOMMENDED] Synthesizes hard environmental constraints and localized semantic guidelines
    into a single, complete agricultural strategy document.
    Calls both Engine Alpha (zero-hallucination rules) and Engine Beta (RAG community knowledge) in one pass,
    running them concurrently for minimum latency.
    """
    logging.info(f"[Router] Comprehensive consult for '{action_category}' on '{target_crop}'")

    # Auto-populate hardiness_zones from location_zone so callers use a clean API
    combined_filters = dict(metadata_filters) if metadata_filters else {}
    combined_filters.setdefault("hardiness_zones", location_zone)

    result_markdown = await router_instance.comprehensive_ag_consult(
        action_category, target_crop, env_context, query, combined_filters
    )
    return result_markdown

async def main():
    """
    Main entry point for the AgriCore MCP Server.
    Sets up standard I/O communication for the agent.
    """
    logging.info("Starting AgriCore MCP-Server via stdio...")
    try:
        # We define a standard stdio server loop for communication
        async with stdio_server() as (read_stream, write_stream):
            # Run the server with initial configuration
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except Exception as e:
        logging.error(f"Server encountered an error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server received shutdown signal. Exiting gracefully.")
    except Exception as e:
        logging.error(f"Fatal server failure: {e}")
