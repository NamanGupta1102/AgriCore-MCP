"""
Build static reference text for MCP Resources (Engine Alpha vars, RAG metadata).
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any, Iterator


def iter_jsonlogic_vars(node: Any) -> Iterator[str]:
    """Yield variable names referenced by json-logic rules ({\"var\": \"name\"})."""
    if isinstance(node, dict):
        if "var" in node:
            v = node["var"]
            if isinstance(v, str):
                yield v
            elif isinstance(v, list) and v and isinstance(v[0], str):
                yield v[0]
        for val in node.values():
            yield from iter_jsonlogic_vars(val)
    elif isinstance(node, list):
        for item in node:
            yield from iter_jsonlogic_vars(item)


def build_engine_alpha_env_context_reference_from_rules(rules: list[dict[str, Any]]) -> str:
    """
    Markdown listing each rule's target and json-logic variables.
    `rules` should be the in-memory list from `RulesEngine.rules`.
    """
    lines: list[str] = [
        "# Engine Alpha: `env_context` variables",
        "",
        "Rules live in `data/rules/*.json`. Each rule binds to `category` plus `target_plant` **or** `target_crop`.",
        "Only the variables listed for a matching rule are read by JSON Logic; missing keys can fail evaluation.",
        "",
        "- Temperatures: use **°F** as numbers (e.g. `72`, not strings).",
        "- Booleans: JSON `true` / `false` for yes/no risks.",
        "",
    ]

    if not rules:
        lines.append("_No JSON rules loaded._")
        return "\n".join(lines)

    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rules:
        cat = str(r.get("category", "?"))
        by_category[cat].append(r)

    for cat in sorted(by_category.keys()):
        lines.append(f"## category `{cat}`")
        lines.append("")
        bucket = sorted(
            by_category[cat],
            key=lambda x: (str(x.get("rule_id", "")), str(x.get("name", ""))),
        )
        for r in bucket:
            rid = r.get("rule_id", "?")
            rname = r.get("name", "")
            target = r.get("target_plant") or r.get("target_crop") or "?"
            logic = r.get("logic_evaluator", {})
            vars_sorted = sorted(set(iter_jsonlogic_vars(logic)))
            vars_md = ", ".join(f"`{v}`" for v in vars_sorted) if vars_sorted else "_none_"
            title = f" `{rname}`" if rname else ""
            lines.append(f"- **`{rid}`**{title} — target **`{target}`** — vars: {vars_md}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_engine_alpha_env_context_reference(rules_dir: str) -> str:
    """Load `data/rules` from disk (tests / offline helpers). Prefer `build_engine_alpha_env_context_reference_from_rules`."""
    rules: list[dict[str, Any]] = []
    if not os.path.isdir(rules_dir):
        return (
            "# Engine Alpha: `env_context` variables\n\n"
            f"_Rules directory not found: `{rules_dir}`_\n"
        )
    for root, _, files in os.walk(rules_dir):
        for name in files:
            if not name.endswith(".json"):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8") as f:
                    rules.append(json.load(f))
            except (OSError, json.JSONDecodeError):
                continue
    return build_engine_alpha_env_context_reference_from_rules(rules)


RAG_AND_LIGHT_REFERENCE = """\
# Engine Beta: RAG metadata & `light_level`

Guidelines are indexed from `data/guidelines/*.md` YAML front-matter.

## Filter keys (`metadata_filters` / consult extras)

| Key | Applies to | Notes |
|-----|------------|--------|
| `plant_tags` | `search_guidelines`, optional on `comprehensive_ag_consult` | String; should match corpus tags (e.g. `basil`, `tomato`). |
| `category` | both | e.g. `qa`, `disease_management`, `companion_planting`. |
| `light_levels` | `search_guidelines` only | For `comprehensive_ag_consult`, use the **`light_level`** tool argument instead (server sets `light_levels`). |

## `light_level` (consult) and `light_levels` (search)

Use one of:

- **`direct`** or **`full_sun`** — outdoor / strong sun (synonyms expanded server-side).
- **`bright_indirect`**, **`low`**, **`partial_shade`**, **`part_shade`** — shadier conditions.
- **`all`** — unknown light; matches broadly tagged chunks and skips strict light filtering.

The server expands common synonyms and always allows corpus tags of **`all`** where applicable.
"""

INDEX_REFERENCE = """\
# AgriCore MCP — reference resources

Fetch these URIs with **ListResources** / **ReadResource** when building tool arguments.

| URI | Purpose |
|-----|---------|
| `agricore://reference/index` | This index |
| `agricore://reference/engine-alpha-env-context` | Per-rule `env_context` / JSON Logic variable names (from `data/rules`) |
| `agricore://reference/rag-metadata-and-light-levels` | RAG filter keys and `light_level` vocabulary |
"""
