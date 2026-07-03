import os
import sys
import streamlit as st
import tempfile
from dotenv import load_dotenv

# Force Python to see the project root
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
load_dotenv()
from app.graph.workflow import app as kyc_graph

st.set_page_config(page_title="KYC Forensic Engine", layout="centered")
st.title("KYC Forensic Audit")

# --- 🚦 SESSION STATE MANAGEMENT ---
# We use this to track which phase of the audit we are in
if "thread_id" not in st.session_state:
    st.session_state.thread_id = os.urandom(3).hex()
if "app_phase" not in st.session_state:
    st.session_state.app_phase = "UPLOAD"

# The LangGraph configuration required to track the paused memory
config = {"configurable": {"thread_id": st.session_state.thread_id}}


# ==========================================
# PHASE 1: UPLOAD & INGESTION
# ==========================================
if st.session_state.app_phase == "UPLOAD":
    st.markdown("""
    **To ensure a successful verification, your video must meet these strict criteria:**
    * ✅ **Valid ID:** Hold a Government-Issued ID (Passport, National ID, or Driver's License).
    * ✅ **Legibility:** Your Name and Date of Birth must be clearly visible.
    * ✅ **Clear Audio:** Speak clearly. Background voices will trigger a behavioral anomaly.
    """)
    st.markdown("---")

    uploaded_file = st.file_uploader("Upload video recording (.mp4)", type=["mp4"])

    if uploaded_file is not None:
        st.markdown("---")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(uploaded_file.read())
            temp_video_path = temp_video.name
            
        with st.spinner("Executing Audio & Vision AI Pipeline..."):
            initial_state = {
                "session_id": f"web_session_{st.session_state.thread_id}",
                "video_file_path": temp_video_path,
                "detected_anomalies": [],
                "expected_name": "John Doe", 
                "expected_dob": "01.01.1990" 
            }
            
            # This will run the graph until it hits the interrupt!
            kyc_graph.invoke(initial_state, config=config)
            
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            
        # Move to the review phase
        st.session_state.app_phase = "REVIEW"
        st.rerun()


# ==========================================
# PHASE 2: HUMAN-IN-THE-LOOP (HITL) REVIEW
# ==========================================
elif st.session_state.app_phase == "REVIEW":
    st.warning("⚠️ AI Pipeline Paused. Human Auditor Intervention Required.")
    st.markdown("---")
    
    # Grab the current frozen state from LangGraph memory
    current_state = kyc_graph.get_state(config).values
    anomalies = current_state.get("detected_anomalies", [])
    
    st.subheader("🤖 AI Forensic Findings")
    if anomalies:
        for flag in anomalies:
            st.error(flag)
    else:
        st.success("AI found no visual or document anomalies. CLEAR.")
        
    st.markdown("---")
    st.subheader("👨‍⚖️ Auditor Decision")
    st.write("Please override or confirm the AI's findings to generate the final BaFin report.")
    
    col1, col2 = st.columns(2)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve Session"):
            # 🛑 FIX: Only update with the NEW item, do not pass the entire list back
            new_override = ["HUMAN AUDITOR OVERRIDE: Session Approved by Compliance Officer."]
            kyc_graph.update_state(config, {"detected_anomalies": new_override})
            
            with st.spinner("Synthesizing Final Approved Report..."):
                kyc_graph.invoke(None, config=config)
                
            st.session_state.app_phase = "COMPLETE"
            st.rerun()
            
    with col2:
        if st.button("🚨 Reject Session"):
            # 🛑 FIX: Only update with the NEW item, do not pass the entire list back
            new_override = ["HUMAN AUDITOR OVERRIDE: Session Manually Rejected."]
            kyc_graph.update_state(config, {"detected_anomalies": new_override})
            
            with st.spinner("Synthesizing Final Rejected Report..."):
                kyc_graph.invoke(None, config=config)
                
            st.session_state.app_phase = "COMPLETE"
            st.rerun()

# ==========================================
# PHASE 3: FINAL SYNTHESIS & REPORT
# ==========================================
elif st.session_state.app_phase == "COMPLETE":
    st.subheader("Results")
    
    # Grab the completed state
    final_state = kyc_graph.get_state(config).values
    report = final_state.get("final_report")
    
    if report:
        if report.decision.upper() == "APPROVED":
            st.success(f"Final Result: {report.decision} (Score: {report.risk_score})")
        else:
            st.error(f"Final Result: {report.decision} (Score: {report.risk_score})")
            
        st.write("")
        st.write(f"**Identity Card:** {report.document_integrity_findings}")
        st.write(f"**Video:** {report.liveness_biometric_findings}")
        st.write(f"**Audio:** {report.behavioral_isolation_findings}")
    else:
        st.error("Error: Failed to synthesize the compliance report.")
        
    st.markdown("---")
    if st.button("🔄 Start New Audit"):
        # Reset the session to start fresh
        st.session_state.thread_id = os.urandom(3).hex()
        st.session_state.app_phase = "UPLOAD"
        st.rerun()