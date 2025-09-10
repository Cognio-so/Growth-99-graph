# nodes/analyze_intent.py
from typing import Dict, Any
from graph_types import GraphState
from llm import get_chat_model, call_llm_json

ENHANCED_SYSTEM_PROMPT = """You are an intelligent intent analyzer for a design/code pipeline.
Your job is to determine if the user wants to EDIT an existing application or create a NEW design.

Analyze the user's request and determine the intent based on:
1. The specific wording and context of the request
2. Whether there's an existing application available for editing
3. The nature of what the user is asking for

Use ONLY the provided TEXT and DOC extraction (if any) and output strict JSON:
{
  "is_edit": boolean,
  "is_new_design": boolean,
  "is_url": boolean,
  "doc_kind": "json_schema" | "guideline" | "other" | "none",
  "json_schema": object | null,
  "reasoning": "Brief explanation of your analysis and decision"
}

Rules:
- "is_url" is true only if TEXT is exactly a URL with no other text.
- "doc_kind=json_schema" when the uploaded doc content is a JSON schema; supply it in "json_schema".
- Analyze the user's intent intelligently based on context and wording
- Consider if the request implies modifying something existing vs creating something new
- Provide clear reasoning for your decision
- Do not add other keys beyond the specified ones.
"""

def _check_existing_application() -> bool:
    """Check if there's an existing application/sandbox available for editing."""
    try:
        # Import here to avoid circular imports
        from nodes.apply_to_Sandbox_node import _global_sandbox, _global_sandbox_info
        
        if not _global_sandbox:
            return False
        
        # Quick health check
        test_result = _global_sandbox.commands.run("echo 'test'", timeout=5)
        if test_result and test_result.stdout:
            # Check if Vite project exists
            project_check = _global_sandbox.commands.run("ls my-app/package.json", timeout=5)
            if project_check.exit_code == 0:
                return True
        
        return False
    except Exception as e:
        print(f"⚠️ Error checking existing application: {e}")
        return False

def _build_enhanced_user_prompt(state: GraphState) -> str:
    text = state.get("text","")
    ex = (state.get("context") or {}).get("extraction") or {}
    doc_meta = {
        "mime": (state.get("doc") or {}).get("mime"),
        "name": (state.get("doc") or {}).get("name"),
        "size": (state.get("doc") or {}).get("size"),
    }
    
    # Check if there's an existing application
    has_existing_app = _check_existing_application()
    
    prompt = (
        "USER REQUEST:\n"
        f"{text}\n\n"
        "DOCUMENT INFORMATION:\n"
        f"Document metadata: {doc_meta}\n"
        f"Document text excerpt: {ex.get('text_excerpt','')}\n"
        f"JSON candidates: {ex.get('json_candidates',[])}\n\n"
    )
    
    # Add context about existing application
    if has_existing_app:
        prompt += (
            "CONTEXT:\n"
            "There is an existing application that has been generated and deployed.\n"
            "The user may be requesting modifications to this existing application.\n\n"
        )
    else:
        prompt += (
            "CONTEXT:\n"
            "No existing application detected or this is the first request.\n"
            "The user may be requesting a new application to be created.\n\n"
        )
    
    prompt += (
        "ANALYSIS TASK:\n"
        "Analyze the user's request and determine their intent:\n"
        "- Does the request imply modifying something that already exists? → is_edit = true\n"
        "- Does the request describe creating a new application/website from scratch? → is_new_design = true\n"
        "- Is the request just a URL? → is_url = true\n"
        "\n"
        "Consider the wording, context, and what the user is actually asking for.\n"
        "Provide clear reasoning for your decision.\n"
    )
    
    return prompt

def analyze_intent(state: GraphState) -> GraphState:
    model = state.get("llm_model")
    chat = get_chat_model(model, temperature=0.0)
    
    # Use enhanced prompt
    user_prompt = _build_enhanced_user_prompt(state)
    result = call_llm_json(chat, ENHANCED_SYSTEM_PROMPT, user_prompt) or {}

    is_edit = bool(result.get("is_edit"))
    is_new = bool(result.get("is_new_design"))
    is_url = bool(result.get("is_url"))
    doc_kind = result.get("doc_kind") or ("none" if not state.get("doc") else "other")
    json_schema = result.get("json_schema") if doc_kind == "json_schema" else None
    reasoning = result.get("reasoning", "")

    # Compute route based on LLM decision
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
        state["edit_history"] = None
        state["existing_code"] = None

    # ENHANCED: Store original query when it's detected as "new design"
    if is_new and not (state.get("metadata") or {}).get("regenerate"):
        user_text = state.get("text", "")
        session_id = state.get("session_id")
        if user_text and session_id:
            from nodes.user_query_node import _store_original_new_design_query
            _store_original_new_design_query(session_id, user_text)
            print(f"✅ Stored original new design query for regeneration: '{user_text[:100]}...'")

    ctx = state.get("context") or {}
    ctx["intent"] = {
        "is_edit": is_edit,
        "is_new_design": is_new,
        "is_url": is_url,
        "doc_kind": doc_kind,
        "json_schema": json_schema,
        "route": route,
        "model_used": model,
        "reasoning": reasoning,  # Add reasoning for debugging
        "has_existing_app": _check_existing_application(),  # Track existing app status
    }
    state["context"] = ctx
    
    # Enhanced logging
    print(f"🎯 LLM Intent Analysis Results:")
    print(f"   - User text: '{state.get('text', '')}'")
    print(f"   - Has existing app: {_check_existing_application()}")
    print(f"   - Is edit: {is_edit}")
    print(f"   - Is new design: {is_new}")
    print(f"   - Is URL: {is_url}")
    print(f"   - Route: {route}")
    print(f"   - LLM Reasoning: {reasoning}")
    
    return state

def route_from_intent(state: GraphState) -> str:
    return ((state.get("context") or {}).get("intent") or {}).get("route", "schema_extraction")

