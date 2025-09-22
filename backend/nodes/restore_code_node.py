# nodes/restore_code_node.py
import uuid
from typing import Dict, Any
from db import db_session
from models import SessionGeneratedLinks
from sqlalchemy import select, desc

async def restore_code_from_session(state: Dict[str, Any]) -> Dict[str, Any]:
    """Restore code from a previous session to current sandbox"""
    print("--- Running Restore Code Node ---")
    
    ctx = state.get("context", {})
    session_id = state.get("session_id")
    link_id = ctx.get("restore_link_id")
    
    if not session_id:
        ctx["restore_result"] = {
            "success": False,
            "error": "No session ID provided"
        }
        state["context"] = ctx
        return state
    
    try:
        with db_session() as db:
            if link_id:
                # Restore specific link
                link = db.get(SessionGeneratedLinks, link_id)
                if not link or link.session_id != session_id:
                    ctx["restore_result"] = {
                        "success": False,
                        "error": "Generated link not found"
                    }
                    state["context"] = ctx
                    return state
            else:
                # Get latest link for session
                stmt = (
                    select(SessionGeneratedLinks)
                    .where(SessionGeneratedLinks.session_id == session_id)
                    .order_by(SessionGeneratedLinks.created_at.desc())
                    .limit(1)
                )
                link = db.execute(stmt).scalar_one_or_none()
                if not link:
                    ctx["restore_result"] = {
                        "success": False,
                        "error": "No generated code found for session"
                    }
                    state["context"] = ctx
                    return state
            
            # Store the code to be applied
            ctx["restore_result"] = {
                "success": True,
                "code": link.generated_code,
                "generation_number": link.generation_number,
                "created_at": link.created_at.isoformat(),
                "sandbox_url": link.sandbox_url,
                "message": "Code ready to be applied to current sandbox"
            }
            
            # Set the code in generation result so it can be applied
            ctx["generation_result"] = {
                "e2b_script": link.generated_code,
                "is_restore": True,
                "restore_from": link_id or "latest"
            }
            from nodes.apply_to_Sandbox_node import _ensure_sandbox_for_session, _capture_all_files, _write_files_to_sandbox
            session_id = state.get("session_id")

            sandbox = await _ensure_sandbox_for_session(session_id)

            # write restored code to sandbox
            await _write_files_to_sandbox(sandbox, link.generated_code)

            # capture sandbox state so edit_analyzer & generator have correct base
            captured_files = await _capture_all_files(sandbox)
            ctx["restored_session"] = True
            ctx["active_sandbox_id"] = sandbox.id
            ctx["existing_code_context"] = {
                "files": captured_files,
                "source": "restored_snapshot"
            }

            # optional: store per-conversation snapshot
            conv_id = state.get("conversation_id")
            ctx.setdefault("history_snapshots", {})[conv_id] = captured_files

            state["context"] = ctx
            return state
            print(f"✅ Restored code from session {session_id}, generation {link.generation_number}")
            
    except Exception as e:
        print(f"❌ Error restoring code: {e}")
        ctx["restore_result"] = {
            "success": False,
            "error": str(e)
        }
    
    state["context"] = ctx
    return state
