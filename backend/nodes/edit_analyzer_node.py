# nodes/edit_analyzer.py
from typing import Dict, Any, List
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
  "context_needed": "What existing code context is needed for this edit",
  "image_requirements": [
    {
      "description": "Description of the image needed",
      "category": "logo" | "photo" | "icon" | "banner",
      "context": "Where the image will be used",
      "required": true
    }
  ]
}

Rules:
- "edit_type" should categorize the type of edit being requested
- "target_files" should list the specific files that need modification
- "changes_description" should be a clear summary of the edit request
- "specific_requirements" should list the exact changes needed
- "preserve_existing" should be true if existing functionality should be kept
- "context_needed" should describe what existing code context is required
- "image_requirements" should list any images needed for the edit (empty array if no images needed)
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

def _detect_image_requirements(user_text: str, existing_code: str) -> List[Dict[str, Any]]:
    """
    Detect if the edit request requires images and generate descriptions.
    """
    image_keywords = [
        'image', 'photo', 'picture', 'logo', 'banner', 'icon', 'avatar', 'thumbnail',
        'background', 'hero', 'header image', 'profile picture', 'product image',
        'gallery', 'carousel', 'slider', 'visual', 'graphic', 'illustration'
    ]
    
    user_text_lower = user_text.lower()
    
    # Check if the request mentions images
    has_image_mention = any(keyword in user_text_lower for keyword in image_keywords)
    
    if not has_image_mention:
        return []
    
    # Use LLM to analyze and generate image requirements
    try:
        model = get_chat_model("groq-default", temperature=0.1)
        
        prompt = f"""
Analyze this edit request and determine what images are needed:

USER REQUEST: {user_text}

EXISTING CODE CONTEXT: {existing_code}

If the user wants to add, change, or modify images, provide detailed image requirements.
Output JSON array of image requirements:
[
  {{
    "description": "Detailed description of the image needed",
    "category": "logo|photo|icon|banner",
    "context": "Where/how the image will be used",
    "required": true
  }}
]

If no images are needed, return empty array: []
"""
        
        result = call_llm_json(model, "You are an image requirements analyzer. Output only valid JSON.", prompt)
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "image_requirements" in result:
            return result["image_requirements"]
        else:
            return []
            
    except Exception as e:
        print(f"❌ Error detecting image requirements: {e}")
        return []

def _generate_images_for_edit(image_requirements: List[Dict[str, Any]], state: GraphState) -> List[Dict[str, Any]]:
    """
    Generate images for edit requirements using photo generator functions.
    """
    if not image_requirements:
        return []
    
    print(f"🖼️ Generating {len(image_requirements)} images for edit request...")
    
    try:
        # Import photo generator functions
        from nodes.photo_generator_node import (
            _generate_high_quality_images_from_pexels,
            _save_image_to_csv,
            _infer_category_from_description
        )
        
        generated_images = []
        
        for req in image_requirements:
            description = req.get("description", "")
            category = req.get("category", "photo")
            context = req.get("context", "")
            
            if not description:
                continue
            
            print(f"   Generating: {description} ({category})")
            
            # Generate images using the photo generator
            urls = _generate_high_quality_images_from_pexels(
                description=description,
                context=context,
                category=category,
                max_images=1
            )
            
            if urls:
                # Save to CSV
                website_type = state.get("context", {}).get("website_type", "general")
                _save_image_to_csv(description, website_type, context, category, urls)
                
                # Add to generated images list
                generated_images.append({
                    "description": description,
                    "category": category,
                    "context": context,
                    "urls": urls,
                    "generated_for_edit": True
                })
                
                print(f"   ✅ Generated: {description}")
            else:
                print(f"   ❌ Failed to generate: {description}")
        
        print(f"✅ Generated {len(generated_images)} images for edit")
        return generated_images
        
    except Exception as e:
        print(f"❌ Error generating images for edit: {e}")
        import traceback
        traceback.print_exc()
        return []

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
        
        # NEW: Check for image requirements and generate images if needed
        image_requirements = result.get("image_requirements", [])
        if not image_requirements:
            # Fallback: detect image requirements from user text
            image_requirements = _detect_image_requirements(user_text, existing_code)
        
        generated_images = []
        if image_requirements:
            print(f"🖼️ Detected {len(image_requirements)} image requirements")
            generated_images = _generate_images_for_edit(image_requirements, state)
            edit_analysis["image_requirements"] = image_requirements
            edit_analysis["generated_images"] = generated_images
        
        # Prepare generator input for editing mode
        gi = ctx.get("generator_input", {})
        gi.update({
            "edit_request": True,
            "user_text": user_text,
            "edit_analysis": edit_analysis,
            "is_edit_mode": True,
            "existing_code": existing_code,  # Pass existing code to generator
            "generated_images": generated_images  # Pass generated images to generator
        })
        
        ctx["edit_analysis"] = edit_analysis
        ctx["generator_input"] = gi
        
        print(f"✅ Edit analysis completed: {edit_analysis['edit_type']}")
        print(f"   Target files: {edit_analysis['target_files']}")
        print(f"   Changes: {edit_analysis['changes_description']}")
        print(f"   Existing code context captured: {len(existing_code.split('```')) // 2} files")
        if generated_images:
            print(f"   Generated {len(generated_images)} images for edit")
        
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
