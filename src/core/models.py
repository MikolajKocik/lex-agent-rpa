from pydantic import BaseModel, Field

class GroundReviewResponse(BaseModel):
    """Model response for the initial verification and reading node (Ground Review)"""
    extracted_clauses: list[str] = Field(
        default_factory=list,
        description="List of key clauses extracted from the document"
    )
    identified_risks: list[str] = Field(
        default_factory=list,
        description="List of potential business and legal risks"
    )

class SecurityLexResponse(BaseModel):
    """Model response assessing data security and PII"""
    pii_entities_found: list[str] = Field(
        default_factory=list,
        description="List of sensitive data/entities found (PII)"
    )
    is_safe: bool = Field(description="True if the document is safe to process, False if it has critical data leaks")

class CriticAnalyzeResponse(BaseModel):
    """Model response acting as a critical lawyer"""
    legal_opinion: str = Field(description="Detailed legal opinion based on the review and security audit")
    pii_summary: str = Field(description="Summary of the personally identifiable information (PII) found during the security audit")

class RpaActionResponse(BaseModel):
    """Model specifying which physical RPA actions (e.g. download/save) the system should perform"""
    actions_completed: list[str] = Field(
        default_factory=list,
        description="List of planned or executed automation steps"
    )
    final_report_path: str | None = Field(
        default=None,
        description="Path to the generated report"
    )
