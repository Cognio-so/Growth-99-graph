# graph_types.py
from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict, total=False):
    session_id: str
    timestamp: str
    text: str
    llm_model: Optional[str]
    doc: Optional[Dict[str, Any]]        # {name,mime,size,path} if uploaded
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    context: Dict[str, Any]
    # Enhanced context for editing support
    existing_code: Optional[str]          # Existing code context for edits
    edit_history: Optional[Dict[str, Any]]  # Single edit context (not a list)
