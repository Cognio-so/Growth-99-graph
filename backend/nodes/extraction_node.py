# nodes/doc_extraction.py
from typing import Dict, Any
from pathlib import Path

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
    ctx = state.get("context") or {}
    doc = state.get("doc") or {}
    path = doc.get("path")
    mime = (doc.get("mime") or "").lower()

    text = ""
    if path and Path(path).exists():
        if mime == "application/pdf" or path.lower().endswith(".pdf"):
            text = _read_pdf_text(path)
        elif "wordprocessingml.document" in mime or path.lower().endswith(".docx"):
            text = _read_docx_text(path)
        elif mime.startswith("text/") or path.lower().endswith((".txt",".md",".csv",".json")):
            text = _read_plain(path)
        else:
            text = _read_plain(path)

    ctx["extraction"] = {
        "path": path,
        "mime": mime,
        "text_excerpt": (text or "")[:4000],
        "json_candidates": _candidate_json_blobs(text) if text else [],
        "ok": bool(text),
    }
    state["context"] = ctx
    return state
