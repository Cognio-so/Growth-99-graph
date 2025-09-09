# observability.py
import os
from typing import Any, Callable
from functools import wraps
from langsmith import traceable
from langchain_core.tracers.context import tracing_v2_enabled

# Ensure LangSmith tracing is enabled
os.environ["LANGCHAIN_TRACING_V2"] = "true"
# Make sure you have these environment variables set:
# LANGCHAIN_API_KEY = "your-api-key"
# LANGCHAIN_PROJECT = "your-project-name" (optional, defaults to "default")

def trace_graph_invoke(graph_func: Callable) -> Callable:
    """Decorator to trace the entire graph execution"""
    @wraps(graph_func)
    @traceable(
        name="graph_execution",
        run_type="chain",
        tags=["graph", "api_call"]
    )
    def wrapper(state: dict[str, Any]) -> dict[str, Any]:
        # Add metadata to the current run
        import langsmith
        run = langsmith.get_current_run_tree()
        if run:
            run.extra["metadata"] = {
                "session_id": state.get("session_id"),
                "llm_model": state.get("llm_model"),
                "has_doc": bool(state.get("doc")),
                "text_preview": (state.get("text") or "")[:100]
            }
        
        return graph_func(state)
    
    return wrapper

def trace_node(node_func: Callable, node_name: str) -> Callable:
    """Decorator to trace individual nodes in the graph"""
    @wraps(node_func)
    def wrapper(state: dict[str, Any]) -> dict[str, Any]:
        
        @traceable(
            name=node_name,
            run_type="chain",  # Use "chain" for better Studio visualization
            tags=[node_name, "node", "graph_execution"],
            metadata={
                "node_name": node_name,
                "session_id": state.get("session_id"),
                "thread_id": state.get("session_id"),
                "input_keys": list(state.keys()) if isinstance(state, dict) else [],
                "timestamp": state.get("timestamp")
            }
        )
        def _execute_node(input_state):
            return node_func(input_state)
        
        return _execute_node(state)
    
    return wrapper

def trace_llm_call(func: Callable) -> Callable:
    """Decorator specifically for LLM calls within nodes"""
    @wraps(func)
    @traceable(
        run_type="llm",
        tags=["llm_call"]
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper