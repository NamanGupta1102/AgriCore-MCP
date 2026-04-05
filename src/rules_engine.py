import os
import json
import logging
from json_logic import jsonLogic
from typing import Dict, Any, List

class RulesEngine:
    """
    Engine Alpha (Deterministic Rules Engine)
    Loads and evaluates JSON rules for hard constraints.
    """
    def __init__(self, rules_dir: str = "data/rules"):
        self.rules_dir = rules_dir
        self.rules: List[Dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self):
        """Recursively scan and load all .json files in rules_dir."""
        if not os.path.exists(self.rules_dir):
            logging.warning(f"Rules directory '{self.rules_dir}' does not exist.")
            return

        for root, _, files in os.walk(self.rules_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            rule = json.load(f)
                            self.rules.append(rule)
                            logging.debug(f"Loaded rule: {rule.get('rule_id', file)}")
                    except Exception as e:
                        logging.error(f"Failed to load rule {file_path}: {e}")
        
        logging.info(f"Loaded {len(self.rules)} rules into Engine Alpha.")

    @staticmethod
    def _rule_matches_target(rule: Dict[str, Any], target: str) -> bool:
        """Match either target_plant or target_crop so crop JSON rules stay compatible."""
        plant = rule.get("target_plant")
        crop = rule.get("target_crop")
        return plant == target or crop == target

    def evaluate(self, action_category: str, target_plant: str, env_context: Dict[str, Any]) -> str:
        """
        Evaluate environmental conditions against loaded rules.
        Returns a formatted markdown string representing PASS/FAIL constraints.
        """
        relevant_rules = [
            r for r in self.rules
            if r.get("category") == action_category and self._rule_matches_target(r, target_plant)
        ]

        if not relevant_rules:
            return f"### 🛑 AGRICORE MCP: HARD CONSTRAINTS\n* **Status:** PASS\n* **Reasoning:** No strict rules found for {action_category} on {target_plant}."

        failed_rules = []
        passed_rules = []

        for rule in relevant_rules:
            logic = rule.get("logic_evaluator", {})
            try:
                # jsonLogic evaluates to a boolean
                passed = jsonLogic(logic, env_context)
                if passed:
                    passed_rules.append(rule)
                else:
                    failed_rules.append(rule)
            except Exception as e:
                logging.error(f"Logic evaluation failed for {rule.get('rule_id')}: {e}")
                failed_rules.append(rule) # Fail safely

        # If any rule fails, the entire constraint fails
        if failed_rules:
            rule_name = failed_rules[0].get("name", "Unknown Rule")
            reasoning = failed_rules[0].get("response_fail", "System logic failed.")
            return f"### 🛑 AGRICORE MCP: HARD CONSTRAINTS\n* **Status:** FAIL\n* **Rule Triggered:** {rule_name}\n* **System Reasoning:** {reasoning}"
        
        # All passed
        rule_name = relevant_rules[0].get("name", "Multiple Rules")
        reasoning = relevant_rules[0].get("response_pass", "All checks passed.")
        return f"### 🛑 AGRICORE MCP: HARD CONSTRAINTS\n* **Status:** PASS\n* **Rule Triggered:** {rule_name}\n* **System Reasoning:** {reasoning}"
