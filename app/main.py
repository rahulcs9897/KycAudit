import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from app.db import initialize_database_infrastructure
from app.graph.workflow import compiled_pipeline
from app.schemas import KYCForensicReport


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler. Automatically sets up our Supabase database
    tables and indices the moment the application boots.
    """
    print("--- 🚀 BOOTING KYC FORENSIC PLATFORM ---")
    try:
        print("Initializing Supabase database infrastructure...")
        initialize_database_infrastructure()
        print("✅ Database infrastructure successfully synced.")
    except Exception as e:
        print(f"❌ Critical Database Initialization Error: {str(e)}")
        print("Ensure your DATABASE_URL in .env is correct.")
    yield
    print("--- 🛑 SHUTTING DOWN KYC FORENSIC PLATFORM ---")

app = FastAPI(
    title="KYC Forensic Audit & Multi-Stream RAG Engine",
    version="1.0.0",
    lifespan=lifespan
)

# API Request contract
class AuditRequest(BaseModel):
    session_id: str
    video_file_path: str  # Local path or simulated file endpoint

def execute_async_graph(session_id: str, video_path: str):
    """Asynchronous background task to execute our state graph without
blocking the API."""
    print(f"--- 🌀 STARTING ASYNC GRAPH WORKFLOW FOR SESSION: {session_id} ---")

    # Standard input payload matching the fields inside KYCState
    initial_inputs = {
        "session_id": session_id,
        "video_file_path": video_path,
        "isolated_audio_path": r"E:\Agents\Project-KycForensic-RAG\mockdata\test.mp4",
        "transcript": None,
        "extracted_frame_paths": [],
        "detected_anomalies": [],
        "final_report": None,
        "current_status": "Initialized",
        "error_message": None
    }

    # Thread configuration required by LangGraph checkpointer (MemorySaver)
    config = {"configurable": {"thread_id": session_id}}

    try:
        # Launch the compilation engine
        final_state = compiled_pipeline.invoke(initial_inputs, config=config)
        print(f"--- 🏁 GRAPH COMPLETE FOR SESSION {session_id}.Status: {final_state.get('current_status')} ---")
    except Exception as e:
        print(f"❌ Graph Execution Fatal Crash: {str(e)}")

@app.post("/api/v1/audit", status_code=202)
async def trigger_forensic_audit(request: AuditRequest,
background_tasks: BackgroundTasks):
    """
    Fintech Production Standard Gateway:
    Receives request, schedules a background processor worker task,
and immediately
    returns a '202 Accepted' response to ensure zero network timeout drops.
    """
    if not request.session_id or not request.video_file_path:
        raise HTTPException(status_code=400, detail="Missing required attributes session_id or video_file_path")

    # Queue up the LangGraph execution to a background worker thread
    background_tasks.add_task(execute_async_graph, request.session_id,
request.video_file_path)

    return {
        "status": "Accepted",
        "message": "Forensic audit initiated successfully in background task thread.",
        "session_id": request.session_id
    }

@app.get("/health")
async def health_check():
    """Simple health node monitoring."""
    return {"status": "healthy", "database_connected":
os.getenv("DATABASE_URL") is not None}