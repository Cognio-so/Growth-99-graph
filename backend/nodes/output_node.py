# nodes/output_node.py
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import json

def _store_conversation_history(session_id: str, message_id: str, user_query: str, ai_response: str, generation_result: dict, sandbox_result: dict) -> str:
    """Store conversation history with unique sandbox URL for each generation"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from db import db_session
    from models import ConversationHistory
    
    # Generate the conversation ID before creating the object
    conversation_id = str(uuid.uuid4())
    
    # For now, store the original sandbox URL without modification
    # The uniqueness will come from having separate ConversationHistory records
    # and using the restore endpoint to create new sandboxes when needed
    sandbox_url = sandbox_result.get('url', '') if sandbox_result else ""
    
    with db_session() as db:
        # Store the conversation history
        conversation = ConversationHistory(
            id=conversation_id,  # Use the pre-generated ID
            session_id=session_id,
            message_id=message_id,
            user_query=user_query,
            ai_response=ai_response,
            generated_code=json.dumps(generation_result) if generation_result else None,
            sandbox_url=sandbox_url,  # Store the original sandbox URL
            generation_timestamp=datetime.utcnow()
        )
        
        db.add(conversation)
        # db.commit() is handled by the context manager
    
    # Return the ID that we generated before the session closed
    return conversation_id

def _update_session_activity(session_id: str, title: str = None):
    """Update session activity timestamp and title"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from db import db_session
    from models import Session
    
    with db_session() as db:
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.updated_at = datetime.utcnow()
            if title:
                session.title = title
            # db.commit() is handled by the context manager
        else:
            # Create new session if it doesn't exist
            new_session = Session(
                id=session_id,
                title=title or f"Session {session_id[:8]}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_session)
            # db.commit() is handled by the context manager

def output_result(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced output node that stores conversation history and generated code"""
    print("--- Running Output Node (Enhanced with History Storage) ---")
    
    ctx = state.get("context", {})
    session_id = state.get("session_id")
    user_query = state.get("text", "")
    
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
        print(f"Error getting message ID: {e}")
    
    # Get generation and sandbox results
    generation_result = ctx.get("generation_result", {})
    sandbox_result = ctx.get("sandbox_result", {})
    
    # Create AI response text
    ai_response = "Design generated successfully"
    if generation_result:
        ai_response += f" with {len(generation_result.get('components', []))} components"
    if sandbox_result.get('url'):
        ai_response += f" and deployed to sandbox"
    
    # Store conversation history
    if message_id:
        conversation_id = _store_conversation_history(
            session_id=session_id,
            message_id=message_id,
            user_query=user_query,
            ai_response=ai_response,
            generation_result=generation_result,
            sandbox_result=sandbox_result
        )
        
        # Add conversationId to the state so frontend can access it
        if conversation_id:
            ctx = state.get("context") or {}
            ctx["conversation_id"] = conversation_id
            state["context"] = ctx
            print(f"✅ Added conversationId to state: {conversation_id}")
        
        # Store generated code and sandbox URL
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
                        id=str(uuid.uuid4()),  # Add this line
                        session_id=session_id,
                        conversation_id=conversation_id,
                        sandbox_url=sandbox_result['url'],
                        generated_code=json.dumps(generation_result) if generation_result else "",
                        generation_number=1,
                        is_active=True
                    )
                    db.add(link)
                    db.commit()
            except Exception as e:
                print(f"Error storing generated link: {e}")
    
    # Update session title if this is the first message
    title = None
    if user_query and len(user_query) > 0:
        title = user_query[:50] + "..." if len(user_query) > 50 else user_query
        _update_session_activity(session_id, title)
    else:
        _update_session_activity(session_id)
    
    # Return the state unchanged
    return state


