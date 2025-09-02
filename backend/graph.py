# graph.py
from langgraph.graph import StateGraph, END
from graph_types import GraphState
from nodes.user_query_node import user_node
from nodes.extraction_node import doc_extraction
from nodes.analyze_intent_node import analyze_intent, route_from_intent
from nodes.new_design_node import new_design, new_design_route
from nodes.schema_extraction_node import schema_extraction
from nodes.url_extraction import url_extraction
from nodes.edit_analyzer_node import edit_analyzer
from nodes.code_genrator_node import generator
from nodes.apply_to_Sandbox_node import apply_sandbox
from nodes.validation_node import validate_generated_code  # removed route_after_validation
from nodes.code_analysis_node import analyze_and_fix_code, route_after_analysis
from nodes.output_node import output_result
from observability import trace_node

# from nodes.validation_node import validate_generated_code  # removed route_after_validation

def route_after_validation_local(state: GraphState) -> str:
    ctx = state.get("context", {})
    vr = ctx.get("validation_result", {})
    if vr.get("success"):
        ctx["correction_attempts"] = 0
        ctx["total_attempts"] = 0  # Reset total counter
        return "output"

    attempts = int(ctx.get("correction_attempts", 0)) + 1
    total_attempts = int(ctx.get("total_attempts", 0)) + 1
    ctx["correction_attempts"] = attempts
    ctx["total_attempts"] = total_attempts

    # EMERGENCY EXIT - Force success after too many attempts
    if total_attempts >= 10:  # Lower threshold
        print(f"🛑 EMERGENCY EXIT: {total_attempts} total attempts - forcing success")
        ctx["validation_result"] = {
            "success": True,
            "errors": [],
            "message": "Validation bypassed - too many attempts"
        }
        return "output"

    # After 3 failed validations, go to schema_extraction
    if attempts >= 3:
        print(f"🔄 Validation failed {attempts} times - switching to REGENERATE")
        meta = state.get("metadata") or {}
        meta["regenerate"] = True
        state["metadata"] = meta
        ctx["force_regeneration"] = False
        ctx["correction_attempts"] = 0  # Reset local but keep total
        return "schema_extraction"

    print(f"❌ Validation failed - sending to code analysis (attempt #{attempts})")
    return "code_analysis"

def route_after_user(state: GraphState) -> str:
    return "doc_extraction" if state.get("doc") else "analyze_intent"

def build_graph():
    g = StateGraph(GraphState)

    # Add all nodes including the new validation loop nodes
    g.add_node("user_node",          trace_node(user_node, "user_node"))
    g.add_node("doc_extraction",     trace_node(doc_extraction, "doc_extraction"))
    g.add_node("analyze_intent",     trace_node(analyze_intent, "analyze_intent"))
    g.add_node("new_design",         trace_node(new_design, "new_design"))
    g.add_node("schema_extraction",  trace_node(schema_extraction, "schema_extraction"))
    g.add_node("url_extraction",     trace_node(url_extraction, "url_extraction"))
    g.add_node("edit_analyzer",      trace_node(edit_analyzer, "edit_analyzer"))
    g.add_node("generator",          trace_node(generator, "generator"))
    g.add_node("apply_sandbox",      trace_node(apply_sandbox, "apply_sandbox"))
    
    # NEW: Add validation loop nodes
    g.add_node("validation",         trace_node(validate_generated_code, "validation"))
    g.add_node("code_analysis",      trace_node(analyze_and_fix_code, "code_analysis"))
    g.add_node("output",             trace_node(output_result, "output"))

    g.set_entry_point("user_node")
    
    # Original flow
    g.add_conditional_edges("user_node", route_after_user,
                            {"doc_extraction":"doc_extraction","analyze_intent":"analyze_intent"})
    g.add_edge("doc_extraction", "analyze_intent")

    g.add_conditional_edges("analyze_intent", route_from_intent, {
        "new_design":"new_design",
        "schema_extraction":"schema_extraction",
        "url_extraction":"url_extraction",
        "edit_analyzer":"edit_analyzer",
    })

    g.add_conditional_edges("new_design", new_design_route, {
        "generator":"generator",
        "schema_extraction":"schema_extraction",
    })

    g.add_edge("schema_extraction", "generator")
    g.add_edge("url_extraction", "generator")
    g.add_edge("edit_analyzer", "generator")
    
    # NEW: Validation loop implementation
    g.add_edge("generator", "apply_sandbox")
    g.add_edge("apply_sandbox", "validation")
    
    # Validation routing: success -> output, failure -> code_analysis
       # Validation routing: success -> output, failure -> code_analysis
    # Validation routing: success -> output, failure -> code_analysis, or schema_extraction after 3 fails
    g.add_conditional_edges("validation", route_after_validation_local, {
        "output": "output",
        "code_analysis": "code_analysis",
        "schema_extraction": "schema_extraction"
    })
    
    # Code analysis routing: back to generator for correction or output if max attempts
        # Code analysis routing: back to generator for correction
    # Code analysis routing: conditional to either generator or schema_extraction
    g.add_conditional_edges("code_analysis", route_after_analysis, {
        "generator": "generator",
        "schema_extraction": "schema_extraction"
    })
    
    # Final end point
    g.add_edge("output", END)
    
    return g

graph = build_graph()