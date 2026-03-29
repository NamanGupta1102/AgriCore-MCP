import sys
sys.stdout = open('debug.txt', 'w', encoding='utf-8')
sys.stderr = sys.stdout

import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from rag_engine import RagEngine

try:
    engine = RagEngine(db_dir="data/.lancedb")
    print("Engine inited")
    res1 = engine.search("blight")
    print("Res1:", res1)
    
    res2 = engine.search("soil requirements", metadata_filters={"crop_tags": ["corn"], "hardiness_zones": "5a"})
    print("Res2:", res2)
except Exception as e:
    import traceback
    traceback.print_exc()

sys.stdout.close()
