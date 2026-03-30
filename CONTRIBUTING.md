# Contributing to AgriCore MCP

Thank you for contributing! AgriCore MCP is a community-driven agricultural knowledge base. You don't need to know Python or databases to contribute — all knowledge lives in plain text files that you submit via a standard Pull Request.

---

## How to Add a Rule (Engine Alpha)

Rules live in `data/rules/` as `.json` files and are evaluated by the deterministic JSON-Logic engine. They represent **hard biological/regulatory constraints** where binary accuracy is critical (e.g., minimum germination temperatures, chemical withholding periods).

### Rule Schema

Create a file named `rule_<crop>_<topic>_<NNN>.json`:

```json
{
  "rule_id": "rule_wheat_frost_002",
  "name": "Wheat Spring Frost Window",
  "target_crop": "wheat_winter",
  "category": "planting",
  "description": "Brief description of what this rule prevents or enforces.",
  "logic_evaluator": {
    "and": [
      {">=": [{"var": "soil_temp_f"}, 34]},
      {"==": [{"var": "frost_risk_7_day"}, false]}
    ]
  },
  "response_pass": "Conditions met: Soil temperature and frost window are safe for winter wheat.",
  "response_fail": "HARD STOP: Soil temperature must be >= 34°F and no frost risk within 7 days."
}
```

### Field Reference

| Field | Type | Description |
|---|---|---|
| `rule_id` | `string` | Unique identifier. Convention: `rule_<crop>_<topic>_<NNN>` |
| `name` | `string` | Human-readable rule name |
| `target_crop` | `string` | Crop slug (e.g., `corn`, `wheat_winter`, `tomato`) |
| `category` | `string` | Action type: `planting`, `fertilizing`, `harvesting`, `spraying` |
| `description` | `string` | Plain-English description of what the rule prevents |
| `logic_evaluator` | `object` | A valid [JSON-Logic](https://jsonlogic.com/) expression |
| `response_pass` | `string` | Message returned to the LLM on PASS |
| `response_fail` | `string` | Message returned to the LLM on FAIL — start with `HARD STOP:` |

### Available `env_context` Variables

The host agent is responsible for populating these from external sensor data or weather APIs:

| Key | Type | Description |
|---|---|---|
| `soil_temp_f` | `number` | Soil temperature in Fahrenheit |
| `air_temp_f` | `number` | Air temperature in Fahrenheit |
| `frost_risk_7_day` | `boolean` | Whether frost is forecast within 7 days |
| `rainfall_48h_in` | `number` | Rainfall in the last 48 hours (inches) |
| `wind_speed_mph` | `number` | Current wind speed (mph) |

---

## How to Add a Guideline (Engine Beta)

Guidelines live in `data/guidelines/` as `.md` files with YAML frontmatter. They represent **localized, contextual best practices** (e.g., pest management, companion planting, soil amendments).

### Guideline Schema

Create a file named `guide_<crop>_<topic>_<region>.md`:

```markdown
---
id: "guide_pepper_aphid_sw_01"
title: "Organic Aphid Control for Bell Peppers in Arid Climates"
author: "your_github_username"
crop_tags: ["pepper", "bell_pepper"]
hardiness_zones: ["9a", "9b", "10a"]
soil_type: ["sandy", "loam"]
category: "pest_management"
---

# Organic Aphid Control for Bell Peppers

[Your Markdown content here. Be specific, cite sources where possible,
and focus on practices appropriate for the zones listed above.]
```

### Field Reference (YAML Frontmatter)

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique identifier. Must match the filename (without `.md`) |
| `title` | `string` | Descriptive title of the guideline |
| `author` | `string` | GitHub username or `extension_bot_<N>` for bot-generated content |
| `crop_tags` | `list[string]` | All crops this guideline applies to |
| `hardiness_zones` | `list[string]` | USDA zones this advice is valid for (use `["all"]` if universal) |
| `soil_type` | `list[string]` | Relevant soil types: `clay`, `loam`, `sandy`, `silt` |
| `category` | `string` | Topic: `disease_management`, `pest_management`, `companion_planting`, `soil_health`, `irrigation` |

---

## PR Checklist

Before submitting your Pull Request, verify the following:

- `[ ]` JSON rule files pass a JSON linter (e.g., [jsonlint.com](https://jsonlint.com/))
- `[ ]` Markdown guideline files include all required YAML frontmatter fields
- `[ ]` Guideline `id` matches the filename (without `.md`)
- `[ ]` Run `python src/build_index.py` to regenerate the vector index
- `[ ]` Run `pytest -v` — all tests must pass
- `[ ]` Run `python test_client.py` to verify the engines return expected output

---

## Questions?

Open a GitHub Issue and tag it `question` or `data-contribution`.
