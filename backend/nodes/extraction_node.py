# nodes/doc_extraction.py
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from llm import get_chat_model, call_llm_json

def _read_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return ""

def _read_docx_text(path: str) -> str:
    try:
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

def _read_plain(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def _extract_business_information(text: str, llm_model: Optional[str] = None) -> Dict[str, Any]:
    """Extract specific business information from document text using LLM."""
    if not text or len(text.strip()) < 50:
        return {}
    
    system_prompt = """You are an expert business information extractor. Analyze the document and extract ALL relevant business information.

Return a JSON object with these fields:
{
    "business_name": "string or null",
    "brand_name": "string or null", 
    "unique_value_proposition": "string or null",
    "competitor_websites": ["array of website URLs or empty array"],
    "color_palette": "string or null",
    "preferred_font_style": "string or null",
    "logo_url": "string or null"
}

INSTRUCTIONS:
1. Read the ENTIRE document carefully
2. Look for ANY mention of business information, even if not in exact format
3. Extract colors mentioned anywhere (black, white, gold, minimalist, elegant, etc.)
4. Extract font preferences mentioned anywhere (Beautifully Delicious, serif, sans-serif, etc.)
5. For competitor websites: ONLY extract websites that are clearly mentioned as competitors or in a "Competitors and Their Websites" section. Do NOT include:
   - Email addresses (gmail.com, yahoo.com, etc.)
   - General service websites (google.com, canva.com, etc.)
   - The business's own website
   - Any other random URLs in the document
6. Extract unique value propositions or business descriptions
7. Extract business names or company names
8. Be thorough and extract everything relevant
9. If you find partial information, include it
10. Don't miss any important details

EXAMPLES of what to look for:
- "Black and white, minimalist, elegant" → color_palette
- "Beautifully Delicious font" → preferred_font_style  
- "www.thirdcoastiv.com, serenitydermatology.com, sovein.vip" (from competitors section) → competitor_websites
- "We are a locally owned business..." → unique_value_proposition
- "7th Dimension Aesthetics" → business_name

IMPORTANT: For competitor_websites, be very selective and only include actual competitor websites mentioned in the competitors section, not any random URLs in the document.

Extract EVERYTHING you can find!"""

    user_prompt = f"Analyze this document and extract ALL business information:\n\n{text}"
    
    try:
        chat = get_chat_model(llm_model, temperature=0.1)
        result = call_llm_json(chat, system_prompt, user_prompt)
        # print(f"🤖 LLM extraction result: {result}")
        return result or {}
    except Exception as e:
        # print(f"LLM extraction failed: {e}")
        return {}

def _candidate_json_blobs(text: str) -> list[str]:
    import re
    blobs = []
    # naive: braces or brackets blocks
    for m in re.finditer(r"(\{[\s\S]*?\})", text):
        s = m.group(1).strip()
        if len(s) > 2:
            blobs.append(s)
            if len(blobs) >= 5: break
    for m in re.finditer(r"(\[[\s\S]*?\])", text):
        s = m.group(1).strip()
        if len(s) > 2:
            blobs.append(s)
            if len(blobs) >= 5: break
    return blobs

def doc_extraction(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced document extraction focused on business information."""
    print("--- Running Business-Focused Document Extraction ---")
    
    ctx = state.get("context") or {}
    doc = state.get("doc") or {}
    path = doc.get("path")
    mime = (doc.get("mime") or "").lower()
    llm_model = state.get("llm_model")

    text = ""
    if path and Path(path).exists():
        print(f"📄 Processing document: {path}")
        if mime == "application/pdf" or path.lower().endswith(".pdf"):
            text = _read_pdf_text(path)
        elif "wordprocessingml.document" in mime or path.lower().endswith(".docx"):
            text = _read_docx_text(path)
        elif mime.startswith("text/") or path.lower().endswith((".txt",".md",".csv",".json")):
            text = _read_plain(path)
        else:
            text = _read_plain(path)

    if not text:
        print("❌ No text extracted from document")
        ctx["extraction"] = {
            "path": path,
            "mime": mime,
            "ok": False,
            "error": "No text could be extracted from the document"
        }
        state["context"] = ctx
        return state

    # print(f"✅ Extracted {len(text)} characters from document")
    # print(f"📝 Document text preview: {text[:500]}...")
    
    # Let LLM do ALL the intelligent extraction
    # print("🧠 Using LLM to extract business information...")
    business_info = _extract_business_information(text, llm_model)
    
    # Legacy JSON candidates for backward compatibility
    json_candidates = _candidate_json_blobs(text) if text else []
    
    # Build extraction result
    extraction_result = {
        "path": path,
        "mime": mime,
        "text_length": len(text),
        "text_excerpt": text[:4000],
        "ok": True,
        
        # Business information (HIGH PRIORITY) - ALL from LLM
        "business_name": business_info.get("business_name"),
        "brand_name": business_info.get("brand_name"),
        "unique_value_proposition": business_info.get("unique_value_proposition"),
        "color_palette": business_info.get("color_palette"),
        "preferred_font_style": business_info.get("preferred_font_style"),
        "logo_url": business_info.get("logo_url"),
        
        # Legacy compatibility
        "json_candidates": json_candidates,
        
        # Extraction metadata
        "has_business_info": any([
            business_info.get("business_name"),
            business_info.get("brand_name"),
            business_info.get("unique_value_proposition"),
            business_info.get("color_palette"),
            business_info.get("preferred_font_style"),
            business_info.get("logo_url")
        ])
    }
    
    # print(f"📊 Business extraction complete:")
    # print(f"   - Business name: {business_info.get('business_name', 'Not found')}")
    # print(f"   - Brand name: {business_info.get('brand_name', 'Not found')}")
    # print(f"   - Unique Value Proposition: {business_info.get('unique_value_proposition', 'Not found')[:100]}...")
    # print(f"   - Color palette: {business_info.get('color_palette', 'Not found')}")
    # print(f"   - Font style: {business_info.get('preferred_font_style', 'Not found')}")
    # print(f"   - Logo URL: {business_info.get('logo_url', 'Not found')}")
    
    ctx["extraction"] = extraction_result
    state["context"] = ctx
    return state 