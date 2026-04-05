import sys
import os
import asyncio
import logging

# Ensure robust console encoding for Windows emojis
sys.stdout.reconfigure(encoding='utf-8')

# Import core engines
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from rules_engine import RulesEngine
from rag_engine import RagEngine
from router import IntelligentRouter

async def main():
    print("="*60)
    print("🌾 AGRICORE: NEW DATA VERIFICATION 🌾")
    print("="*60)
    
    # Initialize engines
    alpha_engine = RulesEngine(rules_dir=os.path.join("data", "rules"))
    beta_engine = RagEngine(db_dir=os.path.join("data", ".lancedb"))
    router = IntelligentRouter(alpha_engine, beta_engine)
    
    # scenario = [plant, category, temp, query, light]
    scenarios = [
        ("monstera", "temperature", 75, "How to care for my Monstera?", "bright_indirect"),
        ("pothos", "temperature", 70, "Tips for Pothos growth.", "low"),
        ("basil", "temperature", 75, "Best sunlight for Basil?", "direct"),
        # Test a fail case for temperature
        ("monstera", "temperature", 45, "Monstera cold stress?", "bright_indirect")
    ]

    for plant, cat, temp, query, light in scenarios:
        print(f"\n--- Testing Scenario: {plant.capitalize()} at {temp}°F ---")
        
        # Test direct router call (parallels)
        try:
            res = await router.comprehensive_ag_consult(
                action_category=cat,
                target_plant=plant,
                env_context={"room_temp_f": temp, "frost_risk_7_day": False},
                query=query,
                metadata_filters={"plant_tags": plant, "light_levels": light}
            )
            
            # Simple check for success (PASS/FAIL should be in output)
            if "PASS" in res:
                print("Status: ✅ PASS (Rules Met)")
            elif "FAIL" in res:
                print("Status: ❌ FAIL (Constraint Triggered)")
            else:
                print("Status: ❓ UNKNOWN output length")
            
            # Verify RAG is working
            if "AGRICORE: COMMUNITY GUIDELINES" in res or "semantic guidance" in res.lower() or "RAG" in res:
                print("RAG Ingestion: ✅ ACTIVE")
        except Exception as e:
            print(f"Error evaluating {plant}: {e}")

    print("\n" + "="*60)
    print("✅ Verification Run Complete.")

if __name__ == "__main__":
    asyncio.run(main())
