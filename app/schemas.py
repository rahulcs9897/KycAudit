"""
LLMs are inherently unpredictable text generators.
Even if you explicitly tell an LLM to output JSON, it might wrap it in markdown code blocks (e.g., json ... ), misspell a key, or 
return a string instead of an integer.

In a production environment, if you pass malformed data to your Postgres/Qdrant database, the entire system crashes. 
Pydantic is our Guardrail. It forces the data to conform to a strict, typed structure. 
If the LLM breaks the rules, Pydantic catches it immediately so we can retry the generation.
"""

from pydantic import BaseModel, Field 
# BaseModel: foundation of all Pydantic schemas
# field: lets us add constraints and descriptions
from typing import List, Literal

class KYCForensicReport(BaseModel):
    """
    Strict validation schema for the final KYC Forensic output.
    Enforces the exact BaFin-compliant JSON structure.
    """
    
    risk_score: int = Field(
        ..., 
        ge=0, 
        le=100, 
        description="The calculated risk score from 0 to 100."
    )
    # enforce that the LLM must return an integer between 0 and 100.
    
    decision: Literal["APPROVED", "REJECTED", "ESCALATED"] = Field(
        ..., 
        description="The final routing decision based on the risk score."
    )
    
    document_integrity_findings: str = Field(
        ..., 
        description="Detailed findings regarding ID card/document tampering or visual inconsistencies."
    )
    
    liveness_biometric_findings: str = Field(
        ..., 
        description="Details on liveness checks, deepfake indicators, or presentation attacks."
    )
    
    behavioral_isolation_findings: str = Field(
        ..., 
        description="Details on suspicious behavior, potential coercion, or third-party voices detected."
    )
    
    timestamps: List[str] = Field(
        default_factory=list, 
        description="List of timestamps highlighting suspicious activity in 'MM:SS - flag description' format."
    )