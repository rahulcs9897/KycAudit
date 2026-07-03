import operator
from typing import TypedDict, Annotated, List, Optional
from app.schemas import KYCForensicReport

class KYCState(TypedDict):
    """
    In a traditional backend, you might pass variables from one function to another sequentially.
    But in an AI workflow, tasks can fail, loop, or run in parallel.
    LangGraph solves this by passing a single State object (defined using Python's TypedDict) between every node.
    The state object that LangGraph passes between AI nodes.
    This acts as the stateful memory engine for our KYC Forensic pipeline.
    """
    
    # --- 1. Inputs ---
    session_id: str
    video_file_path: str
    
    # --- 2. Intermediate Processing Data ---
    isolated_audio_path: Optional[str]
    transcript: Optional[str]
    extracted_frame_paths: List[str]
    
    # --- 3. Accumulating State ---
    # The 'Annotated' type with 'operator.add' tells LangGraph to append to this list 
    # rather than overwriting it if multiple nodes detect anomalies simultaneously.
    detected_anomalies: Annotated[List[str], operator.add]
    
    # --- 4. Final Output ---
    final_report: Optional[KYCForensicReport]
    
    # --- 5. Control Flow ---
    current_status: str
    error_message: Optional[str]