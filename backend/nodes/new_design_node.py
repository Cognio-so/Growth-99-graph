# nodes/new_design.py
from typing import Dict, Any

def new_design(state: Dict[str, Any]) -> Dict[str, Any]:
    ctx = state.get("context") or {}
    intent = ctx.get("intent") or {}
    json_schema = intent.get("json_schema")
    gi = ctx.get("generator_input") or {}
    gi["user_text"] = state.get("text","")

    if intent.get("doc_kind") == "json_schema" and isinstance(json_schema, dict):
        gi["schema_source"] = "doc"
        gi["json_schema"] = json_schema
    else:
        gi["schema_source"] = "none"

    # Clear edit history for new design
    state["edit_history"] = None
    state["existing_code"] = None

    ctx["generator_input"] = gi
    state["context"] = ctx
    return state

def new_design_route(state: Dict[str, Any]) -> str:
    ctx = state.get("context") or {}
    gi = ctx.get("generator_input") or {}
    if gi.get("schema_source") == "doc" and isinstance(gi.get("json_schema"), dict):
        return "generator"
    return "schema_extraction"     # fallback to schema_extraction (will pick CSV-random)
