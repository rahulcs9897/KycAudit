from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph.state import KYCState
from app.schemas import KYCForensicReport

# Dedicated client for JSON Synthesis
synthesis_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)

def generate_bafin_report_node(state: KYCState) -> Dict[str, Any]:
    """Uses Llama 3.3 with structured output to generate strict BaFin JSON."""
    structured_llm = synthesis_llm.with_structured_output(KYCForensicReport)

    system_prompt = SystemMessage(content="""
        SYSTEM ROLE: You are an elite KYC/AML Compliance Auditor
operating under BaFin regulations.
        Evaluate the provided transcript and visual anomalies.
        Determine a risk score (0-100) and an exact decision
(APPROVED, REJECTED, ESCALATED).
    """)

    human_prompt = HumanMessage(content=f"""
        Transcript: {state.get('transcript', 'None')}
        Vision Anomalies: {state.get('detected_anomalies', [])}
    """)

    report = structured_llm.invoke([system_prompt, human_prompt])

    return {"final_report": report, "current_status": "Report Generated"}
