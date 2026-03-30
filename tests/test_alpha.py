"""
test_alpha.py — Unit tests for Engine Alpha (Deterministic Rules Engine).

Uses the `rules_engine` session fixture from conftest.py.
Run with: pytest tests/test_alpha.py -v
"""


def test_hard_constraint_fail_on_cold_soil(rules_engine):
    """
    Engine Alpha must return FAIL when soil temperature is below the 50°F threshold.
    Also verifies the 'HARD STOP' reasoning string is present in the output.
    """
    env = {"soil_temp_f": 45, "frost_risk_7_day": False}
    result = rules_engine.evaluate(
        action_category="planting",
        target_crop="corn",
        env_context=env
    )
    assert "FAIL" in result, f"Expected FAIL status, got:\n{result}"
    assert "HARD STOP" in result, f"Expected HARD STOP reasoning, got:\n{result}"


def test_hard_constraint_fail_on_frost_risk(rules_engine):
    """
    Engine Alpha must return FAIL when frost risk is present, even if soil temp is adequate.
    """
    env = {"soil_temp_f": 55, "frost_risk_7_day": True}
    result = rules_engine.evaluate(
        action_category="planting",
        target_crop="corn",
        env_context=env
    )
    assert "FAIL" in result, f"Expected FAIL status due to frost risk, got:\n{result}"


def test_hard_constraint_pass_on_good_conditions(rules_engine):
    """
    Engine Alpha must return PASS when soil temp >= 50°F and frost risk is false.
    """
    env = {"soil_temp_f": 55, "frost_risk_7_day": False}
    result = rules_engine.evaluate(
        action_category="planting",
        target_crop="corn",
        env_context=env
    )
    assert "PASS" in result, f"Expected PASS status, got:\n{result}"
    assert "Conditions met" in result, f"Expected pass reasoning string, got:\n{result}"


def test_no_rule_match_returns_pass(rules_engine):
    """
    When no rules exist for the given action+crop combination,
    the engine must return a PASS with a 'No strict rules found' message.
    """
    env = {"soil_temp_f": 70}
    result = rules_engine.evaluate(
        action_category="harvesting",
        target_crop="mystery_crop",
        env_context=env
    )
    assert "PASS" in result, f"Expected default PASS for unknown rule, got:\n{result}"
    assert "No strict rules" in result, f"Expected 'No strict rules' message, got:\n{result}"
