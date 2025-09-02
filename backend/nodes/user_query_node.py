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

def user_node_init_state(payload: Dict[str, Any]) -> GraphState:
    ts = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    text: str = payload["text"]
    llm_model: Optional[str] = payload.get("llm_model")
    doc = payload.get("doc")  # {name,mime,size,path} or None
    regenerate = bool(payload.get("regenerate", False))

    session_id = _ensure_session(payload.get("session_id"), meta={"llm_model": llm_model, "has_doc": bool(doc)})
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
    return state
