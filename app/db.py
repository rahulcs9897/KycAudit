import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_db_connection():
    """Context manager ensuring transaction atomic safety and pooling protection."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize_database_infrastructure():
    """Initializes schema targets matching compliance recording requirements."""
    schema_query = """
    CREATE TABLE IF NOT EXISTS kyc_forensic_audits (
        session_id VARCHAR(64) PRIMARY KEY,
        tenant_id VARCHAR(64) NOT NULL,
        risk_score INT NOT NULL,
        decision VARCHAR(20) NOT NULL,
        document_integrity_findings TEXT,
        liveness_biometric_findings TEXT,
        behavioral_isolation_findings TEXT,
        timestamps JSONB,
        execution_errors TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_kyc_tenant ON kyc_forensic_audits(tenant_id);
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(schema_query)

def save_audit_record(session_id: str, tenant_id: str, payload_dict: dict, errors: str = ""):
    """Inserts compiled runtime results natively utilizing structured execution."""
    insert_query = """
    INSERT INTO kyc_forensic_audits (
        session_id, tenant_id, risk_score, decision, 
        document_integrity_findings, liveness_biometric_findings, 
        behavioral_isolation_findings, timestamps, execution_errors
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (session_id) DO UPDATE SET
        risk_score = EXCLUDED.risk_score,
        decision = EXCLUDED.decision,
        execution_errors = EXCLUDED.execution_errors;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(insert_query, (
                session_id,
                tenant_id,
                payload_dict.get("risk_score", 100 if errors else 0),
                payload_dict.get("decision", "ESCALATED" if errors else "REJECTED"),
                payload_dict.get("document_integrity_findings", ""),
                payload_dict.get("liveness_biometric_findings", ""),
                payload_dict.get("behavioral_isolation_findings", ""),
                json.dumps(payload_dict.get("timestamps", [])),
                errors
            ))