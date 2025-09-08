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
    generated_images = gi.get("generated_images", [])
    has_images = gi.get("has_images", False)
    
    # Get extracted business information from generator_input (passed from new_design_node)
    has_extracted_business_info = gi.get("has_extracted_business_info", False)
    extraction_priority = gi.get("extraction_priority", "low")
    
    prompt_parts = [
        "## USER PROMPT - YOUR DESIGN DIRECTION",
        f"{user_text}",
        "",
    ]
    
    # HIGHEST PRIORITY: Business information from document
    if has_extracted_business_info and extraction_priority == "high":
        prompt_parts.extend([
            "## 🎨 HIGHEST PRIORITY - BUSINESS INFORMATION FROM DOCUMENT",
            "**CRITICAL**: The user provided a document with business information. This takes ABSOLUTE PRIORITY over all other design sources.",
            "**OVERRIDE ALL**: Use this business information instead of JSON schema colors, UI guidelines, or any other source.",
            "",
        ])
        
        # Business name and brand
        business_name = gi.get("extracted_business_name") or gi.get("extracted_brand_name")
        if business_name:
            prompt_parts.extend([
                f"**BUSINESS/BRAND NAME**: {business_name}",
                "**USAGE**: Use this exact name throughout the website for branding consistency.",
                "",
            ])
        
        # Unique value proposition (motive of website)
        unique_value_proposition = gi.get("extracted_unique_value_proposition")
        if unique_value_proposition:
            prompt_parts.extend([
                f"**UNIQUE VALUE PROPOSITION (MOTIVE OF WEBSITE)**: {unique_value_proposition}",
                "**USAGE**: Highlight this prominently in hero sections, about sections, and key messaging areas.",
                "**IMPORTANCE**: This is the core message and purpose of the website - make it central to the design.",
                "",
            ])
        
        # Color palette from document
        color_palette = gi.get("extracted_color_palette")
        if color_palette:
            prompt_parts.extend([
                f"**DOCUMENT COLOR PALETTE**: {color_palette}",
                "**CRITICAL**: Use these EXACT colors from the document. Override any colors from JSON schema or UI guidelines.",
                "**PRIORITY**: Document colors > User query colors > JSON schema colors > UI guidelines",
                "",
            ])
        
        # Font style from document
        font_style = gi.get("extracted_font_style")
        if font_style:
            prompt_parts.extend([
                f"**DOCUMENT FONT STYLE**: {font_style}",
                "**CRITICAL**: Use this EXACT font style from the document. Override any typography from JSON schema or UI guidelines.",
                "**PRIORITY**: Document fonts > User query fonts > JSON schema fonts > UI guidelines",
                "",
            ])
        
        # Logo URL from document
        logo_url = gi.get("extracted_logo_url")
        if logo_url:
            prompt_parts.extend([
                f"**DOCUMENT LOGO URL**: {logo_url}",
                "**CRITICAL**: Use this EXACT logo from the document. Do not use any generated logos or create text-based logos.",
                "**USAGE**: Use this logo in header, navbar, footer, and all branding areas.",
                "",
            ])
        
        # Competitor websites
        competitor_websites = gi.get("extracted_competitor_websites", [])
        if competitor_websites:
            prompt_parts.extend([
                f"**COMPETITOR WEBSITES**: {', '.join(competitor_websites)}",
                "**USAGE**: Use these as reference to create a BETTER design than competitors.",
                "**GOAL**: Analyze what competitors do and improve upon their weaknesses.",
                "",
            ])
    
    # Add theme application rules (but with business info priority)
    prompt_parts.extend([
        "## 🎨 THEME APPLICATION RULES:",
        "**PRIORITY ORDER**: Document info > User theme > JSON schema > UI guidelines",
        "**GLOBAL THEME**: When user mentions a theme, apply it to the ENTIRE application",
        "**YOU CHOOSE COLORS**: Decide what colors work best for the requested theme (unless document specifies colors)",
        "**THEME CONSISTENCY**: Use consistent colors from the same theme family throughout",
        "**SECTION OVERRIDE**: Only change theme for specific sections if user explicitly requests it",
        "**VISUAL COHESION**: Maintain consistent design by using the same theme palette",
        "",
        "## 🎨 THEME IMPLEMENTATION PROCESS:",
        "1. **Check document colors first** - use document colors if available",
        "2. **User mentions a theme** - interpret what they want",
        "3. **YOU choose appropriate colors** - decide what works best",
        "4. **Apply consistently** - use the same theme across all components",
        "5. **Ensure accessibility** - maintain proper contrast ratios",
        "6. **Maintain visual harmony** - create cohesive design",
        "",
        "**IMPORTANT**: Document business information takes ABSOLUTE PRIORITY over all other design sources!",
        ""
    ])
    
    # Add image information if available
    if has_images and generated_images:
        prompt_parts.extend([
            "## 🖼️ AVAILABLE IMAGES - USE THESE IMAGES IN YOUR CODE",
            "**MANDATORY**: You MUST use these available images in your React components.",
            "**IMAGE INTEGRATION**: Include these images using the provided URLs and alt text.",
            "**CRITICAL**: Use the images provided - do not create placeholder images or skip using them.",
            "",
            "### Available Images:"
        ])
        
        # Group images by category for better organization
        images_by_category = {}
        for img in generated_images:
            category = img.get("category", "unknown")
            if category not in images_by_category:
                images_by_category[category] = []
            images_by_category[category].append(img)
        
        for category, images in images_by_category.items():
            prompt_parts.extend([
                f"#### {category.upper()} IMAGES:",
                ""
            ])
            
            for i, img in enumerate(images, 1):
                prompt_parts.extend([
                    f"**{category.title()} {i}: {img['type']}**",
                    f"- Description: {img['description']}",
                    f"- Website Type: {img.get('website_type', 'general')}",
                    f"- Context: {img['context']}",
                    f"- Primary URL: {img['primary_url']}",
                    f"- Alt Text: {img['alt_text']}",
                ])
                
                # Show all available URLs
                if img.get('urls') and len(img['urls']) > 1:
                    prompt_parts.append("- Additional URLs:")
                    for j, url in enumerate(img['urls'][1:], 2):
                        prompt_parts.append(f"  - URL {j}: {url}")
                
                prompt_parts.append("")
        
        prompt_parts.extend([
            "### Image Usage Instructions by Category:",
            "",
            "#### LOGO IMAGES:",
            "- Use for navbar, header, footer branding elements",
            "- Apply appropriate sizing (typically 150-200px width for navbar, 100-150px for footer)",
            "- Use CSS filters if needed to match theme colors",
            "- Ensure proper contrast with background",
            "- MANDATORY: Use the provided logo URLs, do not create text-based logos",
            "",
            "#### PHOTO IMAGES:",
            "- Use for service cards, product displays, team photos, testimonials",
            "- Apply responsive sizing with proper aspect ratios",
            "- Use CSS object-fit: cover for consistent cropping",
            "- Add subtle shadows or borders for professional look",
            "- MANDATORY: Use the provided photo URLs, do not create placeholder images",
            "",
            "#### ICON IMAGES:",
            "- Use for service icons, feature indicators, UI elements",
            "- Apply consistent sizing (typically 24-48px for small icons, 64-96px for large icons)",
            "- Use CSS filters to match theme colors",
            "- Ensure proper spacing and alignment",
            "- MANDATORY: Use the provided icon URLs, do not create text-based icons",
            "",
            "#### BANNER IMAGES:",
            "- Use for hero sections, background images, promotional banners",
            "- Apply full-width or container-width sizing as appropriate",
            "- Use CSS object-fit: cover for consistent display",
            "- Add overlay effects if needed for text readability",
            "- MANDATORY: Use the provided banner URLs, do not create placeholder backgrounds",
            "",
            "### General Image Guidelines:",
            "- Use the primary URL for the main image display",
            "- Use additional URLs for responsive design or fallbacks",
            "- Include proper alt text for accessibility",
            "- Match images to their intended purpose based on description, website type, and context",
            "- Apply appropriate CSS classes for consistent styling",
            "- Use high-quality images (these are ultra HD images from Pexels API)",
            "- CRITICAL: Always use the provided images - never skip them or create alternatives",
            ""
        ])
    
    # Add logo processing instructions
    prompt_parts.extend([
        "### �� LOGO PROCESSING INSTRUCTIONS:",
        "**CRITICAL FOR LOGO IMAGES**: When using logo images, apply these CSS properties:",
        "",
        "```css",
        "/* Logo styling to remove backgrounds and make them look professional */",
        ".logo {",
        "  background: transparent;",
        "  filter: brightness(1.1) contrast(1.2);",
        "  mix-blend-mode: multiply;",
        "  border-radius: 8px;",
        "  padding: 10px;",
        "  max-width: 200px;",
        "  height: auto;",
        "  object-fit: contain;",
        "}",
        "",
        "/* For navbar logos */",
        ".navbar .logo {",
        "  max-width: 150px;",
        "  height: 50px;",
        "  object-fit: contain;",
        "}",
        "",
        "/* For footer logos */",
        ".footer .logo {",
        "  max-width: 120px;",
        "  height: 40px;",
        "  object-fit: contain;",
        "}",
        "```",
        "",
        "**MANDATORY**: Apply these styles to ALL logo images to make them look professional and remove any background colors.",
        ""
    ])
    
    prompt_parts.extend([
        "## 🚨 COMPREHENSIVE JSON SCHEMA UTILIZATION - EXTRACT EVERYTHING",
        "**CRITICAL**: The JSON schema contains DETAILED design specifications. You MUST extract and use ALL available design information:",
        "",
        "### 📋 JSON SCHEMA - YOUR PRIMARY DESIGN SOURCE",
    ])

    if json_schema and isinstance(json_schema, dict):
        schema_str = json.dumps(json_schema, indent=2)
        prompt_parts.extend([
            "```json",
            schema_str,
            "```",
            "",
            "### 🔍 MANDATORY SCHEMA ANALYSIS - EXTRACT ALL DESIGN DETAILS:",
            "",
            "**1. COLOR SPECIFICATIONS:**",
            "- Extract ALL colors from each component (background, text, accent, etc.)",
            "- Use EXACT color names/values specified (soft beige, dark charcoal, muted rose, etc.)",
            "- Apply colors exactly as defined for each component",
            "- Maintain color consistency across related components",
            "",
            "**2. TYPOGRAPHY SPECIFICATIONS:**",
            "- Extract ALL typography details from each component:",
            "  - Font families (serif, sans-serif, etc.)",
            "  - Font weights (light, regular, medium, etc.)",
            "  - Letter spacing (normal, wide, slight wide, etc.)",
            "  - Text transforms (uppercase, none, etc.)",
            "  - Visual descriptions (Large serif elegant, Small uppercase sans-serif, etc.)",
            "- Apply typography rules exactly as specified for each text element",
            "",
            "**3. SPACING SPECIFICATIONS:**",
            "- Extract ALL spacing rules from each component:",
            "  - Padding values (small vertical, medium, large vertical, etc.)",
            "  - Margin values (none, wide horizontal gutter, etc.)",
            "  - Grid spacing (tight grid spacing, etc.)",
            "- Apply spacing exactly as defined for proper layout",
            "",
            "**4. COMPONENT STRUCTURE & LAYOUT:**",
            "- Follow page_structure order EXACTLY as specified",
            "- Implement each component type as defined (nav, hero, layout, card grid, etc.)",
            "- Use component descriptions for accurate implementation",
            "- Maintain component hierarchy and relationships",
            "",
            "**5. VISUAL STYLING DETAILS:**",
            "- Extract image_style specifications for each component",
            "- Implement other_visual_notes exactly as described",
            "- Apply component-specific styling (rounded corners, shadows, overlays, etc.)",
            "- Use hover effects and interactive elements as specified",
            "",
            "**6. DESIGN THEME & AESTHETIC:**",
            "- Understand overall design aesthetic from component descriptions",
            "- Maintain consistent visual language across all components",
            "- Preserve design intent and professional quality",
            "- Ensure cohesive user experience",
            "",
            "### 🎯 SCHEMA UTILIZATION PRIORITY SYSTEM:",
            "",
            "**WHEN USER SPECIFIES DESIGN PREFERENCES:**",
            "- User preferences OVERRIDE conflicting schema specifications",
            "- Schema provides structure, user provides styling direction",
            "- Example: User says 'dark theme' → override schema colors but keep typography, spacing, layout",
            "",
            "**WHEN USER DOESN'T SPECIFY DESIGN PREFERENCES:**",
            "- Use ALL schema design specifications EXACTLY as provided",
            "- Colors, typography, spacing, visual styles - implement everything",
            "- Schema is your complete design system - use it fully",
            "",
            "### 📐 COMPONENT-SPECIFIC IMPLEMENTATION:",
            "",
            "**FOR EACH COMPONENT IN SCHEMA:**",
            "1. Read component type and description",
            "2. Extract and apply exact color specifications",
            "3. Implement typography rules precisely",
            "4. Apply spacing values as defined",
            "5. Implement image_style requirements",
            "6. Add other_visual_notes styling",
            "7. Ensure component fits page structure order",
            "",
            "### 🎨 DESIGN COMPLETENESS CHECKLIST:",
            "✅ All schema colors implemented exactly",
            "✅ All typography specifications applied",
            "✅ All spacing rules followed precisely",
            "✅ All visual styling notes included",
            "✅ Component structure matches schema",
            "✅ Page order follows schema structure",
            "✅ Image styles implemented as specified",
            "✅ Hover effects and interactions included",
            "✅ Professional quality maintained throughout",
            "",
            "### 🧠 INTELLIGENT DESIGN SYNTHESIS:",
            "",
            "**YOUR ANALYSIS PROCESS:**",
            "1. **EXTRACT EVERYTHING**: Pull ALL design details from schema (colors, fonts, spacing, styles)",
            "2. **ANALYZE USER INTENT**: Identify any user design preferences that should override schema",
            "3. **INTELLIGENT MERGE**: Combine user preferences with non-conflicting schema details",
            "4. **IMPLEMENT COMPLETELY**: Use every available design specification for professional result",
            "",
            "**REMEMBER**: The JSON schema is a COMPLETE design system. Use every detail it provides unless user explicitly requests different styling for specific elements.",
            "",
            "### 🗺️ MANDATORY MAP INTEGRATION FOR CONTACT COMPONENTS:",
            "",
            "**CRITICAL REQUIREMENT**: For ANY contact-related components, ALWAYS include a map:",
            "",
            "**COMPONENTS REQUIRING MAPS:**",
            "- CTA components with contact information",
            "- Contact Us sections", 
            "- Contact forms",
            "- Consultation booking sections",
            "- Any component asking for user contact/location",
            "",
            "**MAP IMPLEMENTATION REQUIREMENTS:**",
            "1. **ALWAYS include a working map** alongside contact forms",
            "2. **Use Google Maps embed** or similar interactive map service", 
            "3. **Position map strategically** - typically beside or below contact form",
            "4. **Use realistic location** - choose any major city location as example",
            "5. **Make map responsive** - ensure it works on all screen sizes",
            "",
            "**MAP CODE EXAMPLE TO USE:**",
            "```jsx",
            "// MANDATORY: Include this type of map in contact components",
            "<div className=\"w-full h-64 md:h-80 rounded-lg overflow-hidden\">",
            "  <iframe",
            "    src=\"https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3022.9663095343008!2d-74.00425878459418!3d40.74844097932681!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89c259bf5c1654f3%3A0xc80f9cfce5383d5d!2sNew%20York%2C%20NY%2C%20USA!5e0!3m2!1sen!2sus!4v1635959472827!5m2!1sen!2sus\"",
            "    width=\"100%\"",
            "    height=\"100%\"",
            "    style={{border: 0}}",
            "    allowFullScreen=\"\"",
            "    loading=\"lazy\"",
            "    referrerPolicy=\"no-referrer-when-downgrade\"",
            "  />",
            "</div>",
            "```",
            "",
            "**MAP STYLING GUIDELINES:**",
            "- Match map container styling to overall component design",
            "- Add subtle shadows or borders consistent with design theme", 
            "- Ensure proper spacing between map and contact form",
            "- Make map visually integrated with component layout",
            "",
            "**LAYOUT OPTIONS FOR MAP + CONTACT FORM:**",
            "- **Side-by-side**: Map on left, form on right (desktop)",
            "- **Stacked**: Form on top, map below (mobile)",
            "- **Split section**: Map as background with overlay form",
            "- **Tabbed interface**: Switch between form and map views",
            "",
            "**MANDATORY**: Never create contact components without including a map!",
            ""
        ])
    else:
        prompt_parts.extend([
            "No JSON schema provided - you will use standard component structure with UI Guidelines.",
            ""
        ])
    
    prompt_parts.extend([
        "",
        "## 🎨 UI GUIDELINES - DESIGN PRINCIPLES & POLISH",
        "**MANDATORY**: You MUST use the UI guidelines for layout, spacing, typography, and design principles.",
        "",
        "## 🔄 MANDATORY INPUT SYNTHESIS",
        "**CRITICAL**: You MUST combine ALL inputs together:",
        "1. 🎯 USER PROMPT - Implement specific requirements (themes, colors, features) GLOBALLY",
        "2. 📋 JSON SCHEMA - Use for component structure and data organization",
        "3. 🎨 UI GUIDELINES - Apply for design principles and professional polish",
        "4. 🖼️ AVAILABLE IMAGES - Use the provided images in your components with proper categorization",
        "5. 🔄 SYNTHESIS - Combine all inputs for cohesive, beautiful design",
        "",
        "**THEME IMPLEMENTATION**: Apply user's theme to the ENTIRE application. YOU choose the specific colors!**"
    ])
    
    return "\n".join(prompt_parts)

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
    
    # Extract file paths from target_files dictionaries
    target_files = edit_analysis.get('target_files', [])
    target_file_paths = [tf.get('file_path', 'Unknown') if isinstance(tf, dict) else str(tf) for tf in target_files]
    
    edit_prompt = f"""
## EDIT MODE - TARGETED CHANGES REQUIRED

You are in EDIT MODE. The user wants to make specific changes to an existing React application.
DO NOT regenerate the entire application. Make ONLY the requested changes.

### USER EDIT REQUEST:
{user_text}

### EDIT ANALYSIS:
- **Edit Type**: {edit_analysis.get('edit_type', 'modify_existing')}
- **Target Files**: {', '.join(target_file_paths)}
- **Changes Description**: {edit_analysis.get('changes_description', '')}
- **Specific Requirements**: {chr(10).join(f"- {req}" for req in edit_analysis.get('specific_requirements', []))}
- **Preserve Existing**: {edit_analysis.get('preserve_existing', True)}
- **Context Needed**: {edit_analysis.get('context_needed', '')}
- **Content Preservation Rules**: {chr(10).join(f"- {rule}" for rule in edit_analysis.get('content_preservation_rules', []))}

### 🚨 CRITICAL EDITING INSTRUCTIONS:

#### FOR THEME/STYLING CHANGES:
- **ONLY modify visual appearance**: colors, backgrounds, borders, shadows, animations, gradients, CSS classes
- **NEVER change text content**: headings, descriptions, button text, form labels, component names, etc.
- **PRESERVE component structure**: same components, same layout, same functionality
- **KEEP all existing content**: text, images, links, form fields, etc.
- **ONLY update className attributes and style properties**

#### FOR FUNCTIONALITY CHANGES:
- **ONLY modify what's specifically requested**: add/remove features as asked
- **PRESERVE existing functionality**: don't break what's already working
- **MAINTAIN component structure**: keep the same layout and organization

#### FOR LAYOUT CHANGES:
- **ONLY modify positioning and spacing**: margins, padding, flexbox, grid
- **PRESERVE content**: same text, same components, same functionality
- **MAINTAIN responsive design**: ensure it still works on all screen sizes

### 🚨 ABSOLUTE RULES:
1. **DO NOT regenerate the entire application**
2. **Make ONLY the specific changes requested**
3. **Preserve all existing functionality unless explicitly asked to change it**
4. **Focus on the target files identified in the analysis**
5. **Ensure the changes integrate seamlessly with existing code**
6. **Maintain the same code style and structure**
7. **NEVER change text content when making theme changes**
8. **ONLY modify styling properties and CSS classes**

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
- **PRESERVE TEXT**: Keep all existing text content unchanged when making theme changes

### 📝 THEME CHANGE EXAMPLE:
If user says "change to cyberpunk theme", you should:
1. Find the existing code above
2. ONLY modify className attributes and style properties
3. Change colors, backgrounds, borders, shadows to cyberpunk style
4. KEEP all existing text content, headings, descriptions, button text
5. PRESERVE all component structure and functionality
6. Return the modified files with ONLY styling changes

###  CRITICAL:
- Return ONLY the Python dictionary
- No markdown formatting
- No explanations
- No additional text
- Just the dictionary structure
- PRESERVE ALL EXISTING TEXT CONTENT

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
            # print(f"   Context: {existing_code[:100]}...")
            ctx["generation_result"] = {
                "error": f"No valid existing code context available for editing: {existing_code}"
            }
            state["context"] = ctx
            return state
        
        # print(f"📁 Using existing code context: {len(existing_code.split('```')) // 2} files")
        
        system_prompt = _load_prompt_template_and_context()
        edit_prompt = _build_edit_prompt(ctx)
        user_prompt = f"{edit_prompt}"
        
        # Use lower temperature for precise edits
        model = state.get("llm_model", "groq-default")
        chat_model = get_chat_model(model, temperature=0.05)
        
        # print(f"Calling generator LLM for targeted edits...")
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
        
        # print(f"Calling generator LLM for code correction...")
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
        
        # print(f"Calling generator LLM for initial generation...")
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
        #   print(f"🔍 Extracting correction data from response...")
        # print(f"   Response length: {len(response_content)} characters")
        # print(f"   Response preview: {response_content[:200]}...")
        
        import re
        import ast
        import json
        
        # Method 1: Find Python dictionary pattern with ```python blocks
        dict_match = re.search(r'```python\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if dict_match:
            dict_str = dict_match.group(1)
            #   print(f"   ✅ Found Python dictionary in code block")
            try:
                correction_data = ast.literal_eval(dict_str)
                #   print(f"   ✅ Successfully parsed Python dictionary")
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
