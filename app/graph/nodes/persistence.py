from typing import Dict, Any
from app.graph.state import KYCState
from app.db import save_audit_record

def persistence_node(state: KYCState) -> Dict[str, Any]:
    """Takes the structured BaFin report from the state and saves it to Postgres."""
    print("--- 💾 INITIATING DATABASE SAVE ---")

    final_report = state.get("final_report")
    session_id = state.get("session_id", "fallback_session_id")

    if not final_report:
        return {"current_status": "Failed Database Save"}

    try:
        save_audit_record(
            session_id=session_id,
            tenant_id="solaris_bank_demo",
            payload_dict=final_report.model_dump(),
            errors=state.get("error_message", "")
        )
        print(f"✅ Audit record {session_id} successfully committed to database.")
        return {"current_status": "Saved to Database"}

    except Exception as e:
        return {"error_message": str(e), "current_status": "Database Error"}
