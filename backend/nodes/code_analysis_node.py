# nodes/code_analysis_node.py
import re
from typing import Dict, Any, List
from llm import get_chat_model

def analyze_and_fix_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze validation errors and prepare context for LLM correction.
    Now prepares targeted file corrections instead of regenerating everything.
    """
    print("--- Running Code Analysis Node ---")
    
    ctx = state.get("context", {})
    validation_result = ctx.get("validation_result", {})
    generation_result = ctx.get("generation_result", {})
    
    if not validation_result.get("errors"):
        print("❌ No validation errors found to analyze")
        return state
    
    errors = validation_result["errors"]
    original_script = generation_result.get("e2b_script", "")
    file_content = validation_result.get("file_content_for_correction", {})
    
    print(f"🔍 Analyzing {len(errors)} validation errors...")
    
    # Categorize errors by type
    error_analysis = _categorize_errors(errors)
    
    # Generate detailed error report
    error_report = _generate_error_report(errors, original_script)
    
    # NEW: Prepare targeted correction data
    correction_data = _prepare_targeted_corrections(errors, file_content)
    
    # Extract actual target files from correction data
    target_files = []
    if "files_to_correct" in correction_data:
        target_files = [file_info.get("path", "") for file_info in correction_data["files_to_correct"] if file_info.get("path")]
    
    # Create correction context for LLM
    correction_context = {
        "original_script": original_script,
        "error_analysis": error_analysis,
        "error_report": error_report,
        "errors": errors,
        "correction_needed": True,
        "attempt_count": ctx.get("correction_attempts", 0) + 1,
        "correction_data": correction_data,
        "target_files": target_files  # Fixed: Use actual file paths
    }
    
    # Generate specific fix suggestions
    fix_suggestions = _generate_fix_suggestions(errors, original_script)
    correction_context["fix_suggestions"] = fix_suggestions
    
    print(f"📋 Error analysis complete:")
    print(f"   - Syntax errors: {len(error_analysis['syntax_errors'])}")
    print(f"   - JSX errors: {len(error_analysis['jsx_errors'])}")
    print(f"   - Import errors: {len(error_analysis['import_errors'])}")
    print(f"   - Component errors: {len(error_analysis['component_errors'])}")
    print(f"   - Files to correct: {target_files}")
    print(f"   - Attempt #{correction_context['attempt_count']}")
    
    ctx["code_analysis"] = correction_context
    ctx["correction_attempts"] = correction_context["attempt_count"]
    ctx["correction_data"] = correction_data  # Store for apply_sandbox to use
    
    state["context"] = ctx
    return state


def _categorize_errors(errors: List[Any]) -> Dict[str, Any]:
    """Categorize validation errors by type and severity."""
    try:
        # Fix: Handle both string and dict error formats
        categorized = {
            "syntax_errors": [],
            "jsx_errors": [],
            "import_errors": [],
            "component_errors": [],
            "other_errors": []
        }
        
        for error in errors:
            # Handle both string and dict error formats
            if isinstance(error, str):
                # If error is a string, extract type from the string
                error_type = _extract_error_type_from_string(error)
                error_data = {"message": error, "type": error_type}
            elif isinstance(error, dict):
                # If error is already a dict, use it directly
                error_type = error.get("type", "other")
                error_data = error
            else:
                # Fallback for unknown error types
                error_type = "other"
                error_data = {"message": str(error), "type": error_type}
            
            # Categorize based on type
            if error_type == "syntax":
                categorized["syntax_errors"].append(error_data)
            elif error_type == "jsx":
                categorized["jsx_errors"].append(error_data)
            elif error_type == "import":
                categorized["import_errors"].append(error_data)
            elif error_type == "component":
                categorized["component_errors"].append(error_data)
            else:
                categorized["other_errors"].append(error_data)
        
        return categorized
        
    except Exception as e:
        print(f"❌ Error in error categorization: {e}")
        # Return safe fallback
        return {
            "syntax_errors": [],
            "jsx_errors": [],
            "import_errors": [],
            "component_errors": [],
            "other_errors": errors if isinstance(errors, list) else [str(errors)]
        }

def _extract_error_type_from_string(error_string: str) -> str:
    """Extract error type from error string message."""
    error_lower = error_string.lower()
    
    if any(word in error_lower for word in ["syntax", "parse", "token"]):
        return "syntax"
    elif any(word in error_lower for word in ["jsx", "react", "component"]):
        return "component"
    elif any(word in error_lower for word in ["import", "module", "require"]):
        return "import"
    elif any(word in error_lower for word in ["jsx", "className", "style"]):
        return "jsx"
    else:
        return "other"


def _generate_error_report(errors: List[Any], script: str) -> str:
    """Generate a detailed error report for the LLM."""
    report_lines = ["VALIDATION ERROR REPORT", "=" * 50]
    
    for i, error in enumerate(errors, 1):
        report_lines.append(f"\nERROR #{i}:")
        
        if isinstance(error, dict):
            report_lines.append(f"Type: {error.get('type', 'unknown')}")
            report_lines.append(f"Message: {error.get('message', 'No message')}")
            
            if error.get("line"):
                report_lines.append(f"Line: {error['line']}")
            
            if error.get("pattern"):
                report_lines.append(f"Pattern: {error['pattern']}")
            
            if error.get("fix"):
                report_lines.append(f"Suggested Fix: {error['fix']}")
            
            if error.get("details"):
                report_lines.append(f"Details: {error['details']}")
        else:
            report_lines.append(f"Message: {str(error)}")
    
    # Add script preview
    report_lines.append(f"\nORIGINAL SCRIPT PREVIEW:")
    report_lines.append("-" * 30)
    script_lines = script.split('\n')
    preview_lines = script_lines[:20] if len(script_lines) > 20 else script_lines
    report_lines.extend(preview_lines)
    
    if len(script_lines) > 20:
        report_lines.append(f"... ({len(script_lines) - 20} more lines)")
    
    return "\n".join(report_lines)


def _generate_fix_suggestions(errors: List[Any], script: str) -> List[str]:
    """Generate specific fix suggestions based on error types."""
    suggestions = []
    
    for error in errors:
        if isinstance(error, dict):
            error_type = error.get("type", "")
        else:
            error_type = _extract_error_type_from_string(str(error))
        
        if "jsx_style" in error_type:
            suggestions.append("Fix JSX style syntax: Replace style={ ... } with style={{ ... }}")
        
        if "missing_import" in error_type:
            suggestions.append("Add missing React import: import React from 'react';")
        
        if "missing_export" in error_type:
            suggestions.append("Add export default statement for the main component")
        
        if "jsx_braces" in error_type:
            suggestions.append("Check JSX brace matching - ensure equal opening and closing braces")
        
        if "tailwind" in error_type:
            suggestions.append("Ensure Tailwind CSS configuration is properly set up")
        
        if "syntax" in error_type:
            suggestions.append("Fix Python syntax errors in the generated script")
    
    return suggestions


def _prepare_targeted_corrections(errors: List[Any], file_content: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare targeted correction data for specific files."""
    corrections = {
        "files_to_correct": [],
        "new_files": [],
        "error_summary": []
    }
    
    # Get actual file content from sandbox
    files_content = file_content.get("files_content", {})
    # Also consider explicitly missing component paths
    missing_components = set(file_content.get("missing_components", []) or [])

    # Group errors by file
    file_errors = {}
    for error in errors:
        if isinstance(error, dict):
            file_path = error.get("file", "src/App.jsx")
            error_msg = error.get("message", str(error))
            missing_path = error.get("missing_component_path") or error.get("missing_file")
            if isinstance(missing_path, str) and missing_path.startswith("src/"):
                missing_components.add(missing_path)
        else:
            file_path = "src/App.jsx"
            error_msg = str(error)
        
        if file_path not in file_errors:
            file_errors[file_path] = []
        file_errors[file_path].append({
            "message": error_msg,
            "type": error.get("type", "unknown") if isinstance(error, dict) else "unknown"
        })
    
    # Prepare correction data for each file
    for file_path, file_specific_errors in file_errors.items():
        current_content = files_content.get(file_path, "")
        corrections["files_to_correct"].append({
            "path": file_path,
            "current_content": current_content or "",
            "errors": file_specific_errors,
            "needs_correction": True
        })
        error_types = [err["type"] for err in file_specific_errors]
        corrections["error_summary"].append({
            "file": file_path,
            "error_count": len(file_specific_errors),
            "error_types": error_types
        })

    # Add missing components as empty targets to be created
    for mpath in sorted(missing_components):
        if mpath not in files_content:
            corrections["files_to_correct"].append({
                "path": mpath,
                "current_content": "",
                "errors": [{"type": "missing_component", "message": "Create this component file"}],
                "needs_correction": True
            })
            corrections["new_files"].append({"path": mpath})

    return corrections


def _determine_correction_type(errors: List[Any]) -> str:
    """Determine the type of correction needed for a file."""
    for error in errors:
        if isinstance(error, dict):
            error_type = error.get("type", "")
        else:
            error_type = _extract_error_type_from_string(str(error))
        
        if "jsx_style" in error_type:
            return "jsx_syntax_fix"
        elif "jsx_quotes" in error_type:
            return "jsx_quotes_fix"
        elif "jsx_braces" in error_type:
            return "jsx_braces_fix"
        elif "missing_import" in error_type:
            return "import_fix"
        elif "missing_export" in error_type:
            return "export_fix"
    
    return "general_fix"


def route_after_analysis(state: Dict[str, Any]) -> str:
    """Route after code analysis - check if we need full regeneration after repeated failures."""
    ctx = state.get("context", {})
    attempts = ctx.get("correction_attempts", 0)
    
    # After 4 failed correction attempts, force full regeneration
    if attempts >= 4:
        print(f"🔄 Too many correction attempts ({attempts}) - forcing full regeneration")
        # Reset correction attempts and trigger full regeneration
        ctx["correction_attempts"] = 0
        ctx["force_regeneration"] = True
        return "generator"
    
    print(f"🔄 Sending to generator for correction (attempt #{attempts})")
    return "generator"
