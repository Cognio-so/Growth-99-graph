# nodes/edit_analyzer.py
from typing import Dict, Any
from graph_types import GraphState
from llm import get_chat_model, call_llm_json

SYSTEM_PROMPT = """You are an edit analyzer for a React application. 
Analyze the user's edit request and determine what changes need to be made.

Analyze the user's request and output strict JSON:
{
  "edit_type": "modify_existing" | "add_new_component" | "modify_styling" | "modify_functionality" | "modify_layout",
  "target_files": ["src/App.jsx", "src/components/Component.jsx"],
  "changes_description": "Detailed description of what needs to be changed",
  "specific_requirements": [
    "Change button color from blue to red",
    "Add new input field for email",
    "Modify the header text"
  ],
  "preserve_existing": boolean,
  "context_needed": "What existing code context is needed for this edit"
}

Rules:
- "edit_type" should categorize the type of edit being requested
- "target_files" should list the specific files that need modification
- "changes_description" should be a clear summary of the edit request
- "specific_requirements" should list the exact changes needed
- "preserve_existing" should be true if existing functionality should be kept
- "context_needed" should describe what existing code context is required
"""

def _capture_existing_code_context(state: GraphState) -> str:
    """Capture the existing code context from the current sandbox."""
    try:
        # Import here to avoid circular imports
        from nodes.apply_to_Sandbox_node import _global_sandbox
        
        if not _global_sandbox:
            print("❌ No global sandbox available for context capture")
            return "No existing sandbox available"
        
        print(" Capturing existing code context for edit analysis...")
        
        # Capture critical files
        critical_files = [
            "src/App.jsx", "src/main.jsx", "src/index.css"
        ]
        
        context_parts = []
        for file_path in critical_files:
            try:
                full_path = f"my-app/{file_path}"
                content = _global_sandbox.files.read(full_path)
                if content:
                    context_parts.append(f"## {file_path}:\n```jsx\n{content}\n```")
                    print(f"   ✅ Captured: {file_path}")
                else:
                    print(f"   ⚠️ Empty content for: {file_path}")
            except Exception as e:
                print(f"   ❌ Could not capture {file_path}: {e}")
        
        # Capture component files
        try:
            ls_result = _global_sandbox.commands.run("find my-app/src/components -name '*.jsx' -o -name '*.js'", timeout=10)
            if ls_result.stdout:
                component_files = ls_result.stdout.strip().split('\n')
                for file_path in component_files:
                    if file_path and "my-app/" in file_path:
                        relative_path = file_path.replace("my-app/", "")
                        try:
                            content = _global_sandbox.files.read(file_path)
                            if content:
                                context_parts.append(f"## {relative_path}:\n```jsx\n{content}\n```")
                                print(f"   ✅ Captured component: {relative_path}")
                            else:
                                print(f"   ⚠️ Empty content for component: {relative_path}")
                        except Exception as e:
                            print(f"   ❌ Could not capture component {relative_path}: {e}")
            else:
                print("   ⚠️ No component files found")
        except Exception as e:
            print(f"   ⚠️ Could not scan components directory: {e}")
        
        if context_parts:
            full_context = "\n\n".join(context_parts)
            print(f"✅ Captured {len(context_parts)} files for edit context")
            return full_context
        else:
            print("❌ No files captured for edit context")
            return "No existing code files found"
            
    except Exception as e:
        print(f"❌ Error capturing existing code context: {e}")
        import traceback
        traceback.print_exc()
        return f"Error capturing context: {str(e)}"

def _build_edit_analysis_prompt(state: GraphState) -> str:
    """Build the prompt for analyzing edit requests."""
    text = state.get("text", "")
    ##
    # CRITICAL: Capture the existing code context
    existing_code = _capture_existing_code_context(state)
    
    prompt = f"""
## USER EDIT REQUEST:
{text}

## EXISTING CODE CONTEXT (CURRENT UI DESIGN):
{existing_code}

## ANALYSIS TASK:
Analyze this edit request and determine:
1. What type of edit is being requested
2. Which files need to be modified
3. What specific changes are needed
4. How to preserve existing functionality
5. What context is needed from the existing code

IMPORTANT: The user wants to modify the EXISTING UI shown above, not create a new one.
Focus on what specific changes need to be made to the current design.

Provide your analysis in the required JSON format.
"""
    return prompt

def edit_analyzer(state: GraphState) -> GraphState:
    """
    Analyze user edit requests to determine what changes need to be made.
    """
    print("--- Running Edit Analyzer Node ---")
    
    ctx = state.get("context", {})
    user_text = state.get("text", "")
    
    if not user_text:
        print("❌ No user text provided for edit analysis")
        ctx["edit_analysis"] = {
            "error": "No user text provided for edit analysis"
        }
        state["context"] = ctx
        return state
    
    try:
        # Get LLM model
        model = state.get("llm_model", "groq-default")
        chat = get_chat_model(model, temperature=0.1)
        
        # Build prompt with existing code context
        user_prompt = _build_edit_analysis_prompt(state)
        
        # Call LLM for analysis
        print("🔍 Analyzing edit request with LLM...")
        result = call_llm_json(chat, SYSTEM_PROMPT, user_prompt) or {}
        
        # Validate and process the result
        edit_analysis = {
            "edit_type": result.get("edit_type", "modify_existing"),
            "target_files": result.get("target_files", []),
            "changes_description": result.get("changes_description", ""),
            "specific_requirements": result.get("specific_requirements", []),
            "preserve_existing": result.get("preserve_existing", True),
            "context_needed": result.get("context_needed", ""),
            "analysis_success": True
        }
        
        # CRITICAL: Store the existing code context for the generator
        existing_code = _capture_existing_code_context(state)
        ctx["existing_code"] = existing_code
        
        # Prepare generator input for editing mode
        gi = ctx.get("generator_input", {})
        gi.update({
            "edit_request": True,
            "user_text": user_text,
            "edit_analysis": edit_analysis,
            "is_edit_mode": True,
            "existing_code": existing_code  # Pass existing code to generator
        })
        
        ctx["edit_analysis"] = edit_analysis
        ctx["generator_input"] = gi
        
        print(f"✅ Edit analysis completed: {edit_analysis['edit_type']}")
        print(f"   Target files: {edit_analysis['target_files']}")
        print(f"   Changes: {edit_analysis['changes_description']}")
        print(f"   Existing code context captured: {len(existing_code.split('```')) // 2} files")
        
    except Exception as e:
        print(f"❌ Error in edit analysis: {e}")
        import traceback
        traceback.print_exc()
        ctx["edit_analysis"] = {
            "error": f"Edit analysis failed: {str(e)}",
            "analysis_success": False
        }
        ctx["generator_input"] = {
            "edit_request": True,
            "user_text": user_text,
            "is_edit_mode": True
        }
    
    state["context"] = ctx
    return state
