# main.py - Complete version with proper LangSmith integration and logo upload
import os
import uvicorn
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure LangSmith tracing is enabled BEFORE importing anything else
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "lovable-orchestrator")

# Now import LangChain/LangGraph components
from langsmith import Client
from langchain_core.runnables import RunnableConfig

from db import engine
from models import Base
from schemas import UserQueryOut
from nodes.user_query_node import user_node_init_state
from graph import graph
from utlis.docs import save_upload_to_disk, save_logo_to_disk

# LangGraph imports
from langgraph.checkpoint.sqlite import SqliteSaver
from langserve import add_routes
from contextlib import asynccontextmanager
import sqlite3

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🔄 Setting up shared checkpointer...")
    yield
    # Shutdown
    if hasattr(checkpointer, 'conn'):
        checkpointer.conn.close()
    print("🔄 Closed checkpointer connection")

app = FastAPI(
    title="Lovable-like Orchestrator", 
    version="0.5.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for logo serving
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Fix the database creation section:
# CREATE DATABASE TABLES - ONLY IF NEEDED
print("🔄 Checking database...")
try:
    import sqlite3
    import os
    
    # Check if database exists and has correct schema
    db_exists = os.path.exists('app.db')
    
    if db_exists:
        # Check if sessions table exists first
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        sessions_table_exists = cursor.fetchone() is not None
        conn.close()
        
        if not sessions_table_exists:
            print("🔄 Sessions table doesn't exist, creating all tables...")
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully!")
        else:
            # Table exists, check if it has the required columns
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('PRAGMA table_info(sessions)')
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            
            has_updated_at = 'updated_at' in columns
            has_title = 'title' in columns
            
            if has_updated_at and has_title:
                print("✅ Database exists with correct schema")
            else:
                print("🔄 Database exists but needs schema update")
                # SAFE: Add missing columns without dropping data
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                
                if not has_updated_at:
                    print("Adding updated_at column...")
                    try:
                        cursor.execute('ALTER TABLE sessions ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP')
                        conn.commit()
                        print("✅ Added updated_at column")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            print("✅ updated_at column already exists")
                        else:
                            raise
                
                if not has_title:
                    print("Adding title column...")
                    try:
                        cursor.execute('ALTER TABLE sessions ADD COLUMN title VARCHAR(255)')
                        conn.commit()
                        print("✅ Added title column")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            print("✅ title column already exists")
                        else:
                            raise
                
                conn.close()
                
                # Create any missing tables (but don't drop existing ones)
                Base.metadata.create_all(bind=engine)
                print("✅ Database schema updated successfully!")
    else:
        print("🔄 Creating new database...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database created successfully!")
    
    # Verify the schema
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(sessions)')
    columns = [row[1] for row in cursor.fetchall()]
    print('📋 Sessions table columns:', columns)
    conn.close()
    
except Exception as e:
    print(f"❌ Error with database: {e}")
    raise

def _as_uuid(s: str | None) -> str:
    """Convert string to UUID format for LangGraph."""
    if not s:
        from uuid import uuid4
        return str(uuid4())
    
    # If already looks like a UUID, return as-is
    if len(s) == 36 and s.count('-') == 4:
        return s
    
    # Convert session string to UUID format
    import hashlib
    hash_obj = hashlib.md5(s.encode())
    hex_dig = hash_obj.hexdigest()
    
    # Format as UUID: 8-4-4-4-12
    uuid_str = f"{hex_dig[:8]}-{hex_dig[8:12]}-{hex_dig[12:16]}-{hex_dig[16:20]}-{hex_dig[20:32]}"
    return uuid_str

def setup_checkpointer():
    # Use absolute path to ensure both services find the same file
    import os
    from pathlib import Path
    
    db_path = Path(__file__).parent / "checkpoints.db"
    print(f"📁 Using checkpointer database: {db_path}")
    
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return SqliteSaver(conn)

# Create shared checkpointer
checkpointer = setup_checkpointer()

# Compile the graph with shared checkpointer
compiled_graph = graph.compile(checkpointer=checkpointer)

@app.on_event("startup")
def _startup():
    # Database is already created above, just verify LangSmith connection
    try:
        client = Client()
        print(f"✅ Connected to LangSmith. Project: {os.getenv('LANGCHAIN_PROJECT')}")
        print(f"✅ API Key configured: {'Yes' if os.getenv('LANGCHAIN_API_KEY') else 'No'}")
    except Exception as e:
        print(f"⚠️  LangSmith connection issue: {e}")
        print("Make sure LANGCHAIN_API_KEY is set in your .env file")

@app.post("/api/query", response_model=UserQueryOut)
async def accept_query(
    session_id: str | None = Form(None),
    text: str = Form(...),
    llm_model: str | None = Form(None),
    file: UploadFile | None = File(None),
    logo: UploadFile | None = File(None),  # Add logo parameter
    regenerate: bool = Form(False),
):
    try:
        doc = None
        if file is not None:
            doc = await save_upload_to_disk(file)

        logo_data = None
        if logo is not None:
            logo_data = await save_logo_to_disk(logo, session_id)
            print(f"🖼️ Logo uploaded: {logo_data.get('filename')} -> {logo_data.get('url')}")

        payload = {
            "session_id": session_id or None,
            "timestamp": datetime.utcnow().isoformat(),
            "text": text,
            "llm_model": llm_model,
            "doc": doc,
            "logo": logo_data,  # Add logo to payload
            "regenerate": regenerate,
        }

        # Initialize state
        state = user_node_init_state(payload)
        
        # FIXED: Use consistent thread ID that LangGraph Studio can track
        thread_id = _as_uuid(state.get("session_id"))
        
        # FIXED: Create configuration with proper LangSmith integration
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "recursion_limit": 50
            },
            tags=["api_request", "frontend", f"model:{llm_model or 'default'}"],
            metadata={
                "session_id": thread_id,
                "model": llm_model,
                "has_doc": bool(doc),
                "has_logo": bool(logo_data),  # Add logo metadata
                "text_preview": text[:100] if text else "",
                "run_name": f"query_{thread_id[:8]}",  # Add run name for Studio
                "project_name": os.getenv("LANGCHAIN_PROJECT", "lovable-orchestrator")
            }
        )
        
        # FIXED: Use stream method for better LangSmith integration  
        final_result = None
        print(f"🔄 Executing graph with thread_id: {thread_id}")
        
        # Use stream to ensure proper checkpointing
        for chunk in compiled_graph.stream(state, config=config):
            final_result = chunk
            print(f"📊 Node completed: {list(chunk.keys())}")
        
        # Use the final result
        result = final_result[list(final_result.keys())[-1]] if final_result else state
        
        print(f"✅ Graph execution completed. Thread {thread_id} should be saved to checkpoints.db")
        
        return {"session_id": result["session_id"], "accepted": True, "state": result}
    except Exception as e:
        print(f"Error in accept_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# FIXED: Configure LangServe routes properly for Studio integration
add_routes(
    app, 
    compiled_graph.with_config(
        configurable={
            "recursion_limit": 50,
        },
        tags=["langserve", "studio"],
        metadata={"source": "langserve_playground"}
    ), 
    path="/graph"
)

@app.post("/api/cleanup")
async def cleanup_session():
    """Emergency cleanup endpoint - kills all running sandboxes immediately"""
    try:
        # Import the cleanup function
        from nodes.apply_to_Sandbox_node import _kill_existing_sandbox
        
        print("🧹 EMERGENCY CLEANUP - Killing all sandboxes...")
        _kill_existing_sandbox()
        
        return {"success": True, "message": "All sandboxes terminated"}
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/")
def health():
    return {"ok": True, "service": "lovable-orchestrator"}

@app.get("/debug/graph")
def debug_graph():
    return {
        "graph_nodes": list(graph.nodes.keys()),
        "graph_edges": list(graph.edges),
        "langserve_url": "/graph/playground",
        "api_endpoint": "/api/query",
        "langsmith_enabled": os.getenv("LANGCHAIN_TRACING_V2") == "true",
        "langsmith_project": os.getenv("LANGCHAIN_PROJECT", "default")
    }

@app.get("/debug/tracing")
def debug_tracing():
    """Debug endpoint to check tracing configuration"""
    return {
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2"),
        "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT"),
        "LANGCHAIN_API_KEY": "***" if os.getenv("LANGCHAIN_API_KEY") else None,
        "LANGCHAIN_ENDPOINT": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    }

@app.get("/debug/threads")
async def debug_threads():
    """Debug endpoint to list active threads"""
    try:
        from langsmith import Client
        client = Client()
        
        # Get recent runs for this project
        runs = list(client.list_runs(
            project_name=os.getenv("LANGCHAIN_PROJECT", "lovable-orchestrator"),
            limit=10
        ))
        
        thread_info = []
        for run in runs:
            metadata = getattr(run, 'extra', {}).get('metadata', {}) if hasattr(run, 'extra') else {}
            if metadata.get('session_id'):
                thread_info.append({
                    "thread_id": metadata['session_id'],
                    "run_id": str(run.id),
                    "status": run.status,
                    "created_at": run.start_time.isoformat() if run.start_time else None,
                    "name": run.name
                })
        
        return {
            "active_threads": thread_info,
            "total_runs": len(runs),
            "project": os.getenv("LANGCHAIN_PROJECT", "lovable-orchestrator")
        }
    except Exception as e:
        return {"error": str(e), "message": "Could not fetch thread info"}

@app.get("/debug/checkpointer")
async def debug_checkpointer():
    """Debug endpoint to check checkpointer status"""
    try:
        import os
        from pathlib import Path
        
        db_path = Path(__file__).parent / "checkpoints.db"
        
        # Try to get some threads from the checkpointer
        threads = []
        try:
            # List some recent threads (if any)
            cursor = checkpointer.conn.cursor()
            cursor.execute("SELECT DISTINCT thread_id FROM checkpoints LIMIT 10")
            threads = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error querying threads: {e}")
        
        return {
            "checkpointer_type": type(checkpointer).__name__,
            "db_exists": os.path.exists(str(db_path)),
            "db_size": os.path.getsize(str(db_path)) if os.path.exists(str(db_path)) else 0,
            "db_path": str(db_path),
            "recent_threads": threads[:5],  # Show first 5 threads
            "total_threads": len(threads)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/sessions")
async def get_sessions():
    """Get all sessions with their conversation history"""
    try:
        from db import db_session
        from models import Session, ConversationHistory, Message
        from sqlalchemy import select, func, desc
        
        with db_session() as db:
            # Get sessions with their latest conversation and message count
            stmt = (
                select(
                    Session.id,
                    Session.created_at,
                    Session.updated_at,
                    Session.title,
                    Session.meta,
                    func.count(Message.id).label('message_count'),
                    func.max(ConversationHistory.generation_timestamp).label('last_activity')
                )
                .outerjoin(Message, Session.id == Message.session_id)
                .outerjoin(ConversationHistory, Session.id == ConversationHistory.session_id)
                .group_by(Session.id)
                .order_by(desc(Session.updated_at))
            )
            
            sessions = []
            for row in db.execute(stmt):
                sessions.append({
                    "id": row.id,
                    "title": row.title or f"Session {row.id[:8]}",
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                    "message_count": row.message_count or 0,
                    "last_activity": row.last_activity.isoformat() if row.last_activity else None,
                    "meta": row.meta or {}
                })
            
            return {"sessions": sessions}
    except Exception as e:
        print(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed session information including conversation history and generated links"""
    try:
        from db import db_session
        from models import Session, Message, ConversationHistory, SessionGeneratedLinks
        from sqlalchemy import select, desc
        
        with db_session() as db:
            # Get session info
            session = db.get(Session, session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Get messages
            messages_stmt = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at)
            )
            messages = [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat(), "meta": m.meta} for m in db.execute(messages_stmt).scalars()]
            
            # Get conversation history
            conv_stmt = (
                select(ConversationHistory)
                .where(ConversationHistory.session_id == session_id)
                .order_by(ConversationHistory.generation_timestamp)
            )
            conversations = []
            for conv in db.execute(conv_stmt).scalars():
                conversations.append({
                    "id": conv.id,
                    "user_query": conv.user_query,
                    "ai_response": conv.ai_response,
                    "generated_code": conv.generated_code,
                    "sandbox_url": conv.sandbox_url,
                    "generation_timestamp": conv.generation_timestamp.isoformat(),
                    "is_edit": conv.is_edit,
                    "meta": conv.meta
                })
            
            # Get generated links
            links_stmt = (
                select(SessionGeneratedLinks)
                .where(SessionGeneratedLinks.session_id == session_id)
                .order_by(desc(SessionGeneratedLinks.created_at))
            )
            generated_links = []
            for link in db.execute(links_stmt).scalars():
                generated_links.append({
                    "id": link.id,
                    "sandbox_url": link.sandbox_url,
                    "generated_code": link.generated_code,
                    "generation_number": link.generation_number,
                    "created_at": link.created_at.isoformat(),
                    "is_active": link.is_active,
                    "meta": link.meta
                })
            
            return {
                "session": {
                    "id": session.id,
                    "title": session.title or f"Session {session.id[:8]}",
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "meta": session.meta or {}
                },
                "messages": messages,
                "conversations": conversations,
                "generated_links": generated_links
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting session details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/restore")
async def restore_session_code(
    session_id: str,
    link_id: str | None = Form(None),
    text: str = Form("restore")
):
    """Restore code from a previous session to current active sandbox"""
    try:
        # Initialize state for restore operation
        payload = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "text": text,
            "llm_model": None,
            "doc": None,
            "logo": None,
            "regenerate": False,
        }

        # Initialize state
        state = user_node_init_state(payload)
        
        # Add restore context
        state["context"] = {
            "restore_link_id": link_id
        }
        
        # Use consistent thread ID
        thread_id = _as_uuid(state.get("session_id"))
        
        # Create configuration
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "recursion_limit": 50
            },
            tags=["api_request", "restore", "frontend"],
            metadata={
                "session_id": thread_id,
                "restore_link_id": link_id,
                "run_name": f"restore_{thread_id[:8]}",
                "project_name": os.getenv("LANGCHAIN_PROJECT", "lovable-orchestrator")
            }
        )
        
        # Execute the graph
        final_result = None
        print(f"🔄 Restoring code for session: {session_id}")
        
        for chunk in compiled_graph.stream(state, config=config):
            final_result = chunk
            print(f"📊 Node completed: {list(chunk.keys())}")
        
        # Use the final result
        result = final_result[list(final_result.keys())[-1]] if final_result else state
        
        return {"session_id": result["session_id"], "accepted": True, "state": result}
    except Exception as e:
        print(f"Error in restore_session_code: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/conversations/{conversation_id}/restore")
async def restore_conversation_design(session_id: str, conversation_id: str):
    """Restore a specific conversation's design to a new sandbox"""
    from db import db_session
    from models import ConversationHistory
    from nodes.apply_to_Sandbox_node import apply_sandbox
    
    with db_session() as db:
        # Get the conversation history
        conversation = db.query(ConversationHistory).filter(
            ConversationHistory.id == conversation_id,
            ConversationHistory.session_id == session_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if not conversation.generated_code:
            raise HTTPException(status_code=400, detail="No generated code found for this conversation")
        
        try:
            # Parse the generated code
            generation_result = json.loads(conversation.generated_code)
            
            print("📝 Converting stored code to proper script for apply_sandbox")
            
            # Check if this is edit/correction format or full script format
            if generation_result.get("e2b_script") and not generation_result.get("files_to_correct"):
                # This is already a full script - use it directly
                print("📝 Using stored full script format")
                if generation_result.get("is_edit"):
                    generation_result["is_edit"] = False
                if generation_result.get("is_correction"):
                    generation_result["is_correction"] = False
            else:
                # This is edit/correction format - convert to proper script
                print("🔧 Converting edit/correction format to proper script")
                
                files_to_correct = generation_result.get("files_to_correct", [])
                new_files = generation_result.get("new_files", [])
                
                # Build a proper script that actually writes the files
                script_lines = []
                script_lines.append("def create_react_app(sandbox):")
                script_lines.append('    """Restore design from stored corrections"""')
                script_lines.append("    print('Restoring stored design...')")
                
                # Add file corrections
                for file_correction in files_to_correct:
                    file_path = file_correction.get("path", "")
                    corrected_content = file_correction.get("corrected_content", "")
                    if file_path and corrected_content:
                        # Properly escape the content for Python
                        escaped_content = corrected_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                        script_lines.append(f'    # Restore {file_path}')
                        script_lines.append(f'    {file_path.replace("/", "_").replace(".", "_")}_content = """{escaped_content}"""')
                        script_lines.append(f'    sandbox.files.write("my-app/{file_path}", {file_path.replace("/", "_").replace(".", "_")}_content)')
                        script_lines.append(f'    print(f"✅ Restored {file_path}")')
                
                # Add new files
                for file_info in new_files:
                    file_path = file_info.get("path", "")
                    content = file_info.get("content", "")
                    if file_path and content:
                        escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                        script_lines.append(f'    # Create new file {file_path}')
                        script_lines.append(f'    {file_path.replace("/", "_").replace(".", "_")}_content = """{escaped_content}"""')
                        script_lines.append(f'    sandbox.files.write("my-app/{file_path}", {file_path.replace("/", "_").replace(".", "_")}_content)')
                        script_lines.append(f'    print(f"✅ Created {file_path}")')
                
                script_lines.append("    print('✅ Design restored successfully')")
                script_lines.append("    return 'Design restored from stored corrections'")
                
                # Create the full script
                full_script = "\n".join(script_lines)
                
                # Update generation_result to use the proper script
                generation_result = {
                    "e2b_script": full_script,
                    "is_correction": False,
                    "is_edit": False
                }
            
            # Create the state object exactly like the normal generation flow
            state = {
                "context": {
                    "generation_result": generation_result
                }
            }
            
            # Apply to sandbox exactly like normal generation
            sandbox_result = apply_sandbox(state)
            
            if sandbox_result and sandbox_result.get('context', {}).get('sandbox_result', {}).get('url'):
                # Get the URL from the result
                url = sandbox_result['context']['sandbox_result']['url']
                # Create unique URL with generation ID
                generation_id = conversation_id[:8]  # Use conversation ID as generation ID
                unique_url = f"{url}?gen_id={generation_id}&restored=true"
                
                return {
                    "success": True,
                    "sandbox_url": unique_url,
                    "conversation_id": conversation_id,
                    "generation_id": generation_id
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create sandbox")
                
        except Exception as e:
            print(f"Error restoring conversation design: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to restore design: {str(e)}")

@app.put("/api/sessions/{session_id}/title")
async def update_session_title(session_id: str, title: str = Form(...)):
    """Update session title"""
    try:
        from db import db_session
        from models import Session
        
        with db_session() as db:
            session = db.get(Session, session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session.title = title
            session.updated_at = datetime.utcnow()
            db.commit()
            
            return {"success": True, "title": title}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating session title: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its associated data"""
    try:
        from db import db_session
        from models import Session, ConversationHistory, SessionGeneratedLinks
        
        with db_session() as db:
            # Delete conversation history
            db.query(ConversationHistory).filter(ConversationHistory.session_id == session_id).delete()
            
            # Delete session generated links
            db.query(SessionGeneratedLinks).filter(SessionGeneratedLinks.session_id == session_id).delete()
            
            # Delete the session itself
            session = db.query(Session).filter(Session.id == session_id).first()
            if session:
                db.delete(session)
                db.commit()
                return {"message": "Session deleted successfully"}
            else:
                return {"error": "Session not found"}, 404
                
    except Exception as e:
        print(f"Error deleting session {session_id}: {e}")
        return {"error": "Failed to delete session"}, 500

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)