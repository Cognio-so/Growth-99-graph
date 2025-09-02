# nodes/code_generator_node.py
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from llm import get_chat_model

# Define paths for both the prompt template and the UI guidelines context file
PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent / "prompts.md"
UI_DESIGN_MD_PATH = Path(__file__).parent.parent / "UI_design.md"

def _load_prompt_template_and_context() -> str:
    """
    Loads the main prompt template and injects the content from the UI design file.
    """
    # Read the main prompt template
    prompt_template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")

    # Read the UI design guidelines file
    if UI_DESIGN_MD_PATH.exists():
        ui_guidelines_content = UI_DESIGN_MD_PATH.read_text(encoding="utf-8")
    else:
        ui_guidelines_content = "No UI guidelines provided. Use your best judgment for UI/UX design."

    # Use simple string replacement instead of format() to avoid brace conflicts
    return prompt_template.replace("{ui_guidelines}", ui_guidelines_content)

def _extract_python_code(markdown_text: str) -> str:
    """Extracts the python code from a markdown code block."""
    match = re.search(r"```python\n(.*?)\n```", markdown_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return markdown_text

def _build_generator_user_prompt(gi: Dict[str, Any]) -> str:
    """Constructs the detailed user-facing prompt for the generator LLM."""
    user_text = gi.get("user_text", "No user text provided.")
    json_schema = gi.get("json_schema")
    
    prompt_parts = [f"## USER REQUEST\n{user_text}"]
    
    if json_schema and isinstance(json_schema, dict):
        schema_str = json.dumps(json_schema, indent=2)
        prompt_parts.append(f"## JSON SCHEMA\nThis schema defines the data structure you must use:\n```json\n{schema_str}\n```")
    
    return "\n\n".join(prompt_parts)

def _build_correction_prompt(ctx: Dict[str, Any]) -> str:
    """Build a targeted correction prompt when validation fails."""
    code_analysis = ctx.get("code_analysis", {})
    
    if not code_analysis.get("correction_needed"):
        return ""
    
    error_report = code_analysis.get("error_report", "")
    fix_suggestions = code_analysis.get("fix_suggestions", [])
    attempt_count = code_analysis.get("attempt_count", 1)
    correction_data = code_analysis.get("correction_data", {})
    target_files = code_analysis.get("target_files", [])
    
    correction_prompt = f"""
## TARGETED CODE CORRECTION REQUIRED (Attempt #{attempt_count})

The previously generated code has validation errors that need to be fixed.
Instead of regenerating everything, you need to provide targeted corrections.

### VALIDATION ERRORS FOUND:
{error_report}

### FILES THAT NEED CORRECTION:
{chr(10).join(f"- {file}" for file in target_files)}

### SPECIFIC FIX REQUIREMENTS:
{chr(10).join(f"- {suggestion}" for suggestion in fix_suggestions)}

### CRITICAL INSTRUCTIONS:
1. Provide ONLY the corrected file content for the files that have errors
2. Do NOT regenerate the entire application
3. Focus on fixing the specific validation errors
4. Ensure proper JSX syntax with double braces for style attributes
5. Fix unescaped quotes in className attributes
6. Ensure proper brace matching

### OUTPUT FORMAT:
Return a Python dictionary with the corrected file content:
```python
{{
    "files_to_correct": [
        {{
            "path": "src/App.jsx",
            "corrected_content": "// corrected JSX content here"
        }}
    ],
    "new_files": []  # if any new files need to be created
}}
```

Generate ONLY the corrected file content for the problematic files.
"""
    
    return correction_prompt


def generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the LLM to generate a Python script compatible with the E2B Sandbox SDK.
    Now handles both initial generation and targeted error corrections.
    """
    print("--- Running Generator Node ---")
    ctx = state.get("context", {})
    gi = ctx.get("generator_input", {})
    
    # Check if we need to force full regeneration after repeated failures
    if ctx.get("force_regeneration", False):
        print(" FORCE REGENERATION MODE - Previous corrections failed repeatedly")
        print("🆕 Running generator for full code regeneration...")
        # Clear the flag and proceed with full generation
        ctx["force_regeneration"] = False
        ctx["correction_attempts"] = 0
        return _generate_initial_code(state)
    
    # Check if this is a correction attempt
    is_correction = ctx.get("code_analysis", {}).get("correction_needed", False)
    
    if is_correction:
        print("🔄 Running generator for targeted code correction...")
        system_prompt = _load_prompt_template_and_context()
        correction_prompt = _build_correction_prompt(ctx)
        user_prompt = f"{_build_generator_user_prompt(gi)}\n\n{correction_prompt}"
    else:
        print("🆕 Running generator for initial code generation...")
        system_prompt = _load_prompt_template_and_context()
        user_prompt = _build_generator_user_prompt(gi)

    # Use Groq by default
    model = state.get("llm_model", "groq-default") 
    chat_model = get_chat_model(model, temperature=0.1)  # Lower temperature for corrections
    
    print(f"Calling generator LLM (Groq - moonshotai/kimi-k2-instruct)...")
    response = chat_model.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    
    if is_correction:
        # For corrections, extract the correction data structure
        correction_data = _extract_correction_data(response.content)
        if correction_data:
            ctx["correction_data"] = correction_data
            ctx["generation_result"] = {
                "e2b_script": response.content,
                "is_correction": True,
                "correction_attempt": ctx.get("correction_attempts", 0) + 1
            }
            print("✅ Targeted correction data generated successfully")
        else:
            print("⚠️ Failed to extract correction data, using fallback approach")
            ctx["generation_result"] = {
                "e2b_script": response.content,
                "is_correction": True,
                "correction_attempt": ctx.get("correction_attempts", 0) + 1
            }
    else:
        # For initial generation
        ctx["generation_result"] = {
            "e2b_script": response.content,
            "is_correction": False
        }
        print("Generator successful. E2B script generated.")
    
    state["context"] = ctx
    return state


def _extract_correction_data(response_content: str) -> Optional[Dict[str, Any]]:
    """Extract correction data from LLM response."""
    try:
        # Look for Python dictionary in the response
        import re
        import ast
        
        # Find Python dictionary pattern
        dict_match = re.search(r'```python\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if dict_match:
            dict_str = dict_match.group(1)
            # Parse the dictionary
            correction_data = ast.literal_eval(dict_str)
            return correction_data
        
        # Alternative: try to find JSON-like structure
        json_match = re.search(r'\{.*?\}', response_content, re.DOTALL)
        if json_match:
            import json
            try:
                correction_data = json.loads(json_match.group(0))
                return correction_data
            except:
                pass
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error extracting correction data: {e}")
        return None