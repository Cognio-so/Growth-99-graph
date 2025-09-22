# nodes/output_node.py
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import json

def _store_conversation_history(session_id: str, message_id: str, user_query: str, ai_response: str, generation_result: dict, sandbox_result: dict) -> str:
    """Store conversation history with unique sandbox URL for each generation"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from db import db_session
        from models import ConversationHistory
        
        # Generate the conversation ID before creating the object
        conversation_id = str(uuid.uuid4())
        
        # For now, store the original sandbox URL without modification
        # The uniqueness will come from having separate ConversationHistory records
        sandbox_url = sandbox_result.get('url', '') if sandbox_result else ''
        
        with db_session() as db:
            conversation = ConversationHistory(
                id=conversation_id,
                session_id=session_id,
                message_id=message_id,
                user_query=user_query,
                ai_response=ai_response,
                generated_code=json.dumps(generation_result) if generation_result else "",
                sandbox_url=sandbox_url,
                generation_timestamp=datetime.utcnow(),
                is_edit=False,
                meta={}
            )
            db.add(conversation)
            db.commit()
            print(f"✅ Stored conversation history: {conversation_id}")
            return conversation_id
    except Exception as e:
        print(f"⚠️ Error storing conversation history (non-critical): {e}")
        return str(uuid.uuid4())  # Return a fallback ID

def _update_session_activity(session_id: str, title: str = None):
    """Update session activity timestamp and optionally title"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from db import db_session
        from models import Session
        
        with db_session() as db:
            session = db.get(Session, session_id)
            if session:
                session.updated_at = datetime.utcnow()
                if title:
                    session.title = title
                db.commit()
                print(f"✅ Updated session activity: {session_id}")
            else:
                print(f"⚠️ Session not found for activity update: {session_id}")

    except Exception as e:
        print(f"⚠️ Error updating session activity (non-critical): {e}")

def output_result(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced output node that stores conversation history and generated code"""
    print("--- Running Output Node (Enhanced with History Storage) ---")
    
    try:
        ctx = state.get("context", {})
        session_id = state.get("session_id")
        user_query = state.get("text", "")
        if ctx.get("sandbox_failed"):
            print(f"🛑 Sandbox failed for session {session_id} - returning error result")
            ctx["final_result"] = {
                "url": None,
                "message": ctx.get("sandbox_error", "Sandbox failed due to code error. Please try again."),
                "success": False
            }
            state["context"] = ctx
            return state
        # CRITICAL: Restore both user and AI messages if they were lost during processing
        immediate_ai_response = ctx.get("immediate_ai_response")
        user_message = ctx.get("user_message")
        current_messages = state.get("messages", [])
        
        print(f"🤖 Output node - Current messages count: {len(current_messages)}")
        print(f"🤖 Output node - Has AI response in context: {immediate_ai_response is not None}")
        print(f"🤖 Output node - Has user message in context: {user_message is not None}")
        
        # Check what messages we have
        has_user_message = any(msg.get("role") == "user" for msg in current_messages)
        has_ai_response = any(msg.get("role") == "assistant" for msg in current_messages)
        
        print(f"🤖 Output node - Has user message in array: {has_user_message}")
        print(f" Output node - Has AI response in array: {has_ai_response}")
        
        # Restore missing messages
        messages_to_add = []
        
        if not has_user_message and user_message:
            messages_to_add.append(user_message)
            print("🤖 Restoring user message from context")
        
        if not has_ai_response and immediate_ai_response:
            messages_to_add.append(immediate_ai_response)
            print("🤖 Restoring AI response from context")
        
        if messages_to_add:
            state["messages"] = current_messages + messages_to_add
            print(f" Output node - Final messages count: {len(state['messages'])}")
            print(f" Output node - Final messages: {[msg.get('role') + ': ' + msg.get('content', '')[:30] + '...' for msg in state['messages']]}")
        else:
            print("🤖 All messages already present")
        
        # Get the latest message ID for this session
        message_id = None
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from db import db_session
            from models import Message
            from sqlalchemy import select, desc
            
            with db_session() as db:
                stmt = (
                    select(Message.id)
                    .where(Message.session_id == session_id)
                    .order_by(desc(Message.created_at))
                    .limit(1)
                )
                result = db.execute(stmt).first()
                if result:
                    message_id = result[0]
        except Exception as e:
            print(f"⚠️ Error getting message ID (non-critical): {e}")
        
        # Get generation and sandbox results
        generation_result = ctx.get("generation_result", {})
        sandbox_result = ctx.get("sandbox_result", {})
        
        # Create final AI response text for database storage
        final_ai_response = "Design generated successfully"
        if generation_result:
            final_ai_response += f" with {len(generation_result.get('components', []))} components"
        if sandbox_result.get('url'):
            final_ai_response += f" and deployed to sandbox"
        
        # Store conversation history (non-critical - don't fail if this fails)
        conversation_id = None
        if message_id:
            try:
                conversation_id = _store_conversation_history(
                    session_id=session_id,
                    message_id=message_id,
                    user_query=user_query,
                    ai_response=final_ai_response,
                    generation_result=generation_result,
                    sandbox_result=sandbox_result
                )
                
                # Add conversationId to the state so frontend can access it
                if conversation_id:
                    ctx = state.get("context") or {}
                    ctx["conversation_id"] = conversation_id
                    state["context"] = ctx
                    print(f"✅ Added conversationId to state: {conversation_id}")
            except Exception as e:
                print(f"⚠️ Error storing conversation history (non-critical): {e}")
        
        # Store generated code and sandbox URL (non-critical - don't fail if this fails)
        if conversation_id and sandbox_result.get('url'):
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                from db import db_session
                from models import SessionGeneratedLinks
                import json
                
                with db_session() as db:
                    link = SessionGeneratedLinks(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        conversation_id=conversation_id,
                        sandbox_url=sandbox_result['url'],
                        generated_code=json.dumps(generation_result) if generation_result else "",
                        generation_number=1,
                        is_active=True
                    )
                    db.add(link)
                    db.commit()
                    print(f"✅ Stored generated link for conversation {conversation_id}")
            except Exception as e:
                print(f"⚠️ Error storing generated link (non-critical): {e}")
        
        # CRITICAL: Always create final_result if sandbox URL exists
        if sandbox_result and sandbox_result.get('url'):
            ctx["final_result"] = {
                "url": sandbox_result['url'],
                "message": sandbox_result.get('message', 'Application deployed successfully'),
                "success": sandbox_result.get('success', True)
            }
            state["context"] = ctx
            print(f"✅ Created final_result for frontend: {ctx['final_result']['url']}")
        
        # Update session title (non-critical - don't fail if this fails)
        try:
            title = None
            if user_query and len(user_query) > 0:
                title = user_query[:50] + "..." if len(user_query) > 50 else user_query
                _update_session_activity(session_id, title)
            else:
                _update_session_activity(session_id)
        except Exception as e:
            print(f"⚠️ Error updating session activity (non-critical): {e}")
        
        # CRITICAL: Always return the state - never fail the request
        print(f"✅ Output node completed successfully for session: {session_id}")
        return state
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in output node: {e}")
        import traceback
        traceback.print_exc()
        
        # Even if there's a critical error, try to return the state with sandbox URL if it exists
        ctx = state.get("context", {})
        sandbox_result = ctx.get("sandbox_result", {})
        
        if sandbox_result and sandbox_result.get('url'):
            ctx["final_result"] = {
                "url": sandbox_result['url'],
                "message": "Application deployed successfully (with minor issues)",
                "success": True
            }
            state["context"] = ctx
            print(f"✅ Created fallback final_result for frontend: {ctx['final_result']['url']}")
        
        return state


