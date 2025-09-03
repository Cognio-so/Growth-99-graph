# main.py - Complete version with proper LangSmith integration
import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
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
from utlis.docs import save_upload_to_disk

# LangGraph imports
from langgraph.checkpoint.memory import MemorySaver
from langserve import add_routes

app = FastAPI(title="Lovable-like Orchestrator", version="0.5.0")

# Update CORS to allow your Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Local Vite
        "https://growth-99-graph.vercel.app",  # Your Vercel domain
        "https://*.vercel.app",  # All Vercel subdomains
        "*"  # Allow all origins (for testing, remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from uuid import UUID, uuid4

def _as_uuid(s: str | None) -> str:
    try:
        UUID(str(s))
        return str(s)
    except Exception:
        return str(uuid4())
        
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

# Create checkpointer for state persistence
memory = MemorySaver()

# Compile the graph with checkpointer (REMOVE any recursion_limit here)
compiled_graph = graph.compile(checkpointer=memory)

@app.post("/api/query", response_model=UserQueryOut)
async def accept_query(
    session_id: str | None = Form(None),
    text: str = Form(...),
    llm_model: str | None = Form(None),
    file: UploadFile | None = File(None),
    regenerate: bool = Form(False),
):
    try:
        doc = None
        if file is not None:
            doc = await save_upload_to_disk(file)

        payload = {
            "session_id": session_id or None,
            "timestamp": datetime.utcnow().isoformat(),
            "text": text,
            "llm_model": llm_model,
            "doc": doc,
            "regenerate": regenerate,
        }

        # Initialize state
        state = user_node_init_state(payload)
        
        # Create configuration with tracing metadata AND recursion limit
        thread_id = _as_uuid(state.get("session_id"))
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "recursion_limit": 50  # INCREASED from 25 to 50
            },
            tags=["api_request", "frontend", f"model:{llm_model or 'default'}"],
            metadata={
                "session_id": thread_id,
                "model": llm_model,
                "has_doc": bool(doc),
                "text_preview": text[:100] if text else ""
            }
        )
        
        # Run the graph with configuration
        result = compiled_graph.invoke(state, config=config)
        
        return {"session_id": result["session_id"], "accepted": True, "state": result}
    except Exception as e:
        print(f"Error in accept_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
# LangGraph playground endpoints
add_routes(app, compiled_graph, path="/graph")

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)