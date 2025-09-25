# nodes/user_query_node.py
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select

from db import db_session
from models import (
    Session as DBSess,
    Message,
    ConversationHistory,
    SessionGeneratedLinks,
)
from graph_types import GraphState

RECENT_LIMIT = 30


def _ensure_session(session_id: Optional[str], meta: Dict[str, Any] | None) -> str:
    with db_session() as db:
        if session_id:
            existing = db.get(DBSess, session_id)
            if existing:

                existing_meta = existing.meta or {}
                if meta:
                    existing_meta.update(meta)
                    existing.meta = existing_meta
                    db.commit()
                return session_id

        sid = session_id or str(uuid.uuid4())

        new_session = DBSess(id=sid, meta=meta or {})
        db.add(new_session)
        db.commit()  

        return sid


def _insert_user_message(session_id: str, content: str, meta: Dict[str, Any] | None):
    with db_session() as db:
        db.add(
            Message(
                id=uuid.uuid4().hex,
                session_id=session_id,
                role="user",
                content=content,
                meta=meta or {},
            )
        )


def _load_recent_messages(session_id: str) -> List[Dict[str, Any]]:
    with db_session() as db:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(RECENT_LIMIT)
        )
        rows = list(db.execute(stmt).scalars())

        for row in rows:
            db.expunge(row)

    rows = list(reversed(rows))
    return [
        {
            "role": r.role,
            "content": r.content,
            "created_at": r.created_at.isoformat(),
            "meta": r.meta,
        }
        for r in rows
    ]


def _store_original_new_design_query(session_id: str, query: str):
    """Store the original 'new design' query as a special message for regeneration."""
    try:
        with db_session() as db:

            existing = db.execute(
                select(Message).where(
                    Message.session_id == session_id,
                    Message.role == "system",
                    Message.content.like("ORIGINAL_QUERY:%"),
                )
            ).scalar_one_or_none()

            if existing:
                db.delete(existing)

            db.add(
                Message(
                    id=uuid.uuid4().hex,
                    session_id=session_id,
                    role="system",
                    content=f"ORIGINAL_QUERY:{query}",
                    meta={"type": "original_new_design_query"},
                )
            )

    except Exception as e:
        print(f"⚠️ Error storing original new design query: {e}")


def _get_original_new_design_query(session_id: str) -> Optional[str]:
    """Retrieve the original 'new design' query from messages."""
    try:
        with db_session() as db:
            result = db.execute(
                select(Message)
                .where(
                    Message.session_id == session_id,
                    Message.role == "system",
                    Message.content.like("ORIGINAL_QUERY:%"),
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()

            if result:

                original_query = result.content.replace("ORIGINAL_QUERY:", "", 1)

                return original_query
            else:
                print(f"⚠️ No original new design query found in messages")
                return None
    except Exception as e:

        return None


def user_node_init_state(payload: Dict[str, Any]) -> GraphState:
    ts = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    text: str = payload["text"]
    llm_model: Optional[str] = payload.get("llm_model")
    doc = payload.get("doc")  
    logo = payload.get("logo")  
    image = payload.get("image")  
    color_palette = payload.get("color_palette")  
    regenerate = bool(payload.get("regenerate", False))

    session_id = _ensure_session(
        payload.get("session_id"),
        meta={
            "llm_model": llm_model,
            "has_doc": bool(doc),
            "has_logo": bool(logo),
            "has_image": bool(image),
        },
    )

    if regenerate:

        if text and text.strip() and text.strip() != "regenerate":

            _insert_user_message(
                session_id,
                text,
                {
                    "doc": doc or None,
                    "logo": logo or None,
                    "image": image or None,
                    "color_palette": color_palette,
                    "regenerate": True,
                },
            )
        else:

            original_query = _get_original_new_design_query(session_id)
            if original_query:

                text = original_query
            else:

                _insert_user_message(
                    session_id,
                    text,
                    {
                        "doc": doc or None,
                        "logo": logo or None,
                        "image": image or None,
                        "color_palette": color_palette,
                        "regenerate": True,
                    },
                )
    else:

        _insert_user_message(
            session_id,
            text,
            {
                "doc": doc or None,
                "logo": logo or None,
                "image": image or None,
                "color_palette": color_palette,
            },
        )

    messages = _load_recent_messages(session_id)

    state = {
        "session_id": session_id,
        "text": text,
        "llm_model": llm_model,
        "doc": doc,
        "logo": logo,
        "image": image,
        "color_palette": color_palette,
        "timestamp": ts,
        "metadata": {"regenerate": regenerate},
        "context": {},
    }

    return state


def _add_immediate_ai_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Add immediate AI response when user submits query"""
    user_text = state.get("text", "")

    if "spa" in user_text.lower() or "medical" in user_text.lower():
        ai_response = "I'll create a beautiful medical spa website with a serene, professional design. Let me build this with calming colors and elegant UI/UX that reflects the luxury spa experience."
    elif (
        "ed-tech" in user_text.lower()
        or "education" in user_text.lower()
        or "student" in user_text.lower()
    ):
        ai_response = "I'll create a beautiful ed-tech platform with login and signup pages designed specifically for students. Let me build this with engaging colors and student-friendly UI/UX."
    elif "landing" in user_text.lower() or "website" in user_text.lower():
        ai_response = "I'll create a stunning landing page that captures your brand's essence. Let me build this with modern design principles and engaging visuals."
    else:
        ai_response = "I'll create a beautiful application based on your requirements. Let me build this with modern design principles and engaging UI/UX."

    current_messages = state.get("messages", [])

    has_user_message = any(msg.get("role") == "user" for msg in current_messages)
    user_message = None
    if not has_user_message and user_text:
        user_message = {
            "role": "user",
            "content": user_text,
            "created_at": datetime.utcnow().isoformat(),
            "meta": {},
        }
        current_messages = current_messages + [user_message]

    ai_message = {
        "role": "assistant",
        "content": ai_response,
        "created_at": datetime.utcnow().isoformat(),
        "meta": {},
    }

    ctx = state.get("context", {})
    ctx["immediate_ai_response"] = ai_message
    ctx["user_message"] = user_message if not has_user_message else None
    state["context"] = ctx

    state["messages"] = current_messages + [ai_message]
    print(f"🤖 New messages count: {len(state['messages'])}")
    print(
        f"🤖 Messages: {[msg.get('role') + ': ' + msg.get('content', '')[:30] + '...' for msg in state['messages']]}"
    )

    return state


def user_node(state: GraphState) -> GraphState:
    """Enhanced user node that clears document information when file is removed or changed."""
    print("--- Running User Node ---")

    current_doc = state.get("doc")
    ctx = state.get("context", {})
    previous_extraction = ctx.get("extraction", {})
    previous_doc_path = previous_extraction.get("path")

    current_doc_path = current_doc.get("path") if current_doc else None

    if not current_doc and previous_extraction.get("has_business_info"):

        _clear_document_information(ctx)

    elif current_doc and previous_doc_path and current_doc_path != previous_doc_path:

        _clear_document_information(ctx)

    elif current_doc and not previous_extraction.get("has_business_info"):
        print(f"📄 New document uploaded: {current_doc.get('name', 'unknown')}")

    elif current_doc and previous_doc_path and current_doc_path == previous_doc_path:
        print(f"📄 Same document being reused: {current_doc.get('name', 'unknown')}")

    elif current_doc:
        print(f" Document provided: {current_doc.get('name', 'unknown')}")
    else:
        print("📝 No document provided")

    state["context"] = ctx

    state = _add_immediate_ai_response(state)
    return state


def _clear_document_information(ctx: Dict[str, Any]) -> None:
    """Helper function to clear all document-related information from context."""

    ctx["extraction"] = {
        "ok": False,
        "reason": "document_removed_or_changed",
        "has_business_info": False,
        "has_competitors": False,
    }

    gi = ctx.get("generator_input", {})
    if gi:

        extracted_fields = [
            "extracted_business_name",
            "extracted_brand_name",
            "extracted_unique_value_proposition",
            "extracted_color_palette",
            "extracted_font_style",
            "extracted_logo_url",
            "extracted_competitor_websites",
            "has_extracted_business_info",
            "extraction_priority",
        ]
        for field in extracted_fields:
            gi.pop(field, None)

        gi["extraction_priority"] = "low"
        gi["has_extracted_business_info"] = False

        ctx["generator_input"] = gi
        print("✅ Cleared all extracted business information from generator input")

    if "competitor_analysis" in ctx:
        ctx["competitor_analysis"] = {
            "ok": False,
            "reason": "document_removed_or_changed",
        }
        print("✅ Cleared competitor analysis")

    print("🗑️ Document information cleanup complete")
