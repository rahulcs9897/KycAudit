'''
This file hooks your nodes together. 
Instead of linear paths, you use add_conditional_edges to route execution dynamically based on 
runtime validation telemetry.
Uses a Sync Node to prevent parallel execution race conditions.
'''
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver  # 👈 NEW: Imports the state memory
from app.graph.state import KYCState
from app.graph.nodes import (
    transcribe_audio_node,
    analyze_vision_node,
    generate_bafin_report_node,
    persistence_node
)

def sync_node(state: KYCState):
    """An empty node that forces LangGraph to wait for all parallel streams to finish."""
    return {}

print("--- ⚙️ COMPILING MULTI-STREAM LANGGRAPH WORKFLOW ---")

workflow = StateGraph(KYCState)

workflow.add_node("audio_isolation", transcribe_audio_node)
workflow.add_node("vision_analysis", analyze_vision_node)
workflow.add_node("sync_node", sync_node) 
workflow.add_node("forensic_synthesis", generate_bafin_report_node)
workflow.add_node("database_persistence", persistence_node)

# Fan-Out & Fan-In
workflow.add_edge(START, "audio_isolation")
workflow.add_edge(START, "vision_analysis")
workflow.add_edge("audio_isolation", "sync_node")
workflow.add_edge("vision_analysis", "sync_node")

# Sequential Finish
workflow.add_edge("sync_node", "forensic_synthesis")
workflow.add_edge("forensic_synthesis", "database_persistence")
workflow.add_edge("database_persistence", END)

memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["forensic_synthesis"] # 👈 Pauses execution right before final synthesis!
)