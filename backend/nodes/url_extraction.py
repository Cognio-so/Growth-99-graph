# nodes/url_extraction.py
from typing import Dict, Any
import os, httpx

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
FIRECRAWL_ENDPOINT = os.getenv("FIRECRAWL_ENDPOINT", "https://api.firecrawl.dev/v1/scrape")

def _firecrawl_fetch(url: str) -> Dict[str, Any]:
    """
    Calls Firecrawl to extract page content.
    Set FIRECRAWL_API_KEY in env. Endpoint is configurable via FIRECRAWL_ENDPOINT.
    Response fields vary; we try common keys like 'markdown', 'content', 'html', 'text'.
    """
    if not FIRECRAWL_API_KEY:
        return {"ok": False, "reason": "missing_api_key"}

    headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"}
    payload = {"url": url}
    try:
        with httpx.Client(timeout=30) as client:
            r = client.post(FIRECRAWL_ENDPOINT, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data.get("markdown") or data.get("content") or data.get("html") or data.get("text") or ""
            return {"ok": True, "data": data, "content": content}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def url_extraction(state: Dict[str, Any]) -> Dict[str, Any]:
    url = state.get("text","").strip()
    ctx = state.get("context") or {}

    result = _firecrawl_fetch(url)
    ctx["url_extraction"] = result

    # Pipe into generator_input for downstream usage
    gi = ctx.get("generator_input") or {}
    gi["user_text"] = url
    if result.get("ok") and result.get("content"):
        gi["extracted_content"] = result["content"]
        gi["schema_source"] = "url_content"  # generator can use content and/or schemas
    else:
        gi["schema_source"] = "url_failed"

    ctx["generator_input"] = gi
    state["context"] = ctx
    return state