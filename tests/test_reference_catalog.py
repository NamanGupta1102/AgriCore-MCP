"""reference_catalog: JSON Logic var extraction and Engine Alpha reference markdown."""

from reference_catalog import build_engine_alpha_env_context_reference_from_rules, iter_jsonlogic_vars


def test_iter_jsonlogic_vars_finds_nested_vars():
    logic = {
        "and": [
            {">=": [{"var": "air_temp_f"}, 28]},
            {"==": [{"var": "frost_risk_7_day"}, False]},
        ]
    }
    assert set(iter_jsonlogic_vars(logic)) == {"air_temp_f", "frost_risk_7_day"}


def test_build_reference_lists_targets_and_vars():
    rules = [
        {
            "rule_id": "rule_a",
            "name": "Test A",
            "category": "planting",
            "target_crop": "wheat_winter",
            "logic_evaluator": {
                "and": [
                    {">=": [{"var": "air_temp_f"}, 28]},
                    {"==": [{"var": "frost_risk_7_day"}, False]},
                ]
            },
        },
        {
            "rule_id": "rule_b",
            "category": "fertilizing",
            "target_crop": "corn",
            "logic_evaluator": {
                "and": [
                    {"==": [{"var": "heavy_rain_48hr"}, False]},
                    {">=": [{"var": "soil_temp_f"}, 50]},
                ]
            },
        },
    ]
    md = build_engine_alpha_env_context_reference_from_rules(rules)
    assert "fertilizing" in md
    assert "`air_temp_f`" in md
    assert "`soil_temp_f`" in md
    assert "wheat_winter" in md
    assert "rule_a" in md
