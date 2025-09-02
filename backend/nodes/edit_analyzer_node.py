# nodes/edit_analyzer.py
from typing import Dict, Any

def edit_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder: forward user text and any doc extraction for generator to
    produce an edit patch or improved output. Extend as needed.
    """
    ctx = state.get("context") or {}
    gi = ctx.get("generator_input") or {}
    gi["edit_request"] = True
    gi["user_text"] = state.get("text","")
    ctx["generator_input"] = gi
    state["context"] = ctx
    return state
