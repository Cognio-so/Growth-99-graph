# nodes/edit_analyzer.py
from typing import Dict, Any, List
from graph_types import GraphState
from llm import get_chat_model, call_llm_json

ENHANCED_SYSTEM_PROMPT = """You are an advanced edit analyzer for a React application. 
Analyze the user's edit request and determine what changes need to be made with special attention to theme changes and image handling.

🚨 CRITICAL THEME ANALYSIS RULES:
1. **GLOBAL THEME CHANGES**: When user mentions themes (gradient, dark/light, cyberpunk, etc.), analyze as WHOLE UI changes
2. **SCOPE DETECTION**: Determine if changes should apply to entire application or specific sections
3. **IMAGE PROTECTION**: Identify existing images that need protection from theme overlays
4. **COMPONENT COVERAGE**: Ensure theme changes cover ALL components, not just specific sections

Analyze the user's request and output strict JSON:
{
  "edit_type": "modify_styling" | "add_theme_toggle" | "modify_existing" | "add_new_component" | "modify_functionality" | "modify_layout",
  "scope": "global" | "section_specific" | "component_specific",
  "target_files": ["src/App.jsx", "src/components/Component.jsx"],
  "changes_description": "Detailed description of what needs to be changed",
  "specific_requirements": [
    "Apply gradient theme to entire application",
    "Add dark/light theme toggle with global state management", 
    "Protect existing images from theme color overlays",
    "Ensure theme consistency across all components"
  ],
  "theme_analysis": {
    "is_theme_change": boolean,
    "theme_type": "gradient" | "dark_light_toggle" | "color_scheme" | "none",
    "affects_whole_ui": boolean,
    "image_protection_needed": boolean,
    "requires_state_management": boolean
  },
  "preserve_existing": boolean,
  "context_needed": "What existing code context is needed for this edit",
  "content_preservation_rules": [
    "Preserve all text content and functionality",
    "Protect images from theme color overlays",
    "Maintain existing component structure",
    "Keep all interactive elements functional"
  ],
  "image_requirements": [
    {
      "description": "Description of the image needed",
      "category": "logo" | "photo" | "icon" | "banner",
      "context": "Where the image will be used",
      "required": true
    }
  ]
}

🚨 ENHANCED ANALYSIS RULES:
1. **THEME SCOPE**: If user mentions themes without specifying sections, assume GLOBAL application changes
2. **DARK/LIGHT TOGGLE**: When user wants theme toggle, analyze need for state management and global application
3. **IMAGE SAFETY**: Always identify existing images that need protection from theme colors
4. **COMPONENT COVERAGE**: Ensure all UI components are included in theme changes
5. **CONSISTENCY**: Theme changes should create visual consistency across the entire application

SPECIAL THEME DETECTION:
- "gradient theme" → Global styling change with image protection
- "dark/light theme" → Global toggle with state management
- "add theme toggle" → New functionality affecting entire UI
- Color mentions without section → Global color scheme changes
"""

def _capture_existing_code_context(state: GraphState) -> str:
    """Capture the existing code context from the current sandbox."""
    try:
        # Import here to avoid circular imports
        from nodes.apply_to_Sandbox_node import _global_sandbox
        
        if not _global_sandbox:
            print("❌ No global sandbox available for context capture")
            return "No existing sandbox available"
        
        print("📁 Capturing existing code context for edit analysis...")
        
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

def _build_enhanced_edit_analysis_prompt(state: GraphState) -> str:
    """Build the enhanced prompt for analyzing edit requests with better theme and image handling."""
    text = state.get("text", "")
    ctx = state.get("context", {})
    extraction = ctx.get("extraction", {})
    doc = state.get("doc")
    
    # CRITICAL: Capture the existing code context
    existing_code = _capture_existing_code_context(state)
    
    # Check if document information is available
    has_document_info = doc and extraction.get("has_business_info")
    
    prompt = f"""
## USER EDIT REQUEST:
{text}

## EXISTING CODE CONTEXT (CURRENT UI DESIGN):
{existing_code}

## 🎨 ENHANCED THEME ANALYSIS INSTRUCTIONS:

### THEME SCOPE DETECTION:
- **GLOBAL THEMES**: If user mentions themes without specifying sections (e.g., "apply gradient theme", "add dark/light theme"), treat as WHOLE APPLICATION changes
- **SECTION SPECIFIC**: Only if user explicitly mentions specific sections (e.g., "change header to dark theme")
- **DEFAULT ASSUMPTION**: Unless specified otherwise, theme changes affect the ENTIRE UI

### IMAGE PROTECTION ANALYSIS:
- **IDENTIFY EXISTING IMAGES**: Look for img tags, background images, icons in the existing code
- **OVERLAY PROTECTION**: Determine if theme changes might make images invisible or unclear
- **BACKGROUND SAFETY**: Ensure background colors don't conflict with image visibility

### THEME TOGGLE REQUIREMENTS:
- **STATE MANAGEMENT**: If user wants dark/light toggle, analyze need for React state or context
- **GLOBAL APPLICATION**: Theme toggles should affect ALL components, not just headers or sections
- **PERSISTENCE**: Consider if theme preference should persist across page reloads

### COMPONENT COVERAGE:
- **ALL COMPONENTS**: Theme changes should cover App.jsx and ALL component files
- **CONSISTENCY**: Ensure visual consistency across the entire application
- **RESPONSIVE**: Theme changes should work across all screen sizes
"""

    # Add document information if available
    if has_document_info:
        prompt += f"""

## DOCUMENT EXTRACTION INFORMATION (APPLY TO EXISTING DESIGN):
- Business Name: {extraction.get('business_name', 'Not specified')}
- Brand Name: {extraction.get('brand_name', 'Not specified')}
- Unique Value Proposition: {extraction.get('unique_value_proposition', 'Not specified')}
- Color Palette: {extraction.get('color_palette', 'Not specified')}
- Preferred Font Style: {extraction.get('preferred_font_style', 'Not specified')}
- Logo URL: {extraction.get('logo_url', 'Not specified')}

IMPORTANT: The user wants to apply these document specifications to the existing design.
Use the document information as the PRIMARY source for design decisions.
"""

    prompt += f"""

## ANALYSIS TASK:
Analyze this edit request with ENHANCED FOCUS on:
1. **Theme Scope**: Is this a global theme change or section-specific?
2. **Image Protection**: Do existing images need protection from theme overlays?
3. **Component Coverage**: Which files need modification to ensure consistent theming?
4. **State Management**: Does this require React state for theme toggles?
5. **User Intent**: What is the user's expectation for the scope of changes?

## 🚨 CRITICAL ANALYSIS PRIORITIES:
1. **ASSUME GLOBAL SCOPE**: Unless user specifies sections, assume whole-application changes
2. **PROTECT IMAGES**: Always consider image visibility when applying themes
3. **FULL COVERAGE**: Ensure theme changes cover ALL components for consistency
4. **FUNCTIONALITY**: Preserve all existing functionality while applying themes

IMPORTANT: The user wants to modify the EXISTING UI shown above, not create a new one.
Focus on what specific changes need to be made to the current design with ENHANCED theme and image handling.

Provide your analysis in the required JSON format with the enhanced theme_analysis section.
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
    ENHANCED edit analyzer with better theme and image handling.
    Analyze user edit requests to determine what changes need to be made.
    Enhanced to include document extraction information when document is provided.
    """
    print("--- Running ENHANCED Edit Analyzer Node ---")
    
    ctx = state.get("context", {})
    user_text = state.get("text", "")
    doc = state.get("doc")  # Check if document is provided for editing
    logo = state.get("logo")  # Check if logo is provided for editing
    image = state.get("image")  # Check if image is provided for editing
    
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
        
        # Build ENHANCED prompt with existing code context
        user_prompt = _build_enhanced_edit_analysis_prompt(state)
        
        # ENHANCED: Include document extraction information if available
        extraction = ctx.get("extraction", {})
        has_document_info = doc and extraction.get("has_business_info")
        
        if has_document_info:
            print("📄 Document provided for editing - including extracted business information")
            user_prompt += f"\n\nDocument Business Information:\n"
            user_prompt += f"- Business Name: {extraction.get('business_name', 'Not specified')}\n"
            user_prompt += f"- Brand Name: {extraction.get('brand_name', 'Not specified')}\n"
            user_prompt += f"- Value Proposition: {extraction.get('unique_value_proposition', 'Not specified')}\n"
            user_prompt += f"- Color Palette: {extraction.get('color_palette', 'Not specified')}\n"
            user_prompt += f"- Font Style: {extraction.get('preferred_font_style', 'Not specified')}\n"
            user_prompt += f"- Logo URL: {extraction.get('logo_url', 'Not specified')}\n"
        
        # CRITICAL: Process logo upload if available for editing
        if logo:
            print("🖼️ Processing uploaded logo for edit...")
            logo_url = _process_uploaded_logo_for_edit(logo)
            if logo_url:
                user_prompt += f"\n\nUploaded Logo Information:\n"
                user_prompt += f"- Logo URL: {logo_url}\n"
                user_prompt += f"- Logo Filename: {logo.get('filename', 'logo')}\n"
                user_prompt += f"- IMPORTANT: Use this uploaded logo in the design. Replace any existing logo or add it if no logo exists.\n"
                print(f"✅ Logo processed for edit: {logo_url}")
            else:
                print("❌ Failed to process uploaded logo for edit")
        
        # Call LLM for ENHANCED analysis
        print("🔍 Analyzing edit request with ENHANCED LLM analysis...")
        result = call_llm_json(chat, ENHANCED_SYSTEM_PROMPT, user_prompt) or {}
        
        # Validate and process the result with ENHANCED fields
        edit_analysis = {
            "edit_type": result.get("edit_type", "modify_existing"),
            "scope": result.get("scope", "global"),  # NEW: scope detection
            "target_files": result.get("target_files", []),
            "changes_description": result.get("changes_description", ""),
            "specific_requirements": result.get("specific_requirements", []),
            "theme_analysis": result.get("theme_analysis", {  # NEW: theme analysis
                "is_theme_change": False,
                "theme_type": "none",
                "affects_whole_ui": False,
                "image_protection_needed": False,
                "requires_state_management": False
            }),
            "preserve_existing": result.get("preserve_existing", True),
            "context_needed": result.get("context_needed", ""),
            "content_preservation_rules": result.get("content_preservation_rules", [  # NEW: preservation rules
                "Preserve all text content and functionality",
                "Protect images from theme color overlays",
                "Maintain existing component structure",
                "Keep all interactive elements functional"
            ]),
            "analysis_success": True,
            "has_document_info": has_document_info  # Flag to indicate document info is available
        }
        
        # CRITICAL: Store the existing code context for the generator
        existing_code = _capture_existing_code_context(state)
        ctx["existing_code"] = existing_code
        
        # SMART IMAGE HANDLING: Only generate images if user hasn't uploaded one
        image_requirements = result.get("image_requirements", [])
        if not image_requirements:
            # Fallback: detect image requirements from user text
            image_requirements = _detect_image_requirements(user_text, existing_code)
        
        generated_images = []
        # Only generate images if user hasn't uploaded an image but needs images
        if image_requirements and not image:
            print(f"🖼️ No uploaded image detected, generating {len(image_requirements)} images for edit request")
            generated_images = _generate_images_for_edit(image_requirements, state)
            edit_analysis["image_requirements"] = image_requirements
            edit_analysis["generated_images"] = generated_images
        elif image_requirements and image:
            print(f"🖼️ User has uploaded image, using uploaded image instead of generating new ones")
            edit_analysis["image_requirements"] = image_requirements
            edit_analysis["generated_images"] = []  # No generated images needed
        elif not image_requirements:
            print(f"🖼️ No image requirements detected in edit request")
        
        # ENHANCED: Prepare generator input for editing mode with document information
        gi = ctx.get("generator_input", {})
        gi.update({
            "edit_request": True,
            "user_text": user_text,
            "edit_analysis": edit_analysis,
            "is_edit_mode": True,
            "existing_code": existing_code,  # Pass existing code to generator
            "generated_images": generated_images  # Pass generated images to generator
        })
        
        # CRITICAL: Include uploaded logo in generator input for editing
        if logo:
            logo_url = _process_uploaded_logo_for_edit(logo)
            if logo_url:
                gi.update({
                    "uploaded_logo_url": logo_url,
                    "has_uploaded_logo": True,
                    "logo_filename": logo.get("filename", "logo")
                })
                print(f"✅ Logo included in edit generator input: {logo_url}")
            else:
                gi["has_uploaded_logo"] = False
        
        # CRITICAL: Include uploaded image in generator input for editing
        if image:
            image_url = _process_uploaded_image_for_edit(image)
            if image_url:
                gi.update({
                    "uploaded_image_url": image_url,
                    "has_uploaded_image": True,
                    "image_filename": image.get("filename", "image")
                })
                print(f"✅ Image included in edit generator input: {image_url}")
            else:
                gi["has_uploaded_image"] = False
        else:
            gi["has_uploaded_image"] = False
        
        # ENHANCED: Include document extraction information in generator input
        if has_document_info:
            print("📋 Including document business information in edit request")
            gi.update({
                "extracted_business_name": extraction.get("business_name"),
                "extracted_brand_name": extraction.get("brand_name"),
                "extracted_unique_value_proposition": extraction.get("unique_value_proposition"),
                "extracted_color_palette": extraction.get("color_palette"),
                "extracted_font_style": extraction.get("preferred_font_style"),
                "extracted_logo_url": extraction.get("logo_url"),
                "has_extracted_business_info": True,
                "extraction_priority": "high"  # Document info takes highest priority for edits
            })
            print(f"✅ Document info included in edit:")
            print(f"   - Business: {extraction.get('business_name')}")
            print(f"   - Colors: {extraction.get('color_palette')}")
            print(f"   - Font: {extraction.get('preferred_font_style')}")
        else:
            gi["has_extracted_business_info"] = False
            gi["extraction_priority"] = "low"
        
        # CRITICAL: Add color palette to generator input for edit mode
        color_palette = state.get("color_palette", "")
        gi["color_palette"] = color_palette
        
        # Add debug logging for color palette in edit mode
        print(f"🎨 Edit Analyzer - Color Palette: '{color_palette}'")
        if color_palette and color_palette.strip():
            print(f"✅ Color palette will be used in edit generation")
        else:
            print(f"❌ No color palette provided for edit")
        
        ctx["edit_analysis"] = edit_analysis
        ctx["generator_input"] = gi
        
        # ENHANCED logging
        theme_analysis = edit_analysis.get("theme_analysis", {})
        print(f"✅ ENHANCED Edit analysis completed: {edit_analysis['edit_type']}")
        print(f"   Scope: {edit_analysis['scope']}")
        print(f"   Target files: {edit_analysis['target_files']}")
        print(f"   Changes: {edit_analysis['changes_description']}")
        print(f"   Theme change: {theme_analysis.get('is_theme_change', False)}")
        if theme_analysis.get('is_theme_change'):
            print(f"   Theme type: {theme_analysis.get('theme_type', 'none')}")
            print(f"   Affects whole UI: {theme_analysis.get('affects_whole_ui', False)}")
            print(f"   Image protection needed: {theme_analysis.get('image_protection_needed', False)}")
        print(f"   Existing code context captured: {len(existing_code.split('```')) // 2} files")
        if generated_images:
            print(f"   Generated {len(generated_images)} images for edit")
        if has_document_info:
            print(f"   Document business information included for editing")
        
    except Exception as e:
        print(f"❌ Error in ENHANCED edit analysis: {e}")
        import traceback
        traceback.print_exc()
        ctx["edit_analysis"] = {
            "error": f"Enhanced edit analysis failed: {str(e)}",
            "analysis_success": False
        }
        ctx["generator_input"] = {
            "edit_request": True,
            "user_text": user_text,
            "is_edit_mode": True
        }
    
    state["context"] = ctx
    return state

def _process_uploaded_logo_for_edit(logo: Dict[str, Any]) -> str:
    """Process uploaded logo for edit mode and return its URL."""
    try:
        # Get the logo URL from the saved file
        logo_url = logo.get("url")
        if logo_url:
            # Convert to full URL (assuming we have a base URL or use relative)
            # For now, return the relative URL as stored
            return logo_url
        else:
            print("❌ No URL found in logo data for edit")
            return None
    except Exception as e:
        print(f"❌ Error processing logo for edit: {e}")
        return None

def _process_uploaded_image_for_edit(image: Dict[str, Any]) -> str:
    """Process uploaded image for edit mode and return its URL."""
    try:
        # Get the image URL from the saved file
        image_url = image.get("url")
        if image_url:
            # Convert to full URL (assuming we have a base URL or use relative)
            # For now, return the relative URL as stored
            return image_url
        else:
            print("❌ No URL found in image data for edit")
            return None
    except Exception as e:
        print(f"❌ Error processing image for edit: {e}")
        return None