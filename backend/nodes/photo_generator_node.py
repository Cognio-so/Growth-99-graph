# nodes/photo_generator_node.py
import json
import os
import csv
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path
from llm import get_chat_model
import re
# Pexels API configuration
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "YOUR_PEXELS_API_KEY_HERE")
PEXELS_BASE_URL = "https://api.pexels.com/v1"

# CSV file for storing images
IMAGES_CSV_PATH = Path(__file__).parent.parent / "generated_images.csv"

def photo_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate images using intelligent LLM analysis, CSV storage, and Pexels API.
    Now includes uploaded logos with highest priority.
    """
    print("--- Running Photo Generator Node ---")
    
    ctx = state.get("context", {})
    gi = ctx.get("generator_input", {})
    user_text = gi.get("user_text", "")
    json_schema = gi.get("json_schema", {})
    
    # Step 1: Use LLM to analyze what images are needed with detailed descriptions
    image_requirements = _analyze_image_requirements_with_llm(user_text, json_schema, state)
    
    # Step 2: Check existing images in CSV and determine what needs to be generated
    needed_images = _intelligent_check_existing_images(image_requirements, state)
    
    # Step 3: Generate new images only for those that are needed
    if needed_images:
        print(f"🔄 Need to generate {len(needed_images)} new images")
        _generate_and_save_new_images(needed_images)
    else:
        print("✅ All required images already exist in database")
    
    # Step 4: Load all relevant images from CSV for code generation
    final_images = _load_relevant_images_from_csv(image_requirements, state)
    
    # Step 5: Add uploaded logo to images with highest priority
    final_images = _add_uploaded_logo_to_images(gi, final_images)
    
    # Step 6: Add uploaded image to images with high priority
    final_images = _add_uploaded_image_to_images(gi, final_images)
    
    # Step 7: Store the images in the context
    gi["generated_images"] = final_images
    gi["has_images"] = len(final_images) > 0
    
    ctx["generator_input"] = gi
    state["context"] = ctx
    
    print(f"🖼️ Final result: {len(final_images)} images available for code generation")
    if gi.get("has_uploaded_logo"):
        print("   ✅ Uploaded logo included with highest priority")
    
    return state

def _analyze_image_requirements_with_llm(user_text: str, json_schema: dict, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Use LLM to analyze user text and JSON schema to determine what images are needed with detailed descriptions.
    Completely removes logo generation - only uses logos from user documents.
    """
    # print("🤖 Using LLM to analyze image requirements...") 
    
    # Prepare the analysis prompt
    analysis_prompt = f"""
You are an expert UI/UX designer analyzing a user request and JSON schema to determine what images are needed for a web application.

USER REQUEST: "{user_text}"

JSON SCHEMA: {json.dumps(json_schema, indent=2) if json_schema else "No schema provided"}

CRITICAL: DO NOT generate any logo requirements. Logos should only come from user-provided documents.

Your task is to identify what images are needed for this application. For each image needed, provide:
1. A detailed, specific description (5-10 words) that clearly identifies the image type and context
2. The website/application type this is for
3. The specific purpose/context of the image
4. Image category (photo, icon, banner) - NO LOGO CATEGORY
5. Priority (high/medium/low)

CRITICAL IMAGE CATEGORIES (NO LOGOS):
- **PHOTO**: Real photos of people, places, products, services
- **ICON**: Simple line icons, symbols, UI elements
- **BANNER**: Hero images, background photos, promotional graphics

IMPORTANT: Make descriptions very specific and detailed so they can be reused for similar projects.

Examples of good descriptions:
- PHOTO: "dental hospital service card photo for healthcare website"
- ICON: "medical service line icon for treatment cards"
- BANNER: "restaurant interior hero banner for food website"

Focus on:
- User avatars/profile pictures (PHOTO)
- Product/service images (PHOTO)
- Hero/banner images (BANNER)
- Service cards/feature images (PHOTO)
- Background images (BANNER)
- Team photos (PHOTO)
- Equipment/facility photos (PHOTO)
- UI icons (ICON)

DO NOT include any logo requirements. Logos are handled separately from user documents.

Return your analysis as a JSON array with this structure:
[
    {{
        "description": "dental service card photo for healthcare website",
        "website_type": "healthcare/hospital website", 
        "context": "service card display",
        "category": "photo",
        "priority": "high"
    }},
    {{
        "description": "medical equipment display photo for healthcare website",
        "website_type": "healthcare/hospital website",
        "context": "equipment showcase",
        "category": "photo",
        "priority": "medium"
    }}
]

Be very specific and detailed in descriptions. Only include images that are actually needed based on the user request and schema.
DO NOT include any logo requirements.
"""
    
    try:
        model = get_chat_model(state.get("llm_model"))
        # print(f"model--- {model}")    
        response = model.invoke(analysis_prompt)
        
        # Extract JSON from response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Try to find JSON in the response
        
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            image_requirements = json.loads(json_str)
            
            # ENHANCED: Filter out any logo requirements that might slip through
            original_count = len(image_requirements)
            image_requirements = [req for req in image_requirements if req.get("category") != "logo"]
            filtered_count = original_count - len(image_requirements)
            if filtered_count > 0:
                print(f"🚫 Filtered out {filtered_count} logo requirements (logos not generated)")
            
            # print(f"✅ LLM identified {len(image_requirements)} detailed image requirements")
            return image_requirements
        else:
            # print("⚠️ Could not parse LLM response as JSON, using fallback analysis")
            return _fallback_detailed_analysis(user_text, json_schema, state)
            
    except Exception as e:
        # print(f"❌ LLM analysis failed: {e}, using fallback analysis")
        return _fallback_detailed_analysis(user_text, json_schema, state)

def _fallback_detailed_analysis(user_text: str, json_schema: dict, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fallback detailed image analysis when LLM fails.
    Completely removes logo generation - only uses logos from user documents.
    """
    image_requirements = []
    user_text_lower = user_text.lower()
    
    # Determine website type
    website_type = "general website"
    if any(word in user_text_lower for word in ["hospital", "medical", "health", "clinic", "dental"]):
        website_type = "healthcare/hospital website"
    elif any(word in user_text_lower for word in ["restaurant", "food", "menu", "dining"]):
        website_type = "restaurant/food website"
    elif any(word in user_text_lower for word in ["shop", "store", "product", "ecommerce", "buy"]):
        website_type = "e-commerce/shopping website"
    elif any(word in user_text_lower for word in ["business", "corporate", "company"]):
        website_type = "business/corporate website"
    elif any(word in user_text_lower for word in ["real estate", "property", "house", "apartment"]):
        website_type = "real estate website"
    
    # Check for common image types with detailed descriptions (NO LOGOS)
    if any(word in user_text_lower for word in ["avatar", "profile", "user"]):
        image_requirements.append({
            "description": f"user profile avatar photo for {website_type}",
            "website_type": website_type,
            "context": "user profile display",
            "category": "photo",
            "priority": "high"
        })
    
    if any(word in user_text_lower for word in ["service", "card", "feature"]):
        if "health" in website_type or "medical" in website_type:
            image_requirements.append({
                "description": f"medical service card photo for {website_type}",
                "website_type": website_type,
                "context": "service card display",
                "category": "photo",
                "priority": "high"
            })
        elif "restaurant" in website_type:
            image_requirements.append({
                "description": f"restaurant service card photo for {website_type}",
                "website_type": website_type,
                "context": "service card display",
                "category": "photo",
                "priority": "high"
            })
        else:
            image_requirements.append({
                "description": f"service card photo for {website_type}",
                "website_type": website_type,
                "context": "service card display",
                "category": "photo",
                "priority": "high"
            })
    
    if any(word in user_text_lower for word in ["product", "item", "goods"]):
        image_requirements.append({
            "description": f"product showcase photo for {website_type}",
            "website_type": website_type,
            "context": "product display",
            "category": "photo",
            "priority": "high"
        })
    
    # REMOVED: Logo generation completely removed
    # No logo requirements will be added regardless of user input
    
    if any(word in user_text_lower for word in ["banner", "hero", "header"]):
        image_requirements.append({
            "description": f"hero banner photo for {website_type}",
            "website_type": website_type,
            "context": "main banner section",
            "category": "banner",
            "priority": "medium"
        })
    
    # If no specific requirements found, add defaults based on website type (NO LOGOS)
    if not image_requirements:
        if "healthcare" in website_type:
            image_requirements = [
                {
                    "description": "medical service card photo for healthcare website",
                    "website_type": website_type,
                    "context": "service card display",
                    "category": "photo",
                    "priority": "high"
                },
                {
                    "description": "medical equipment display photo for healthcare website",
                    "website_type": website_type,
                    "context": "equipment showcase",
                    "category": "photo",
                    "priority": "medium"
                }
            ]
            # REMOVED: No logo added even for healthcare websites
        elif "restaurant" in website_type:
            image_requirements = [
                {
                    "description": "restaurant food service photo for restaurant website",
                    "website_type": website_type,
                    "context": "service card display",
                    "category": "photo",
                    "priority": "high"
                },
                {
                    "description": "restaurant interior photo for restaurant website",
                    "website_type": website_type,
                    "context": "interior showcase",
                    "category": "photo",
                    "priority": "medium"
                }
            ]
            # REMOVED: No logo added even for restaurant websites
        else:
            image_requirements = [
                {
                    "description": f"service card photo for {website_type}",
                    "website_type": website_type,
                    "context": "service card display",
                    "category": "photo",
                    "priority": "high"
                }
            ]
            # REMOVED: No logo added for general websites
    
    print(f"🚫 Logo generation completely disabled - only using document-provided logos")
    return image_requirements

def _intelligent_check_existing_images(image_requirements: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Intelligently check existing images in CSV and determine what new images need to be generated.
    """
   
    
    # Load existing images from CSV
    existing_images = _load_images_from_csv()
    
    if not existing_images:
       
        return image_requirements
    
    # Batch process all requirements in a single LLM call
    needed_images = _batch_check_existing_images(image_requirements, existing_images, state)
    
    return needed_images

def _batch_check_existing_images(image_requirements: List[Dict[str, Any]], existing_images: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Batch check all image requirements against existing images in a single LLM call.
    Balanced approach - reuse good images but avoid exact duplicates.
    """
    # Prepare existing images data for LLM
    existing_data = []
    for img in existing_images:
        existing_data.append({
            "description": img["description"],
            "website_type": img.get("website_type", "unknown"),
            "context": img["context"],
            "category": img.get("category", "unknown"),
            "url_count": len([url for url in [img.get("url1"), img.get("url2")] if url])
        })
    
    # Prepare requirements data for LLM
    requirements_data = []
    for req in image_requirements:
        requirements_data.append({
            "description": req["description"],
            "website_type": req["website_type"],
            "context": req["context"],
            "category": req["category"]
        })
    
    batch_prompt = f"""
You are analyzing whether we have suitable existing images for multiple image requirements.

NEEDED IMAGES:
{json.dumps(requirements_data, indent=2)}

EXISTING IMAGES IN DATABASE:
{json.dumps(existing_data, indent=2)}

Your task is to determine which needed images have suitable existing images in the database.

Consider images suitable if they are GOOD matches:
1. They serve the same or SIMILAR purpose (same or similar context)
2. They are for the same or similar website type
3. They have the SAME category (logo, photo, icon, banner)
4. They have at least 1 URL available
5. The description is conceptually similar or related

CRITICAL: Category must match exactly:
- LOGO images can only match other LOGO images
- PHOTO images can only match other PHOTO images
- ICON images can only match other ICON images
- BANNER images can only match other BANNER images

IMPORTANT: Be REASONABLE with matching. Reuse good existing images to save time, but avoid exact duplicates.

Examples of suitable matches (be reasonable):
- "dental hospital service card" (PHOTO) matches "medical service card photo" (PHOTO) - SIMILAR PURPOSE
- "company logo design" (LOGO) matches "business logo design" (LOGO) - SIMILAR PURPOSE
- "medspa logo" (LOGO) matches "beauty logo" (LOGO) - SIMILAR INDUSTRY
- "facial treatment photo" (PHOTO) matches "spa treatment photo" (PHOTO) - SIMILAR SERVICE
- "hero banner photo" (BANNER) matches "background banner photo" (BANNER) - SIMILAR USE

Examples of NOT suitable (avoid these):
- "dental hospital service card" (PHOTO) does NOT match "restaurant food photo" (PHOTO) - DIFFERENT INDUSTRY
- "company logo design" (LOGO) does NOT match "product photo" (PHOTO) - DIFFERENT CATEGORY
- "navbar logo" (LOGO) does NOT match "footer logo" (LOGO) - DIFFERENT CONTEXT (unless very similar)

BALANCE: Reuse existing images when they serve a similar purpose, but generate new ones when you need variety or specific requirements.

Return a JSON object where keys are the needed image descriptions and values are "YES" if suitable existing images are found, or "NO" if new images need to be generated.

Example:
{{
    "company logo design for navbar branding": "YES",
    "dental service card photo for healthcare website": "YES", 
    "hero banner photo for restaurant website": "NO"
}}
"""
    
    try:
        model = get_chat_model(state.get("llm_model"))
        response = model.invoke(batch_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            matching_results = json.loads(json_str)
            
            needed_images = []
            for req in image_requirements:
                description = req["description"]
                has_suitable = matching_results.get(description, "NO") == "YES"
                
                if not has_suitable:
                    needed_images.append(req)
                    # print(f" Need to generate: {description} ({req['category']})")
                else:
                    print(f"✅ Found suitable existing images for: {description} ({req['category']})")
            
            return needed_images
        else:
            # print("⚠️ Could not parse batch matching results, generating all images")
            return image_requirements
            
    except Exception as e:
        # print(f"⚠️ Batch matching failed: {e}, generating all images")
        return image_requirements

def _generate_and_save_new_images(needed_images: List[Dict[str, Any]]):
    """
    Generate new images using Pexels API and save them to CSV.
    """
    # print(f"🖼️ Generating {len(needed_images)} new images...")
    
    for req in needed_images:
        description = req["description"]
        website_type = req["website_type"]
        context = req["context"]
        category = req["category"]
        
        # Generate only 1 high-quality image for this description
        image_urls = _generate_high_quality_images_from_pexels(description, context, category)
        
        if image_urls:
            # Save to CSV
            _save_image_to_csv(description, website_type, context, category, image_urls)
            # print(f"✅ Generated and saved {len(image_urls)} images for: {description} ({category})")
        else:
            print(f"❌ Failed to generate images for: {description} ({category})")

def _generate_high_quality_images_from_pexels(description: str, context: str, category: str, max_images: int = 1) -> List[str]:
    """
    Generate high-quality images from Pexels API with multiple search strategies for better accuracy.
    """
    if not PEXELS_API_KEY or PEXELS_API_KEY == "YOUR_PEXELS_API_KEY_HERE":
        print("⚠️ Pexels API key not configured, using placeholder URLs")
        return _generate_placeholder_urls(description, category, max_images)
    
    headers = {"Authorization": PEXELS_API_KEY}
    
    # Get multiple search strategies
    search_strategies = _get_search_strategies(description, context, category)
    
    for search_query in search_strategies:
        try:
            params = {
                "query": search_query,
                "per_page": max_images,
                "orientation": "landscape" if category in ["banner", "photo"] else "all"
            }
            
            response = requests.get(f"{PEXELS_BASE_URL}/search", headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("photos") and len(data["photos"]) > 0:
                image_urls = []
                for photo in data["photos"][:max_images]:
                    # Use large2x for ultra HD quality
                    image_urls.append(photo["src"]["large2x"])
                
                # print(f"✅ Found {len(image_urls)} images with query: '{search_query}'")
                return image_urls
            else:
                print(f"⚠️ No results for query: '{search_query}'")
                
        except Exception as e:
            print(f"❌ Search failed for '{search_query}': {e}")
            continue
    
    print(f"❌ All search strategies failed for '{description}', using placeholder")
    return _generate_placeholder_urls(description, category, max_images)

def _get_search_strategies(description: str, context: str, category: str) -> List[str]:
    """
    Generate multiple search strategies for better image matching.
    """
    strategies = []
    
    if category == "logo":
        strategies = _get_logo_search_strategies(description, context)
    elif category == "photo":
        strategies = _get_photo_search_strategies(description, context)
    elif category == "banner":
        strategies = _get_banner_search_strategies(description, context)
    elif category == "icon":
        strategies = _get_icon_search_strategies(description, context)
    else:
        strategies = _get_general_search_strategies(description, context)
    
    return strategies

def _get_logo_search_strategies(description: str, context: str) -> List[str]:
    """
    Generate logo-specific search strategies that work better with Pexels API.
    """
    strategies = []
    
    # Strategy 1: Look for geometric/abstract patterns that can be used as logos
    strategies.append("geometric pattern")
    strategies.append("abstract design")
    strategies.append("minimalist art")
    strategies.append("geometric shapes")
    
    # Strategy 2: Look for symbols/icons that can be converted to logos
    strategies.append("symbol icon")
    strategies.append("badge design")
    strategies.append("emblem")
    
    # Strategy 3: Industry-specific symbols
    industry_terms = _extract_industry_terms(description)
    if industry_terms:
        if "medical" in industry_terms or "health" in industry_terms:
            strategies.append("medical symbol")
            strategies.append("health cross")
        elif "spa" in industry_terms or "beauty" in industry_terms:
            strategies.append("spa symbol")
            strategies.append("wellness icon")
        elif "restaurant" in industry_terms or "food" in industry_terms:
            strategies.append("restaurant symbol")
            strategies.append("food icon")
    
    # Strategy 4: Simple patterns that can be logo-ized
    strategies.append("simple pattern")
    strategies.append("monochrome design")
    
    return strategies[:4]  # Limit to 4 strategies

def _get_photo_search_strategies(description: str, context: str) -> List[str]:
    """
    Generate photo-specific search strategies.
    """
    strategies = []
    
    # Strategy 1: Extract main subject
    main_subject = _extract_main_subject(description)
    if main_subject:
        strategies.append(main_subject)
        strategies.append(f"{main_subject} professional")
    
    # Strategy 2: Extract industry/context
    industry_terms = _extract_industry_terms(description)
    if industry_terms:
        strategies.append(f"{industry_terms[0]} professional")
        strategies.append(f"{industry_terms[0]} service")
    
    # Strategy 3: Context-based
    if "service" in context.lower():
        strategies.append("professional service")
    elif "team" in context.lower():
        strategies.append("professional team")
    elif "treatment" in context.lower():
        strategies.append("spa treatment")
    
    return strategies[:4]

def _get_banner_search_strategies(description: str, context: str) -> List[str]:
    """
    Generate banner-specific search strategies.
    """
    strategies = []
    
    # Strategy 1: Extract location/scene
    location_terms = _extract_location_terms(description)
    if location_terms:
        strategies.append(location_terms[0])
        strategies.append(f"{location_terms[0]} background")
    
    # Strategy 2: Extract mood/atmosphere
    mood_terms = _extract_mood_terms(description)
    if mood_terms:
        strategies.append(mood_terms[0])
    
    # Strategy 3: Context-based
    if "hero" in context.lower():
        strategies.append("hero background")
        strategies.append("banner background")
    
    # Strategy 4: Industry-specific
    industry_terms = _extract_industry_terms(description)
    if industry_terms:
        strategies.append(f"{industry_terms[0]} background")
    
    return strategies[:4]

def _get_icon_search_strategies(description: str, context: str) -> List[str]:
    """
    Generate icon-specific search strategies.
    """
    strategies = []
    
    # Strategy 1: Extract icon type
    icon_terms = _extract_icon_terms(description)
    if icon_terms:
        strategies.append(f"{icon_terms[0]} icon")
        strategies.append(f"{icon_terms[0]} symbol")
    
    # Strategy 2: Context-based
    if "service" in context.lower():
        strategies.append("service icon")
    elif "social" in context.lower():
        strategies.append("social media icon")
    elif "process" in context.lower():
        strategies.append("process icon")
    
    # Strategy 3: Industry-specific
    industry_terms = _extract_industry_terms(description)
    if industry_terms:
        strategies.append(f"{industry_terms[0]} icon")
    
    return strategies[:4]

def _get_general_search_strategies(description: str, context: str) -> List[str]:
    """
    Generate general search strategies.
    """
    strategies = []
    
    # Extract key terms
    key_terms = _extract_key_terms(description)
    if key_terms:
        strategies.append(" ".join(key_terms[:2]))
        strategies.append(" ".join(key_terms[:3]))
    
    # Context-based
    if context:
        strategies.append(context)
    
    return strategies[:3]

def _extract_industry_terms(description: str) -> List[str]:
    """
    Extract industry-specific terms from description.
    """
    industry_keywords = {
        'medspa': ['spa', 'wellness', 'beauty', 'skincare'],
        'salon': ['salon', 'hair', 'beauty', 'styling'],
        'healthcare': ['medical', 'health', 'hospital', 'clinic'],
        'restaurant': ['restaurant', 'food', 'dining', 'cuisine'],
        'business': ['business', 'corporate', 'office', 'professional'],
        'real estate': ['real estate', 'property', 'home', 'house']
    }
    
    description_lower = description.lower()
    found_terms = []
    
    for industry, terms in industry_keywords.items():
        for term in terms:
            if term in description_lower:
                found_terms.append(term)
                break
    
    return found_terms

def _extract_main_subject(description: str) -> str:
    """
    Extract the main subject from description.
    """
    subjects = ['person', 'people', 'woman', 'man', 'doctor', 'nurse', 'chef', 'staff', 'team', 'customer', 'client']
    description_lower = description.lower()
    
    for subject in subjects:
        if subject in description_lower:
            return subject
    
    return ""

def _extract_location_terms(description: str) -> List[str]:
    """
    Extract location/scene terms from description.
    """
    locations = ['city', 'urban', 'nature', 'outdoor', 'indoor', 'office', 'clinic', 'restaurant', 'spa', 'salon']
    description_lower = description.lower()
    found_locations = []
    
    for location in locations:
        if location in description_lower:
            found_locations.append(location)
    
    return found_locations

def _extract_mood_terms(description: str) -> List[str]:
    """
    Extract mood/atmosphere terms from description.
    """
    moods = ['calm', 'peaceful', 'professional', 'modern', 'elegant', 'luxury', 'minimal', 'clean']
    description_lower = description.lower()
    found_moods = []
    
    for mood in moods:
        if mood in description_lower:
            found_moods.append(mood)
    
    return found_moods

def _extract_icon_terms(description: str) -> List[str]:
    """
    Extract icon-specific terms from description.
    """
    icon_types = ['heart', 'star', 'check', 'arrow', 'phone', 'email', 'location', 'calendar', 'user', 'settings']
    description_lower = description.lower()
    found_icons = []
    
    for icon in icon_types:
        if icon in description_lower:
            found_icons.append(icon)
    
    return found_icons

def _extract_key_terms(description: str) -> List[str]:
    """
    Extract key meaningful terms from description.
    """
    # Remove common words
    common_words = {
        "image", "for", "website", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "of", "with", "by",
        "card", "section", "display", "show", "photo", "picture", "graphic", "design", "element"
    }
    
    words = description.lower().replace(",", " ").replace(".", " ").split()
    meaningful_words = [word for word in words if word not in common_words and len(word) > 2]
    
    return meaningful_words[:5]

def _infer_category_from_description(description: str) -> str:
    """
    Infer category from description text.
    """
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['logo', 'brand', 'monogram', 'wordmark']):
        return 'logo'
    elif any(word in description_lower for word in ['banner', 'hero', 'background', 'scenic']):
        return 'banner'
    elif any(word in description_lower for word in ['icon', 'badge', 'symbol', 'line icon']):
        return 'icon'
    else:
        return 'photo'

def _generate_placeholder_urls(description: str, category: str, count: int) -> List[str]:
    """
    Generate better placeholder URLs, especially for logos.
    """
    urls = []
    for i in range(count):
        if category == "logo":
            # Create better logo placeholders with transparent background
            # Extract key terms for the logo text
            key_terms = _extract_key_terms_for_logo(description)
            logo_text = "+".join(key_terms[:2]) if key_terms else "LOGO"
            
            # Use a more logo-like placeholder with better styling
            url = f"https://via.placeholder.com/200x100/ffffff/333333?text={logo_text}"
        elif category == "icon":
            # For icons, use smaller placeholder
            url = f"https://via.placeholder.com/64x64/666666/ffffff?text=ICON+{i+1}"
        else:
            # For photos and banners, use larger placeholder
            url = f"https://via.placeholder.com/800x600/cccccc/666666?text={description.replace(' ', '+')}+{i+1}"
        urls.append(url)
    return urls

def _extract_key_terms_for_logo(description: str) -> List[str]:
    """
    Extract key terms from description for logo text.
    """
    # Remove common words and extract meaningful terms
    common_words = {
        "logo", "design", "for", "navbar", "branding", "header", "footer", "company", "business"
    }
    
    words = description.lower().replace(",", " ").replace(".", " ").split()
    meaningful_words = [word for word in words if word not in common_words and len(word) > 2]
    
    # Take first 2 meaningful words
    return meaningful_words[:2]

# Add this new function to process logos and remove backgrounds
def _process_logo_for_code_generation(image_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process logo images to make them look more like proper logos.
    Add CSS instructions for background removal and logo styling.
    """
    if image_data.get("category") == "logo":
        # Add logo-specific processing instructions
        image_data["logo_processing"] = {
            "remove_background": True,
            "css_filters": "filter: brightness(1.1) contrast(1.2);",
            "background_removal_css": "background: transparent; mix-blend-mode: multiply;",
            "logo_styling": "border-radius: 8px; padding: 10px; max-width: 200px; height: auto;"
        }
        
        # Add instructions for the code generator
        image_data["logo_instructions"] = (
            "This is a LOGO image. Apply the following CSS to make it look like a proper logo:\n"
            "1. Remove background: background: transparent;\n"
            "2. Apply filters: filter: brightness(1.1) contrast(1.2);\n"
            "3. Add logo styling: border-radius: 8px; padding: 10px; max-width: 200px;\n"
            "4. Use mix-blend-mode: multiply; to blend with any background\n"
            "5. Ensure it looks clean and professional"
        )
    
    return image_data

def _save_image_to_csv(description: str, website_type: str, context: str, category: str, urls: List[str]):
    """
    Save image information to CSV file with website type and category.
    Updated to match actual CSV structure: s_no,description,website_type,context,url1,url2
    """
    # Ensure CSV file exists with headers (matching actual structure)
    if not IMAGES_CSV_PATH.exists():
        with open(IMAGES_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['s_no', 'description', 'website_type', 'context', 'url1', 'url2'])
    
    # Get next serial number
    next_s_no = _get_next_serial_number()
    
    # Prepare row data (matching actual CSV structure)
    row = [next_s_no, description, website_type, context]
    
    # Add URLs (pad with empty strings if less than 2)
    for i in range(2):
        if i < len(urls):
            row.append(urls[i])
        else:
            row.append("")
    
    # Append to CSV
    with open(IMAGES_CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def _get_next_serial_number() -> int:
    """
    Get the next serial number for the CSV file.
    """
    if not IMAGES_CSV_PATH.exists():
        return 1
    
    try:
        with open(IMAGES_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) <= 1:  # Only header or empty
                return 1
            return int(rows[-1][0]) + 1
    except Exception:
        return 1

def _load_images_from_csv() -> List[Dict[str, Any]]:
    """
    Load all images from CSV file.
    Updated to work with actual CSV structure and infer categories.
    """
    if not IMAGES_CSV_PATH.exists():
        return []
    
    images = []
    try:
        with open(IMAGES_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Collect all non-empty URLs
                urls = []
                for i in range(1, 3):  # url1, url2
                    url_key = f"url{i}"
                    if row.get(url_key):
                        urls.append(row[url_key])
                
                # Infer category from description
                category = _infer_category_from_description(row["description"])
                
                images.append({
                    "s_no": row["s_no"],
                    "description": row["description"],
                    "website_type": row.get("website_type", "unknown"),
                    "context": row["context"],
                    "category": category,  # Inferred from description
                    "urls": urls
                })
    except Exception as e:
        print(f"❌ Error loading images from CSV: {e}")
    
    return images

def _load_relevant_images_from_csv(image_requirements: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load ONLY the specific images that were identified as needed from CSV.
    This is much more efficient than loading all images.
    """
    print("📋 Loading ONLY needed images from CSV for code generation...")
    
    all_images = _load_images_from_csv()
    if not all_images:
        print(" No images found in CSV")
        return []
    
    # Use single batch call to find matching images for all requirements
    matching_results = _batch_find_matching_images(image_requirements, all_images, state)
    
    relevant_images = []
    
    # Process each requirement and its matching images
    for req in image_requirements:
        description = req["description"]
        matching_images = matching_results.get(description, [])
            
        for img in matching_images:
            # Convert to format expected by code generator
            formatted_image = {
                "id": f"csv_{img['s_no']}",
                "type": req["description"],
                "description": img["description"],
                "website_type": img["website_type"],
                "context": img["context"],
                "category": img["category"],
                "urls": img["urls"],
                "primary_url": img["urls"][0] if img["urls"] else "",
                "alt_text": f"{img['description']} - {img['context']}",
                "source": "csv_database"
            }
            relevant_images.append(formatted_image)
    
    print(f"✅ Loaded {len(relevant_images)} specific images for code generation (instead of all {len(all_images)} images)")
    return relevant_images

def _batch_find_matching_images(image_requirements: List[Dict[str, Any]], all_images: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Batch find matching images for all requirements in a single LLM call.
    Fixed to use string keys instead of dict keys.
    """
    if not all_images:
        return {}
    
    # Prepare image data for LLM
    image_data = []
    for img in all_images:
        image_data.append({
            "s_no": img["s_no"],
            "description": img["description"],
            "website_type": img["website_type"],
            "context": img["context"],
            "category": img["category"],
            "url_count": len(img["urls"])
        })
    
    # Prepare requirements data for LLM
    requirements_data = []
    for req in image_requirements:
        requirements_data.append({
            "description": req["description"],
            "website_type": req["website_type"],
            "context": req["context"],
            "category": req["category"]
        })
    
    batch_prompt = f"""
You are matching image requirements with available images in a database.

NEEDED IMAGES:
{json.dumps(requirements_data, indent=2)}

AVAILABLE IMAGES:
{json.dumps(image_data, indent=2)}

Your task is to find images that are suitable for each needed image.

Consider images suitable if:
1. They serve the same or SIMILAR purpose (same or similar context)
2. They are for the same or similar website type
3. They have the SAME category (logo, photo, icon, banner)
4. The description is conceptually similar or related

CRITICAL: Category must match exactly:
- LOGO images can only match other LOGO images
- PHOTO images can only match other PHOTO images
- ICON images can only match other ICON images
- BANNER images can only match other BANNER images

IMPORTANT: Be MORE LENIENT with matching. If there's any reasonable similarity, consider it suitable.

Examples of good matches (be generous):
- "dental hospital service card" (PHOTO) matches "medical service card photo" (PHOTO)
- "company logo design" (LOGO) matches "business logo design" (LOGO)
- "medspa logo" (LOGO) matches "beauty logo" (LOGO)
- "facial treatment photo" (PHOTO) matches "spa treatment photo" (PHOTO)

Return a JSON object where keys are the needed image descriptions and values are arrays of matching s_no values.

Example:
{{
    "company logo design for navbar branding": [1, 5],
    "dental service card photo for healthcare website": [3, 7],
    "hero banner photo for restaurant website": [2]
}}
"""
    
    try:
        model = get_chat_model(state.get("llm_model"))
        response = model.invoke(batch_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            matching_results = json.loads(json_str)
            
            # Convert to the expected format with string keys
            result = {}
            for req in image_requirements:
                description = req["description"]
                matching_s_nos = matching_results.get(description, [])
                matching_images = [img for img in all_images if int(img["s_no"]) in matching_s_nos]
                result[description] = matching_images
            
            return result
        else:
            print("⚠️ Could not parse batch matching results")
            return {}
            
    except Exception as e:
        print(f"⚠️ Batch matching failed: {e}")
        return {}

def photo_generator_route(state: Dict[str, Any]) -> str:
    """
    Route after photo generation - always go to code generator.
    """
    return "generator"

# Add this function to handle uploaded logos in the photo_generator_node.py

def _add_uploaded_logo_to_images(gi: Dict[str, Any], final_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add uploaded logo to the images list for code generation."""
    
    if not gi.get("has_uploaded_logo") or not gi.get("uploaded_logo_url"):
        return final_images
    
    # Create logo image entry
    logo_image = {
        "id": "uploaded_logo",
        "type": "uploaded company logo",
        "description": "User uploaded company logo for branding",
        "website_type": "company branding",
        "context": "header, navbar, footer, branding",
        "category": "logo",
        "urls": [gi.get("uploaded_logo_url")],
        "primary_url": gi.get("uploaded_logo_url"),
        "alt_text": "Company logo",
        "source": "user_upload",
        "priority": "highest"  # Mark as highest priority
    }
    
    # Add logo at the beginning of the images list (highest priority)
    final_images.insert(0, logo_image)
    print(f"🖼️ Added uploaded logo to images: {gi.get('uploaded_logo_url')}")
    
    return final_images

def _add_uploaded_image_to_images(gi: Dict[str, Any], final_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add uploaded image to the images list for code generation."""
    
    if not gi.get("has_uploaded_image") or not gi.get("uploaded_image_url"):
        return final_images
    
    # Create image entry
    uploaded_image = {
        "id": "uploaded_image",
        "type": "uploaded user image",
        "description": "User uploaded image for website content",
        "website_type": "user content",
        "context": "hero, about, gallery, portfolio, service, product, contact, testimonials, blog",
        "category": "photo",
        "urls": [gi.get("uploaded_image_url")],
        "primary_url": gi.get("uploaded_image_url"),
        "alt_text": "User uploaded image",
        "source": "user_upload",
        "priority": "high"  # Mark as high priority
    }
    
    # Add image at the beginning of the images list (high priority, after logo)
    final_images.insert(0, uploaded_image)
    print(f"🖼️ Added uploaded image to images: {gi.get('uploaded_image_url')}")
    
    return final_images