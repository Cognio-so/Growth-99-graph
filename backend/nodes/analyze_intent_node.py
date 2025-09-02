# nodes/analyze_intent.py
from typing import Dict, Any
from graph_types import GraphState
from llm import get_chat_model, call_llm_json

SYSTEM_PROMPT = """You are an intent analyzer for a design/code pipeline.
Use ONLY the provided TEXT and DOC extraction (if any) and output strict JSON:
{
  "is_edit": boolean,
  "is_new_design": boolean,
  "is_url": boolean,
  "doc_kind": "json_schema" | "guideline" | "other" | "none",
  "json_schema": object | null
}
Rules:
- "is_url" is true only if TEXT is a URL (no other text).
- "doc_kind=json_schema" when the uploaded doc content is a JSON schema; supply it in "json_schema".
- Do not add other keys.
"""

def _build_user_prompt(state: GraphState) -> str:
    text = state.get("text","")
    ex = (state.get("context") or {}).get("extraction") or {}
    doc_meta = {
        "mime": (state.get("doc") or {}).get("mime"),
        "name": (state.get("doc") or {}).get("name"),
        "size": (state.get("doc") or {}).get("size"),
    }
    return (
        "TEXT:\n"
        f"{text}\n\n"
        "DOC_META:\n"
        f"{doc_meta}\n\n"
        "DOC_TEXT_EXCERPT (first 4000 chars):\n"
        f"{ex.get('text_excerpt','')}\n\n"
        "JSON_CANDIDATES (from doc):\n"
        f"{ex.get('json_candidates',[])}\n"
    )

def analyze_intent(state: GraphState) -> GraphState:
    model = state.get("llm_model")
    chat = get_chat_model(model, temperature=0.0)
    result = call_llm_json(chat, SYSTEM_PROMPT, _build_user_prompt(state)) or {}

    is_edit = bool(result.get("is_edit"))
    is_new = bool(result.get("is_new_design"))
    is_url = bool(result.get("is_url"))
    doc_kind = result.get("doc_kind") or ("none" if not state.get("doc") else "other")
    json_schema = result.get("json_schema") if doc_kind == "json_schema" else None

    # Compute route (no heuristics):
    if is_edit:
        route = "edit_analyzer"
    elif is_url:
        route = "url_extraction"
    elif is_new:
        route = "new_design"
    else:
        route = "schema_extraction"  # inline schema or fallback CSV

    # Force regeneration path to schema_extraction
    if (state.get("metadata") or {}).get("regenerate"):
        route = "schema_extraction"

    ctx = state.get("context") or {}
    ctx["intent"] = {
        "is_edit": is_edit,
        "is_new_design": is_new,
        "is_url": is_url,
        "doc_kind": doc_kind,
        "json_schema": json_schema,
        "route": route,
        "model_used": model,
    }
    state["context"] = ctx
    return state

def route_from_intent(state: GraphState) -> str:
    return ((state.get("context") or {}).get("intent") or {}).get("route", "schema_extraction")


