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
    
    prompt_parts = [
        "## USER PROMPT - YOUR DESIGN DIRECTION",
        f"{user_text}",
        "",
        "## 🎨 THEME APPLICATION RULES:",
        "**GLOBAL THEME**: When user mentions a theme, apply it to the ENTIRE application",
        "**YOU CHOOSE COLORS**: Decide what colors work best for the requested theme",
        "**THEME CONSISTENCY**: Use consistent colors from the same theme family throughout",
        "**SECTION OVERRIDE**: Only change theme for specific sections if user explicitly requests it",
        "**VISUAL COHESION**: Maintain consistent design by using the same theme palette",
        "",
        "## 🎨 THEME IMPLEMENTATION PROCESS:",
        "1. **User mentions a theme** - interpret what they want",
        "2. **YOU choose appropriate colors** - decide what works best",
        "3. **Apply consistently** - use the same theme across all components",
        "4. **Ensure accessibility** - maintain proper contrast ratios",
        "5. **Maintain visual harmony** - create cohesive design",
        "",
        "**IMPORTANT**: You are the designer - choose colors that make sense for the theme!",
        "",
        "## JSON SCHEMA - COMPONENT STRUCTURE & DATA",
        "**MANDATORY**: You MUST use this schema for component organization and data flow.",
        ""
    ]
    
    if json_schema and isinstance(json_schema, dict):
        schema_str = json.dumps(json_schema, indent=2)
        prompt_parts.append(f"```json\n{schema_str}\n```")
    else:
        prompt_parts.append("No JSON schema provided - use standard component structure.")
    
    prompt_parts.extend([
        "",
        "## 🎨 UI GUIDELINES - DESIGN PRINCIPLES & POLISH",
        "**MANDATORY**: You MUST use the UI guidelines for layout, spacing, typography, and design principles.",
        "",
        "## 🔄 MANDATORY THREE-INPUT SYNTHESIS",
        "**CRITICAL**: You MUST combine ALL THREE inputs together:",
        "1. 🎯 USER PROMPT - Implement specific requirements (themes, colors, features) GLOBALLY",
        "2. 📋 JSON SCHEMA - Use for component structure and data organization",
        "3. 🎨 UI GUIDELINES - Apply for design principles and professional polish",
        "4. 🔄 SYNTHESIS - Combine all three for cohesive, beautiful design",
        "",
        "**THEME IMPLEMENTATION**: Apply user's theme to the ENTIRE application. YOU choose the specific colors!**"
    ])
    
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

def _build_edit_prompt(ctx: Dict[str, Any]) -> str:
    """Build a targeted edit prompt when in editing mode."""
    edit_analysis = ctx.get("edit_analysis", {})
    user_text = ctx.get("user_text", "")
    existing_code = ctx.get("existing_code", "")
    
    if not edit_analysis.get("analysis_success"):
        return ""
    
    edit_prompt = f"""
## EDIT MODE - TARGETED CHANGES REQUIRED

You are in EDIT MODE. The user wants to make specific changes to an existing React application.
DO NOT regenerate the entire application. Make ONLY the requested changes.

### USER EDIT REQUEST:
{user_text}

### EDIT ANALYSIS:
- **Edit Type**: {edit_analysis.get('edit_type', 'modify_existing')}
- **Target Files**: {', '.join(edit_analysis.get('target_files', []))}
- **Changes Description**: {edit_analysis.get('changes_description', '')}
- **Specific Requirements**: {chr(10).join(f"- {req}" for req in edit_analysis.get('specific_requirements', []))}
- **Preserve Existing**: {edit_analysis.get('preserve_existing', True)}
- **Context Needed**: {edit_analysis.get('context_needed', '')}

### 🚨 CRITICAL EDITING INSTRUCTIONS:
1. **DO NOT regenerate the entire application**
2. **Make ONLY the specific changes requested**
3. **Preserve all existing functionality unless explicitly asked to change it**
4. **Focus on the target files identified in the analysis**
5. **Ensure the changes integrate seamlessly with existing code**
6. **Maintain the same code style and structure**

### EXISTING CODE CONTEXT (MODIFY THIS CODE):
{existing_code}

###  OUTPUT FORMAT - EXACT STRUCTURE REQUIRED:
You MUST return ONLY a Python dictionary with this EXACT structure:

```python
{{
    "files_to_correct": [
        {{
            "path": "src/App.jsx",
            "corrected_content": "// COMPLETE modified file content here"
        }},
        {{
            "path": "src/components/Component.jsx",
            "corrected_content": "// COMPLETE modified file content here"
        }}
    ],
    "new_files": [
        {{
            "path": "src/components/NewComponent.jsx",
            "content": "// COMPLETE new file content here"
        }}
    ]
}}
```

### 🔧 IMPORTANT EDITING RULES:
- **MODIFY EXISTING FILES**: Take the existing code above and make ONLY the requested changes
- **PRESERVE STRUCTURE**: Keep the same component structure, imports, and layout
- **TARGETED CHANGES**: Only change what's needed for the requested modifications
- **NO REGENERATION**: Do not create new components unless explicitly requested
- **MAINTAIN FUNCTIONALITY**: Keep all existing features and interactions
- **EXACT FORMAT**: Return ONLY the Python dictionary, no explanations or markdown

### 📝 EXAMPLE:
If user says "add a contact form", you should:
1. Find the existing App.jsx in the code above
2. Add the contact form component import and usage
3. Create a new ContactForm.jsx component
4. Return the modified App.jsx and new ContactForm.jsx in the exact format above

###  CRITICAL:
- Return ONLY the Python dictionary
- No markdown formatting
- No explanations
- No additional text
- Just the dictionary structure

Generate ONLY the corrected file content for the files that need changes.
"""
    
    return edit_prompt


def generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the LLM to generate code or make targeted edits.
    Now handles both initial generation and targeted editing with enhanced validation.
    """
    print("--- Running Generator Node ---")
    ctx = state.get("context", {})
    gi = ctx.get("generator_input", {})
    
    # Check if we're in edit mode
    is_edit_mode = gi.get("is_edit_mode", False)
    
    if is_edit_mode:
        print("🔄 EDIT MODE - Generating targeted changes...")
        
        # CRITICAL: Get existing code context for editing
        existing_code = ctx.get("existing_code", "")
        if not existing_code or existing_code == "No existing code files found" or existing_code.startswith("Error"):
            print("❌ No valid existing code context available for editing")
            print(f"   Context: {existing_code[:100]}...")
            ctx["generation_result"] = {
                "error": f"No valid existing code context available for editing: {existing_code}"
            }
            state["context"] = ctx
            return state
        
        print(f"📁 Using existing code context: {len(existing_code.split('```')) // 2} files")
        
        system_prompt = _load_prompt_template_and_context()
        edit_prompt = _build_edit_prompt(ctx)
        user_prompt = f"{edit_prompt}"
        
        # Use lower temperature for precise edits
        model = state.get("llm_model", "groq-default")
        chat_model = get_chat_model(model, temperature=0.05)
        
        print(f"Calling generator LLM for targeted edits...")
        response = chat_model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        
        # Extract edit data
        edit_data = _extract_correction_data(response.content)
        if edit_data:
            ctx["correction_data"] = edit_data
            ctx["generation_result"] = {
                "e2b_script": response.content,
                "is_correction": True,
                "is_edit": True,
                "edit_attempt": 1
            }
            print("✅ Targeted edit data generated successfully")
        else:
            print("⚠️ Failed to extract edit data, using fallback approach")
            ctx["generation_result"] = {
                "e2b_script": response.content,
                "is_correction": True,
                "is_edit": True,
                "edit_attempt": 1
            }
        
        # CRITICAL: Set state and return immediately for edit mode
        state["context"] = ctx
        return state
    
    # Check if this is a correction attempt
    elif ctx.get("code_analysis", {}).get("correction_needed", False):
        print("🔄 Running generator for targeted code correction...")
        system_prompt = _load_prompt_template_and_context()
        correction_prompt = _build_correction_prompt(ctx)
        user_prompt = f"{_build_generator_user_prompt(gi)}\n\n{correction_prompt}"
        
        # Use lower temperature for corrections
        model = state.get("llm_model", "groq-default")
        chat_model = get_chat_model(model, temperature=0.1)
        
        print(f"Calling generator LLM for code correction...")
        response = chat_model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        
        # Extract correction data
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
        # Initial generation mode
        print("🆕 Running generator for initial code generation...")
        system_prompt = _load_prompt_template_and_context()
        user_prompt = _build_generator_user_prompt(gi)
        
        # Use normal temperature for initial generation
        model = state.get("llm_model", "groq-default")
        chat_model = get_chat_model(model, temperature=0.1)
        
        print(f"Calling generator LLM for initial generation...")
        response = chat_model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        
        ctx["generation_result"] = {
            "e2b_script": response.content,
            "is_correction": False,
            "is_edit": False
        }
        print("✅ Initial code generation completed")
    
    state["context"] = ctx
    return state


def _extract_correction_data(response_content: str) -> Optional[Dict[str, Any]]:
    """Extract correction data from LLM response with enhanced parsing."""
    try:
        print(f"🔍 Extracting correction data from response...")
        print(f"   Response length: {len(response_content)} characters")
        print(f"   Response preview: {response_content[:200]}...")
        
        import re
        import ast
        import json
        
        # Method 1: Find Python dictionary pattern with ```python blocks
        dict_match = re.search(r'```python\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if dict_match:
            dict_str = dict_match.group(1)
            print(f"   ✅ Found Python dictionary in code block")
            try:
                correction_data = ast.literal_eval(dict_str)
                print(f"   ✅ Successfully parsed Python dictionary")
                return correction_data
            except Exception as parse_error:
                print(f"   ❌ Failed to parse Python dictionary: {parse_error}")
        
        # Method 2: Find COMPLETE dictionary structure (ENHANCED)
        # Look for the opening brace and find its matching closing brace
        start_idx = response_content.find('{')
        if start_idx != -1:
            brace_count = 0
            end_idx = start_idx
            
            for i in range(start_idx, len(response_content)):
                char = response_content[i]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count == 0:  # Found complete dictionary
                dict_str = response_content[start_idx:end_idx]
                print(f"   ✅ Found complete dictionary structure ({len(dict_str)} chars)")
                try:
                    correction_data = ast.literal_eval(dict_str)
                    print(f"   ✅ Successfully parsed complete dictionary")
                    return correction_data
                except Exception as parse_error:
                    print(f"   ❌ Failed to parse complete dictionary: {parse_error}")
                    # Try JSON parsing as fallback
                    try:
                        correction_data = json.loads(dict_str)
                        print(f"   ✅ Successfully parsed as JSON")
                        return correction_data
                    except Exception as json_error:
                        print(f"   ❌ JSON parsing also failed: {json_error}")
        
        # Method 3: Manual extraction fallback
        if "files_to_correct" in response_content or "corrected_content" in response_content:
            print(f"   ⚠️ Found edit-related keywords but couldn't extract structured data")
            print(f"   🔧 Attempting manual extraction...")
            
            manual_data = _manual_extract_edit_data(response_content)
            if manual_data:
                print(f"   ✅ Manual extraction successful")
                return manual_data
        
        print(f"   ❌ No structured data found in response")
        return None
        
    except Exception as e:
        print(f"⚠️ Error extracting correction data: {e}")
        import traceback
        traceback.print_exc()
        return None

def _manual_extract_edit_data(response_content: str) -> Optional[Dict[str, Any]]:
    """Manually extract edit data when automatic extraction fails."""
    try:
        print(f"   🔧 Attempting manual extraction...")
        
        # Look for file paths and content patterns
        import re
        
        # Pattern to find file paths and content
        file_pattern = r'(?:src/[^:\s]+\.(?:jsx?|css))'
        files_found = re.findall(file_pattern, response_content)
        
        if files_found:
            print(f"   📁 Found potential files: {files_found}")
            
            # Try to extract content for each file
            files_to_correct = []
            for file_path in set(files_found):
                # Look for content after the file path
                content_pattern = rf'{re.escape(file_path)}[:\s]*\n(.*?)(?=\n(?:src/|$))'
                content_match = re.search(content_pattern, response_content, re.DOTALL)
                
                if content_match:
                    content = content_match.group(1).strip()
                    if len(content) > 10:  # Minimum content length
                        files_to_correct.append({
                            "path": file_path,
                            "corrected_content": content
                        })
                        print(f"   ✅ Extracted content for {file_path}")
            
            if files_to_correct:
                return {
                    "files_to_correct": files_to_correct,
                    "new_files": []
                }
        
        return None
        
    except Exception as e:
        print(f"   ❌ Manual extraction failed: {e}")
        return None