# main.py - Complete version with proper LangSmith integration and logo upload
import os
import uvicorn
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
# Create database tables
Base.metadata.create_all(bind=engine)
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
    Base.metadata.create_all(bind=engine)
    # Verify LangSmith connection
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)