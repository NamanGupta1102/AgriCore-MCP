import os
import sys

# Ensure src/ is in the module path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from rules_engine import RulesEngine

def test_engine_alpha():
    # Load Engine alpha focusing on the repo's data directory
    engine = RulesEngine(rules_dir=os.path.join(os.path.dirname(__file__), "..", "data", "rules"))

    # 1. Test a Failing condition (soil temp too low)
    env_fail = {"soil_temp_f": 45, "frost_risk_7_day": False}
    result_fail = engine.evaluate(action_category="planting", target_crop="corn", env_context=env_fail)
    print("--- FAIL EVALUATION ---")
    print(result_fail)
    assert "FAIL" in result_fail
    assert "HARD STOP" in result_fail
    
    # 2. Test a Passing condition (soil temp good, no frost)
    env_pass = {"soil_temp_f": 55, "frost_risk_7_day": False}
    result_pass = engine.evaluate(action_category="planting", target_crop="corn", env_context=env_pass)
    print("--- PASS EVALUATION ---")
    print(result_pass)
    assert "PASS" in result_pass
    assert "Conditions met" in result_pass

    print("\n✅ All Engine Alpha unit checks passed successfully!")

if __name__ == "__main__":
    test_engine_alpha()
