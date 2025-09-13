# nodes/new_design.py
from typing import Dict, Any
import os

def new_design(state: Dict[str, Any]) -> Dict[str, Any]:
    print("--- Running Enhanced New Design Node ---")
    
    ctx = state.get("context") or {}
    intent = ctx.get("intent") or {}
    extraction = ctx.get("extraction") or {}
    
    gi = ctx.get("generator_input") or {}
    gi["user_text"] = state.get("text", "")
    gi["color_palette"] = state.get("color_palette", "")
    
    # Add debug logging for color palette
    color_palette = state.get("color_palette", "")
    print(f" Color Palette received: '{color_palette}'")
    if color_palette and color_palette.strip():
        print(f"✅ Color palette will be used in design generation")
    else:
        print(f"❌ No color palette provided or empty")
    
    # Handle extracted schema
    json_schema = intent.get("json_schema")
    if intent.get("doc_kind") == "json_schema" and isinstance(json_schema, dict):
        gi["schema_source"] = "doc"
        gi["json_schema"] = json_schema
    else:
        gi["schema_source"] = "none"
    
    # CRITICAL: Process logo upload if available
    logo = state.get("logo")
    if logo:
        print("🖼️ Processing uploaded logo...")
        logo_url = _process_uploaded_logo(logo)
        if logo_url:
            gi["uploaded_logo_url"] = logo_url
            gi["has_uploaded_logo"] = True
            print(f"✅ Logo processed successfully: {logo_url}")
        else:
            print("❌ Failed to process uploaded logo")
            gi["has_uploaded_logo"] = False
    else:
        gi["has_uploaded_logo"] = False
    
    # CRITICAL: Process image upload if available
    image = state.get("image")
    if image:
        print("️ Processing uploaded image...")
        image_url = _process_uploaded_image(image)
        if image_url:
            gi["uploaded_image_url"] = image_url
            gi["has_uploaded_image"] = True
            print(f"✅ Image processed successfully: {image_url}")
        else:
            print("❌ Failed to process uploaded image")
            gi["has_uploaded_image"] = False
    else:
        gi["has_uploaded_image"] = False
    
    # CRITICAL: Pass ALL extracted business information to code generator
    # But only if document information is still valid (not cleared)
    if extraction.get("has_business_info") and extraction.get("ok") != False:
        print("🏢 Passing extracted business information to code generator...")
        
        # Business identity
        gi["extracted_business_name"] = extraction.get("business_name")
        gi["extracted_brand_name"] = extraction.get("brand_name")
        
        # Unique value proposition (motive of website)
        gi["extracted_unique_value_proposition"] = extraction.get("unique_value_proposition")
        
        # Design specifications (HIGHEST PRIORITY)
        gi["extracted_color_palette"] = extraction.get("color_palette")
        gi["extracted_font_style"] = extraction.get("preferred_font_style")
        gi["extracted_logo_url"] = extraction.get("logo_url")
        
        # Competitor information
        gi["extracted_competitor_websites"] = extraction.get("competitor_websites", [])
        
        # Set priority flags
        gi["has_extracted_business_info"] = True
        gi["extraction_priority"] = "high"  # Document info takes highest priority
        
        print(f"✅ Business info passed to generator:")
        print(f"   - Business name: {gi['extracted_business_name']}")
        print(f"   - Brand name: {gi['extracted_brand_name']}")
        print(f"   - Value proposition: {gi['extracted_unique_value_proposition'][:50] if gi['extracted_unique_value_proposition'] else 'None'}...")
        print(f"   - Color palette: {gi['extracted_color_palette']}")
        print(f"   - Font style: {gi['extracted_font_style']}")
        print(f"   - Competitors: {len(gi['extracted_competitor_websites'])}")
    else:
        print("📋 No business information available (document removed or not provided)")
        gi["has_extracted_business_info"] = False
        gi["extraction_priority"] = "low"

    # Clear edit history for new design
    state["edit_history"] = None
    state["existing_code"] = None

    ctx["generator_input"] = gi
    state["context"] = ctx
    return state

def _process_uploaded_logo(logo: Dict[str, Any]) -> str:
    """Process uploaded logo and return its URL."""
    try:
        # Get the logo URL from the saved file
        logo_url = logo.get("url")
        if logo_url:
            # Convert to full URL (assuming we have a base URL or use relative)
            # For now, return the relative URL as stored
            return logo_url
        else:
            print("❌ No URL found in logo data")
            return None
    except Exception as e:
        print(f"❌ Error processing logo: {e}")
        return None

def _process_uploaded_image(image: Dict[str, Any]) -> str:
    """Process uploaded image and return its URL."""
    try:
        # Get the image URL from the saved file
        image_url = image.get("url")
        if image_url:
            return image_url
        else:
            print("❌ No URL found in image data")
            return None
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return None

def new_design_route(state: Dict[str, Any]) -> str:
    ctx = state.get("context") or {}
    gi = ctx.get("generator_input") or {}
    if gi.get("schema_source") == "doc" and isinstance(gi.get("json_schema"), dict):
        # When JSON schema is provided, go to photo_generator which will then go to generator
        return "photo_generator"
    return "schema_extraction"     # fallback to schema_extraction (will pick CSV-random)