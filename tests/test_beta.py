import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Ensure src/ is in the module path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from rag_engine import RagEngine

def test_engine_beta():
    # Load Engine beta focusing on the repo's data directory
    engine = RagEngine(db_dir=os.path.join(os.path.dirname(__file__), "..", "data", ".lancedb"))

    # 1. Test a general search without filters
    print("\n--- TEST: General Search ---")
    res1 = engine.search(query="How do I manage blight?")
    print(res1)
    assert "guide_tomato_blight_ne_01" in res1, "Failed to retrieve tomato blight guide"

    # 2. Test a search with specific metadata filtering
    print("\n--- TEST: Search with Filters ---")
    res2 = engine.search(query="soil requirements", metadata_filters={"crop_tags": ["corn"], "hardiness_zones": "5a"})
    print(res2)
    assert "guide_corn_soil_ph" in res2, "Failed to retrieve corn soil guide with filters"

    # 3. Test a search that shouldn't match anything useful (or with bad filter)
    print("\n--- TEST: Search with bad filter ---")
    res3 = engine.search(query="tomatoes", metadata_filters={"crop_tags": ["apples"]})
    print(res3)
    assert "guide_tomato_blight_ne_01" not in res3, "Retrieved a tomato guide despite searching for apples filter"

    print("\n✅ All Engine Beta unit checks passed successfully!")

if __name__ == "__main__":
    test_engine_beta()
