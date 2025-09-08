# nodes/output_node.py
from typing import Dict, Any

def output_result(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final output node that returns the deployment URL or error information.
    Enhanced to detect edit operations and provide clear signal for frontend.
    """
    print("--- Running Output Node ---")
    
    ctx = state.get("context", {})
    sandbox_result = ctx.get("sandbox_result", {})
    validation_result = ctx.get("validation_result", {})
    
    # Check if this was an edit operation with document
    gi = ctx.get("generator_input", {})
    is_edit_operation = gi.get("is_edit_mode", False)
    has_document_info = gi.get("has_extracted_business_info", False)
    doc = state.get("doc")
    
    # Determine if we should clear the frontend form
    should_clear_form = is_edit_operation
    
    # Check if we have a successful deployment
    if sandbox_result.get("success") and sandbox_result.get("url"):
        if validation_result.get("success"):
            print("✅ Application successfully deployed and validated!")
            final_result = {
                "success": True,
                "url": sandbox_result["url"],
                "message": "Application deployed successfully with validation passed",
                "validation_passed": True,
                "deployment_info": {
                    "sandbox_id": sandbox_result.get("sandbox_id"),
                    "port": sandbox_result.get("port"),
                    "correction_attempts": ctx.get("correction_attempts", 0)
                }
            }
        else:
            print("⚠️ Application deployed but validation failed - using fallback")
            final_result = {
                "success": True,
                "url": sandbox_result["url"],
                "message": "Application deployed with fallback after validation failures",
                "validation_passed": False,
                "validation_errors": validation_result.get("errors", []),
                "deployment_info": {
                    "sandbox_id": sandbox_result.get("sandbox_id"),
                    "port": sandbox_result.get("port"),
                    "correction_attempts": ctx.get("correction_attempts", 0)
                }
            }
    else:
        print("❌ Deployment failed")
        final_result = {
            "success": False,
            "error": sandbox_result.get("error", "Unknown deployment error"),
            "message": "Application deployment failed",
            "validation_passed": False,
            "deployment_info": {
                "correction_attempts": ctx.get("correction_attempts", 0)
            }
        }
    
    # ENHANCED: Add clear signal for edit operations with documents
    if should_clear_form:
        print("🧹 Edit operation with document completed - signaling frontend to clear form")
        final_result["clear_form"] = True
        final_result["clear_reason"] = "edit_with_document_completed"
    else:
        final_result["clear_form"] = False
    
    ctx["final_result"] = final_result
    state["context"] = ctx
    return state



