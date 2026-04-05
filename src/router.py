import asyncio
import logging
from typing import Dict, Any, Optional


class IntelligentRouter:
    """
    Sprint 5: The Intelligent Router.
    Synthesizes Engine Alpha (Deterministic Rules) and Engine Beta (Semantic RAG)
    into a single, agent-friendly consultation endpoint.

    Both engines are fired concurrently via asyncio.gather() + asyncio.to_thread(),
    satisfying the parallel execution requirement (FR-5) and the sub-500ms
    latency constraint (NFR-4).
    """
    def __init__(self, rules_engine, rag_engine):
        self.rules_engine = rules_engine
        self.rag_engine = rag_engine

    async def comprehensive_ag_consult(
        self,
        action_category: str,
        target_plant: str,
        env_context: Dict[str, Any],
        query: str,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Asynchronously fires both Engine Alpha and Engine Beta in parallel
        and merges their outputs into a single cohesive agricultural strategy document.
        """
        logging.info(f"[Router] Comprehensive consult: action='{action_category}', plant='{target_plant}'")

        # Bias RAG toward the same entity Alpha evaluates (rules corpus may not tag by plant).
        rag_query = f"{query.strip()}\n\nPlant: {target_plant.strip()}"

        # Fire both engines concurrently — neither blocks the other.
        # asyncio.to_thread() offloads the synchronous engine calls to a thread pool.
        rules_output, rag_output = await asyncio.gather(
            asyncio.to_thread(self.rules_engine.evaluate, action_category, target_plant, env_context),
            asyncio.to_thread(self.rag_engine.search, rag_query, metadata_filters),
        )

        # Synthesize the final payload
        final_doc = (
            f"# 🚜 AGRICORE: COMPREHENSIVE CONSULT\n\n"
            f"> **Action**: `{action_category}` | **Plant**: `{target_plant}`\n\n"
            f"---\n\n"
            f"{rules_output}\n\n"
            f"---\n\n"
            f"{rag_output}\n"
        )

        return final_doc
