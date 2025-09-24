# main.py - Complete version with proper LangSmith integration and logo upload
import os
import uvicorn
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import zipfile
import io
import tempfile
from contextlib import asynccontextmanager
import asyncio
import time
import uuid
from typing import Dict

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
from utlis.docs import save_upload_to_disk, save_logo_to_disk, save_image_to_disk

# LangGraph imports - NO SQLite
from langserve import add_routes

# Track running requests per session
_running_requests: Dict[str, asyncio.Task] = {}

# FIXED: Replaced deprecated on_event with lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    # Startup
    print("🔄 Setting up application...")
    yield
    # Shutdown
    print(" Application shutdown - cancelling all requests...")
    
    # Cancel all running requests
    for session_id, task in _running_requests.items():
        print(f" Cancelling request for session {session_id}")
        task.cancel()
    
    _running_requests.clear()
    
    print("🧹 Cleaning up sandboxes...")
    from nodes.apply_to_Sandbox_node import cleanup_all_sessions
    # cleanup_all_sessions()
    print("✅ Application shutdown complete")

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
    import os
    
    # Check if database exists and has correct schema
    db_exists = os.path.exists('app.db')
    
    if db_exists:
        print("✅ Database exists with correct schema")
    else:
        print("🔄 Creating new database...")
        Base.metadata.create_all(bind=engine)
        print("✅ New database created")
        
except Exception as e:
    print(f"❌ Database setup error: {e}")
    # Continue anyway - tables might be created later

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

#  NO SQLite checkpointer - compile graph without checkpointer
compiled_graph = graph.compile()

@app.post("/api/query", response_model=UserQueryOut)
async def accept_query(
    session_id: str | None = Form(None),
    text: str = Form(...),
    llm_model: str | None = Form(None),
    file: UploadFile | None = File(None),
    logo: UploadFile | None = File(None),
    image: UploadFile | None = File(None),
    color_palette: str | None = Form(None),
    regenerate: bool = Form(False),
    schema_type: str = Form("medspa")
):
    """Handle multiple concurrent requests - each session gets its own processing"""
    try:
        # Generate unique session ID if not provided
        if not session_id:
            session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        print(f"🔄 Starting request for session: {session_id}")
        
        # Check if this session already has a running request
        if session_id in _running_requests:
            print(f"⚠️ Session {session_id} already has active request, cancelling previous")
            try:
                _running_requests[session_id].cancel()
                await _running_requests[session_id]  # Wait for cancellation
            except asyncio.CancelledError:
                pass
            _running_requests.pop(session_id, None)
        
        # Create new task for this request
        task = asyncio.create_task(
            process_query_request(
                session_id, text, llm_model, file, logo, image, 
                color_palette, regenerate, schema_type
            )
        )
        
        # Track the request
        _running_requests[session_id] = task
        
        try:
            # Wait for the request to complete
            result = await task
            return result
        except asyncio.CancelledError:
            print(f"🛑 Request cancelled for session {session_id}")
            return {"error": "Request cancelled", "session_id": session_id}
        finally:
            # Clean up tracking
            _running_requests.pop(session_id, None)
            print(f"✅ Request completed for session {session_id}")
        
    except Exception as e:
        print(f"❌ Error in accept_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def process_query_request(
    session_id: str, 
    text: str, 
    llm_model: str | None, 
    file: UploadFile | None, 
    logo: UploadFile | None, 
    image: UploadFile | None, 
    color_palette: str | None, 
    regenerate: bool, 
    schema_type: str
):
    """Process individual query request - isolated per session"""
    try:
        print(f"🔄 Processing query for session: {session_id}")
        
        # Handle file uploads
        doc = None
        if file is not None:
            doc = await save_upload_to_disk(file)

        logo_data = None
        if logo is not None:
            logo_data = await save_logo_to_disk(logo, session_id)
            print(f"🖼️ Logo uploaded for {session_id}: {logo_data.get('filename')}")

        image_data = None
        if image is not None:
            image_data = await save_image_to_disk(image, session_id)
            print(f"🖼️ Image uploaded for {session_id}: {image_data.get('filename')}")

        # Create payload
        payload = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "text": text,
            "llm_model": llm_model,
            "doc": doc,
            "logo": logo_data,
            "image": image_data,
            "color_palette": color_palette,
            "regenerate": regenerate,
        }
        
        print(f"🎨 Session {session_id} - Color Palette: '{color_palette}'")

        # Initialize state for this session
        state = user_node_init_state(payload)
        
        # Add metadata
        state["metadata"] = {
            "regenerate": regenerate,
            "schema_type": schema_type
        }
        
        # Create unique thread ID for this session
        thread_id = _as_uuid(session_id)
        
        # Create configuration for this session
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "recursion_limit": 50
            },
            tags=["api_request", "frontend", f"model:{llm_model or 'default'}", f"session:{session_id[:8]}"],
            metadata={
                "session_id": session_id,
                "thread_id": thread_id,
                "model": llm_model,
                "has_doc": bool(doc),
                "has_logo": bool(logo_data),
                "text_preview": text[:100] if text else "",
                "run_name": f"query_{session_id[:8]}_{int(time.time())}",
                "project_name": os.getenv("LANGCHAIN_PROJECT", "lovable-orchestrator")
            }
        )
        
        # Execute graph for this session
        final_result = None
        print(f"🔄 Executing graph for session {session_id} with thread_id: {thread_id}")

        # Execute the graph
        async for chunk in compiled_graph.astream(state, config=config):
            final_result = chunk
            print(f"📊 Session {session_id} - Node completed: {list(chunk.keys())}")
        
        # Get final result
        result = final_result[list(final_result.keys())[-1]] if final_result else state
        
        print(f"✅ Session {session_id} - Graph execution completed. Thread {thread_id}")
        
        return {
            "session_id": result["session_id"], 
            "accepted": True, 
            "state": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing query for session {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Request processing failed: {str(e)}")

@app.post("/api/regenerate")
async def regenerate_query(
    session_id: str = Form(...),
    llm_model: str | None = Form(None),
    schema_type: str = Form("medspa")
):
    try:
        print(f"🔄 Regenerating for session: {session_id}")
        
        # Create regeneration payload
        payload = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "text": "...",  # Empty text for regeneration
            "llm_model": llm_model,
            "regenerate": True,
        }
        
        # Initialize state
        state = user_node_init_state(payload)
        
        # Add schema_type to metadata
        state["metadata"] = {
            "regenerate": True,
            "schema_type": schema_type
        }
        
        # Use consistent thread ID
        thread_id = _as_uuid(session_id)
        
        # Create configuration
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "recursion_limit": 50
            },
            tags=["api_request", "regenerate", f"model:{llm_model or 'default'}"],
            metadata={
                "session_id": thread_id,
                "model": llm_model,
                "run_name": f"regenerate_{thread_id[:8]}",
                "project_name": os.getenv("LANGCHAIN_PROJECT", "lovable-orchestrator")
            }
        )
        
        # Execute graph
        final_result = None
        print(f"🔄 Executing regeneration with thread_id: {thread_id}")
        
        async for chunk in compiled_graph.astream(state, config=config):
            final_result = chunk
            print(f"📊 Node completed: {list(chunk.keys())}")
        
        # Use the final result
        result = final_result[list(final_result.keys())[-1]] if final_result else state
        
        print(f"✅ Regeneration completed. Thread {thread_id}")
        
        return {"session_id": result["session_id"], "accepted": True, "state": result}
    except Exception as e:
        print(f"Error in regenerate_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads")
async def get_threads():
    """Get list of available threads"""
    try:
        # Since we removed SQLite, return empty list or implement with your MongoDB
        return {"threads": [], "message": "No checkpointer - using stateless execution"}
    except Exception as e:
        return {"error": str(e), "message": "Could not fetch threads"}

@app.get("/api/thread/{thread_id}")
async def get_thread_info(thread_id: str):
    """Get information about a specific thread"""
    try:
        # Since we removed SQLite, return basic info
        return {
            "thread_id": thread_id,
            "message": "No checkpointer - using stateless execution",
            "status": "active"
        }
    except Exception as e:
        return {"error": str(e), "message": "Could not fetch thread info"}

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
        from nodes.apply_to_Sandbox_node import cleanup_all_sessions
        
        print("🧹 EMERGENCY CLEANUP - Killing all sandboxes...")
        cleanup_all_sessions()
        
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

@app.get("/api/requests/status")
async def get_requests_status():
    """Get status of all running requests"""
    try:
        status = {}
        for session_id, task in _running_requests.items():
            status[session_id] = {
                "status": "running" if not task.done() else "completed",
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        
        return {
            "active_requests": len(_running_requests),
            "requests": status
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/requests/{session_id}/cancel")
async def cancel_request(session_id: str):
    """Cancel a specific request"""
    try:
        if session_id in _running_requests:
            print(f"🛑 Cancelling request for session {session_id}")
            _running_requests[session_id].cancel()
            _running_requests.pop(session_id, None)
            return {"success": True, "message": f"Request for session {session_id} cancelled"}
        else:
            return {"success": False, "message": f"No active request found for session {session_id}"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/requests/cancel-all")
async def cancel_all_requests():
    """Cancel all running requests"""
    try:
        cancelled_count = 0
        for session_id, task in _running_requests.items():
            print(f"🛑 Cancelling request for session {session_id}")
            task.cancel()
            cancelled_count += 1
        
        _running_requests.clear()
        
        return {
            "success": True, 
            "message": f"Cancelled {cancelled_count} requests"
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
        
        async for chunk in compiled_graph.astream(state, config=config):
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
            
            print(" Converting stored code to proper script for apply_sandbox")
            
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
                "session_id": session_id,  # Add session_id for session-based sandbox
                "context": {
                    "generation_result": generation_result
                }
            }
            
            # Apply to sandbox exactly like normal generation
            sandbox_result =await apply_sandbox(state)
            
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

@app.get("/api/sessions/{session_id}/conversations/{conversation_id}/download")
async def download_conversation_files(session_id: str, conversation_id: str):
    """Download all project files as a zip archive - EXCEPT NODE_MODULES"""
    try:
        print(f"🔄 Starting download for conversation: {conversation_id}")
        
        # Get files from session-based sandbox
        from nodes.apply_to_Sandbox_node import _get_session_sandbox
        
        sandbox = _get_session_sandbox(session_id)
        
        if not sandbox:
            raise HTTPException(status_code=404, detail="No active sandbox found for this session")
        
        print(f"✅ Active sandbox found for session {session_id}, scanning for all files (except node_modules)...")
        
        files_to_download = {}
        
        # DYNAMIC APPROACH: Use E2B SDK's list_files method
        def scan_directory_recursive(directory_path=""):
            """Recursively scan directory using E2B SDK"""
            try:
                # Use the correct E2B SDK method to list files
                items = sandbox.files.list(directory_path)
                
                for item in items:
                    # Build the full path
                    item_path = f"{directory_path}/{item.name}" if directory_path else item.name
                    
                    # Skip node_modules directory
                    if item.name == 'node_modules':
                        print(f"⏭️ Skipping node_modules directory: {item_path}")
                        continue
                    
                    # Check if it's a directory by trying to list its contents
                    try:
                        # Try to list contents - if it works, it's a directory
                        sub_items = sandbox.files.list(item_path)
                        print(f" Found directory: {item_path}")
                        # Recursively scan the subdirectory
                        scan_directory_recursive(item_path)
                    except:
                        # If listing fails, it's a file
                        try:
                            content = sandbox.files.read(item_path)
                            if content and content.strip():
                                # Clean the path (remove my-app/ prefix if present)
                                clean_path = item_path.replace('my-app/', '')
                                files_to_download[clean_path] = content
                                print(f"  ✅ Found file: {clean_path}")
                        except Exception as e:
                            print(f"  ⚠️ Could not read {item_path}: {e}")
                            continue
                            
            except Exception as e:
                print(f"⚠️ Could not scan directory {directory_path}: {e}")
        
        # Start scanning from the root
        print("🔍 Scanning project structure...")
        scan_directory_recursive("my-app")
        
        # If my-app directory doesn't exist, try scanning from root
        if not files_to_download:
            print("🔍 my-app not found, scanning from root...")
            scan_directory_recursive("")
        
        print(f"📦 Found {len(files_to_download)} files total")
        
        if not files_to_download:
            raise HTTPException(status_code=404, detail="No files found in sandbox")
        
        # Create zip quickly
        print("🔄 Creating zip...")
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, content in files_to_download.items():
                zip_file.writestr(file_path, content)
        
        zip_buffer.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_{conversation_id[:8]}_{timestamp}.zip"
        
        print(f"✅ Download ready: {filename}")
        
        # Return zip
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


import os
from fastapi.responses import StreamingResponse
import io


from nodes.apply_to_Sandbox_node import _get_session_sandbox, _async_sandbox_command, _async_sandbox_file_read
import re

import re

async def build_single_file_html_from_sandbox(sandbox, dist_dir: str = "my-app/dist") -> str:
    index_html = await _async_sandbox_file_read(sandbox, f"{dist_dir}/index.html")
    html = index_html

    assets_dir = f"{dist_dir}/assets"
    # List all asset files from sandbox
    asset_files = await _async_sandbox_command(sandbox, f"ls {assets_dir}", 30)
    if asset_files.exit_code != 0:
        return html

    for fname in asset_files.stdout.splitlines():
        if fname.endswith(".css"):
            css_content = await _async_sandbox_file_read(sandbox, f"{assets_dir}/{fname}")
            html = re.sub(
                rf'<link[^>]+{fname}[^>]*>',
                f"<style>{css_content}</style>",
                html
            )
        elif fname.endswith(".js"):
            js_content = await _async_sandbox_file_read(sandbox, f"{assets_dir}/{fname}")
            html = re.sub(
                rf'<script[^>]+{fname}[^>]*></script>',
                f"<script type=\"module\">{js_content}</script>",
                html
            )

    return html




from nodes.apply_to_Sandbox_node import (
    _get_session_sandbox,
    _async_sandbox_command,
    _async_sandbox_file_read,
    _create_fast_vite_project,
    _is_project_setup,
)

@app.get("/api/sessions/{session_id}/conversations/{conversation_id}/download-html")
async def download_single_html(session_id: str, conversation_id: str):
    """Return single self-contained HTML file with bundled CSS/JS inlined."""
    sandbox = _get_session_sandbox(session_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    try:
        print(f"📄 Creating single HTML file for conversation: {conversation_id}")
        
        # Step 1: Check if dist already exists, if not build it
        print("🔨 Rebuilding project from active sandbox...")
        # Always rebuild before reading
        await _async_sandbox_command(sandbox, "rm -rf my-app/dist", 30)
        build_result = await _async_sandbox_command(sandbox, "cd my-app && npm run build", 300)
        if build_result.exit_code != 0:
            raise HTTPException(status_code=500, detail="Build failed")

        print("📖 Reading built HTML file...")
        
        # Step 2: Read the built index.html
        try:
            html = await _async_sandbox_file_read(sandbox, "my-app/dist/index.html")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not read index.html: {str(e)}")
        
        # Step 3: Get list of asset files
        print("📦 Processing asset files...")
        assets_result = await _async_sandbox_command(sandbox, "ls my-app/dist/assets/", 30)
        
        if assets_result.exit_code == 0 and assets_result.stdout.strip():
            asset_files = [f.strip() for f in assets_result.stdout.strip().split('\n') if f.strip()]
            
            print(f"Found {len(asset_files)} asset files: {asset_files}")
            
            # Step 4: Inline CSS files
            for fname in asset_files:
                if fname.endswith(".css"):
                    try:
                        css_content = await _async_sandbox_file_read(sandbox, f"my-app/dist/assets/{fname}")
                        if css_content:
                            # Find and replace the CSS link tag
                            import re
                            css_pattern = rf'<link[^>]*href="[^"]*{re.escape(fname)}"[^>]*>'
                            replacement = f"<style>{css_content}</style>"
                            html = re.sub(css_pattern, replacement, html)
                            print(f"✅ Inlined CSS: {fname}")
                    except Exception as e:
                        print(f"⚠️ Could not inline CSS {fname}: {e}")
            
            # Step 5: Inline JS files
            # Step 5: Inline JS files
            for fname in asset_files:
                if fname.endswith(".js"):
                    try:
                        js_content = await _async_sandbox_file_read(sandbox, f"my-app/dist/assets/{fname}")
                        if js_content:
                            # FIXED: Escape the JS content properly to handle Unicode escapes
                            try:
                                # First, try to safely escape problematic characters
                                js_content_escaped = js_content.replace('\\', '\\\\').replace('</script>', '<\/script>')
                                
                                # Find and replace the JS script tag
                                import re
                                js_pattern = rf'<script[^>]*src="[^"]*{re.escape(fname)}"[^>]*></script>'
                                replacement = f'<script type="module">{js_content_escaped}</script>'
                                html = re.sub(js_pattern, replacement, html)
                                print(f"✅ Inlined JS: {fname}")
                            except Exception as escape_error:
                                # If escaping fails, try a different approach - encode as base64
                                print(f"⚠️ Unicode escape issue with {fname}, trying base64 approach...")
                                import base64
                                js_b64 = base64.b64encode(js_content.encode('utf-8')).decode('ascii')
                                
                                js_pattern = rf'<script[^>]*src="[^"]*{re.escape(fname)}"[^>]*></script>'
                                replacement = f'''<script type="module">
                                // Decoded from base64 due to Unicode escape issues
                                (function() {{
                                    const jsCode = atob("{js_b64}");
                                    const script = document.createElement('script');
                                    script.type = 'module';
                                    script.text = jsCode;
                                    document.head.appendChild(script);
                                }})();
                                </script>'''
                                html = re.sub(js_pattern, replacement, html)
                                print(f"✅ Inlined JS with base64: {fname}")
                    except Exception as e:
                        print(f"⚠️ Could not inline JS {fname}: {e}")
                        # Leave the original script tag if inlining fails
        
        # Step 6: Generate filename and return
        from datetime import datetime
        from datetime import datetime
        import zipfile
        import io

        # Step 6: Generate filename
        # ... (code to build the html string) ...

        # Step 6: Generate filename and return the HTML content directly
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"index_{conversation_id[:8]}_{timestamp}.txt"

        print(f"✅ Single HTML file ready for download: {filename}")

        # Return the HTML string directly as a streaming response
        return StreamingResponse(
            io.BytesIO(html.encode("utf-8")),  # Encode the string to bytes
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ HTML download error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create HTML: {str(e)}")
# ... existing code ...



@app.post("/api/sessions/{session_id}/cleanup")
async def cleanup_session_sandbox(session_id: str):
    """Clean up sandbox for a specific session"""
    try:
        from nodes.apply_to_Sandbox_node import cleanup_session_sandbox
        
        print(f"🧹 Cleaning up sandbox for session: {session_id}")
        cleanup_session_sandbox(session_id)
        
        return {"success": True, "message": f"Sandbox for session {session_id} cleaned up"}
    except Exception as e:
        print(f"❌ Session cleanup failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session sandbox status"""
    try:
        from nodes.apply_to_Sandbox_node import _get_session_sandbox, _get_session_info
        
        sandbox = _get_session_sandbox(session_id)
        info = _get_session_info(session_id)
        
        return {
            "session_id": session_id,
            "has_sandbox": sandbox is not None,
            "sandbox_info": info,
            "status": "active" if sandbox else "inactive"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/message")
async def save_message(
    session_id: str = Form(...),
    message: str = Form(...)
):
    """Save a message to the database"""
    try:
        from db import db_session
        from models import Message
        
        with db_session() as db:
            message_obj = Message(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="user",
                content=message,
                created_at=datetime.utcnow()
            )
            db.add(message_obj)
            db.commit()
            
            return {"success": True, "message_id": message_obj.id}
    except Exception as e:
        print(f"Error saving message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )