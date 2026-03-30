import sys
import os
import asyncio

# Ensure robust console encoding for Windows emojis
sys.stdout.reconfigure(encoding='utf-8')

# Import core engines
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from rules_engine import RulesEngine
from rag_engine import RagEngine
from router import IntelligentRouter

def main():
    print("="*60)
    print("🌾 WELCOME TO THE AGRICORE MCP ENGINE DEMO 🌾")
    print("="*60)
    print("Loading Engine Alpha (Deterministic JSON-Logic)...")
    alpha_engine = RulesEngine(rules_dir=os.path.join("data", "rules"))
    
    print("Loading Engine Beta (Vector RAG + BAAI Embeddings)...")
    # Silence internal warnings during the demo
    import logging
    logging.getLogger().setLevel(logging.ERROR)
    
    beta_engine = RagEngine(db_dir=os.path.join("data", ".lancedb"))
    router = IntelligentRouter(alpha_engine, beta_engine)
    print("\n✅ Systems Online! Let's watch the pipelines independently evaluate context.\n")

    # Demo 1: Engine Alpha
    print("--- [SCENARIO 1] HARD CONSTRAINTS VERIFICATION (ENGINE ALPHA) ---")
    print("Context: Attempting to plant corn.")
    print("Variables: Soil temperature is 45°F, and frost risk is pending.")
    res = alpha_engine.evaluate(
        action_category="planting", 
        target_crop="corn", 
        env_context={"soil_temp_f": 45, "frost_risk_7_day": True}
    )
    print("\n" + res + "\n")

    # Demo 2: Engine Beta
    print("--- [SCENARIO 2] SEMANTIC GUIDELINE RETRIEVAL (ENGINE BETA) ---")
    print("Context: 'What are the best methods to manage early blight?'")
    print("Filters: Ensuring responses are constrained specifically to [tomato] crops.")
    res = beta_engine.search(
        query="What are the best methods to manage early blight?",
        metadata_filters={"crop_tags": ["tomato"]}
    )
    print("\n" + res + "\n")

    # Demo 3: Intelligent Router (Sprint 5)
    print("--- [SCENARIO 3] COMPREHENSIVE CONSULTATION (INTELLIGENT ROUTER) ---")
    print("Context: Complete consultation for corn planting in borderline conditions.")
    print("Fires both Engine Alpha & Beta in a single unified call.")
    res = asyncio.run(router.comprehensive_ag_consult(
        action_category="planting",
        target_crop="corn",
        env_context={"soil_temp_f": 45, "frost_risk_7_day": True},
        query="Best practices for planting corn in cold soil conditions?",
        metadata_filters={"crop_tags": ["corn"]}
    ))
    print("\n" + res + "\n")
    
    print("="*60)
    print("✅ Demo completed! All three engines are successfully returning markdown.")

if __name__ == "__main__":
    main()
