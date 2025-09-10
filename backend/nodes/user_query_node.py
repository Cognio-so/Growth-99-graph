# nodes/user_node.py
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select

from db import db_session
from models import Session as DBSess, Message
from graph_types import GraphState

RECENT_LIMIT = 30

def _ensure_session(session_id: Optional[str], meta: Dict[str, Any] | None) -> str:
    with db_session() as db:
        if session_id:
            existing = db.get(DBSess, session_id)
            if existing:
                # PRESERVE existing metadata and only update new fields
                existing_meta = existing.meta or {}
                if meta:
                    existing_meta.update(meta)  # Update with new meta but preserve existing
                    existing.meta = existing_meta
                    db.commit()  # Commit the metadata update
                return session_id
        sid = session_id or str(uuid.uuid4())
        db.add(DBSess(id=sid, meta=meta or {}))
        return sid

def _insert_user_message(session_id: str, content: str, meta: Dict[str, Any] | None):
    with db_session() as db:
        db.add(Message(
            id=uuid.uuid4().hex,
            session_id=session_id,
            role="user",
            content=content,
            meta=meta or {}
        ))

def _load_recent_messages(session_id: str) -> List[Dict[str, Any]]:
    with db_session() as db:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(RECENT_LIMIT)
        )
        rows = list(db.execute(stmt).scalars())
        # Detach objects from session before closing
        for row in rows:
            db.expunge(row)
    
    rows = list(reversed(rows))
    return [{"role": r.role, "content": r.content, "created_at": r.created_at.isoformat(), "meta": r.meta} for r in rows]

def _store_original_new_design_query(session_id: str, query: str):
    """Store the original 'new design' query as a special message for regeneration."""
    try:
        with db_session() as db:
            # Delete any existing original query for this session
            existing = db.execute(
                select(Message).where(
                    Message.session_id == session_id,
                    Message.role == "system",
                    Message.content.like("ORIGINAL_QUERY:%")
                )
            ).scalar_one_or_none()
            
            if existing:
                db.delete(existing)
            
            # Store as a special system message with prefix
            db.add(Message(
                id=uuid.uuid4().hex,
                session_id=session_id,
                role="system",
                content=f"ORIGINAL_QUERY:{query}",
                meta={"type": "original_new_design_query"}
            ))
            print(f"✅ Stored original new design query as message: '{query[:100]}...'")
    except Exception as e:
        print(f"⚠️ Error storing original new design query: {e}")

def _get_original_new_design_query(session_id: str) -> Optional[str]:
    """Retrieve the original 'new design' query from messages."""
    try:
        with db_session() as db:
            result = db.execute(
                select(Message).where(
                    Message.session_id == session_id,
                    Message.role == "system",
                    Message.content.like("ORIGINAL_QUERY:%")
                ).order_by(Message.created_at.desc()).limit(1)
            ).scalar_one_or_none()
            
            if result:
                # Remove the prefix to get the actual query
                original_query = result.content.replace("ORIGINAL_QUERY:", "", 1)
                print(f"✅ Retrieved original new design query from messages: '{original_query[:100]}...'")
                return original_query
            else:
                print(f"⚠️ No original new design query found in messages")
                return None
    except Exception as e:
        print(f"⚠️ Error retrieving original new design query: {e}")
        return None

def user_node_init_state(payload: Dict[str, Any]) -> GraphState:
    ts = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    text: str = payload["text"]
    llm_model: Optional[str] = payload.get("llm_model")
    doc = payload.get("doc")  # {name,mime,size,path} or None
    regenerate = bool(payload.get("regenerate", False))

    session_id = _ensure_session(payload.get("session_id"), meta={"llm_model": llm_model, "has_doc": bool(doc)})
    
    # ENHANCED REGENERATION LOGIC
    if regenerate:
        print("🔄 REGENERATION MODE - Checking if text is provided...")
        
        # Check if frontend provided text
        if text and text.strip() and text.strip() != "regenerate":
            print(f"✅ Frontend provided text, using current text: '{text[:100]}...'")
            # Use the current text from frontend
            _insert_user_message(session_id, text, {"doc": doc or None, "regenerate": True})
        else:
            print("⚠️ No text from frontend, searching for stored original query...")
            # No text from frontend, use stored original query
            original_query = _get_original_new_design_query(session_id)
            if original_query:
                print(f"✅ Using stored original query for regeneration: '{original_query[:100]}...'")
                text = original_query
            else:
                print("⚠️ No stored original query found, using current text for regeneration")
                _insert_user_message(session_id, text, {"doc": doc or None, "regenerate": True})
    else:
        # Normal flow - insert the new message
        _insert_user_message(session_id, text, {"doc": doc or None})
    
    messages = _load_recent_messages(session_id)

    return {
        "session_id": session_id,
        "timestamp": ts if isinstance(ts, str) else ts.isoformat(),
        "text": text,
        "llm_model": llm_model,
        "doc": doc or None,
        "messages": messages,
        "metadata": {"regenerate": regenerate},
        "context": {},
    }

def user_node(state: GraphState) -> GraphState:
    """Enhanced user node that clears document information when file is removed or changed."""
    print("--- Running User Node ---")
    
    # Check if document was removed or changed
    current_doc = state.get("doc")
    ctx = state.get("context", {})
    previous_extraction = ctx.get("extraction", {})
    previous_doc_path = previous_extraction.get("path")
    
    # Get current document path if available
    current_doc_path = current_doc.get("path") if current_doc else None
    
    # Check if document was removed (no current doc but had previous extraction)
    if not current_doc and previous_extraction.get("has_business_info"):
        print("🗑️ Document removed - clearing all extracted information")
        _clear_document_information(ctx)
    
    # Check if document was changed (different path than previous)
    elif current_doc and previous_doc_path and current_doc_path != previous_doc_path:
        print(f" Document changed - clearing old extraction information")
        print(f"   Old: {previous_doc_path}")
        print(f"   New: {current_doc_path}")
        _clear_document_information(ctx)
    
    # Check if document is new (current doc but no previous extraction)
    elif current_doc and not previous_extraction.get("has_business_info"):
        print(f"📄 New document uploaded: {current_doc.get('name', 'unknown')}")
    
    # Check if same document is being reused
    elif current_doc and previous_doc_path and current_doc_path == previous_doc_path:
        print(f"📄 Same document being reused: {current_doc.get('name', 'unknown')}")
    
    elif current_doc:
        print(f" Document provided: {current_doc.get('name', 'unknown')}")
    else:
        print("📝 No document provided")
    
    state["context"] = ctx
    return state

def _clear_document_information(ctx: Dict[str, Any]) -> None:
    """Helper function to clear all document-related information from context."""
    # Clear all extraction-related information
    ctx["extraction"] = {
        "ok": False,
        "reason": "document_removed_or_changed",
        "has_business_info": False,
        "has_competitors": False
    }
    
    # Clear any business information from generator input
    gi = ctx.get("generator_input", {})
    if gi:
        # Remove all extracted business information
        extracted_fields = [
            "extracted_business_name", "extracted_brand_name", 
            "extracted_unique_value_proposition", "extracted_color_palette",
            "extracted_font_style", "extracted_logo_url", 
            "extracted_competitor_websites", "has_extracted_business_info",
            "extraction_priority"
        ]
        for field in extracted_fields:
            gi.pop(field, None)
        
        # Reset extraction priority
        gi["extraction_priority"] = "low"
        gi["has_extracted_business_info"] = False
        
        ctx["generator_input"] = gi
        print("✅ Cleared all extracted business information from generator input")
    
    # Clear competitor analysis if it exists
    if "competitor_analysis" in ctx:
        ctx["competitor_analysis"] = {
            "ok": False,
            "reason": "document_removed_or_changed"
        }
        print("✅ Cleared competitor analysis")
    
    print("🗑️ Document information cleanup complete")