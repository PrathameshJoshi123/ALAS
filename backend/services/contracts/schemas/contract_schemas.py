"""
Pydantic schemas for Contract Service requests and responses
Following the same pattern as Auth Service schemas
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class ContractStatusEnum(str, Enum):
    """Contract lifecycle statuses"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ANALYSIS_FAILED = "analysis_failed"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive enum lookups and stale enum references"""
        if isinstance(value, str):
            # Try case-insensitive match
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class ClauseSeverityEnum(str, Enum):
    """Risk severity levels for contract clauses"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ==================== REQUEST SCHEMAS ====================

class ContractUploadRequest(BaseModel):
    """Schema for contract upload initiation"""
    counterparty_name: Optional[str] = Field(None, max_length=255, description="Third-party entity name")
    contract_type: Optional[str] = Field(None, max_length=100, description="e.g., NDA, Service Agreement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "counterparty_name": "Acme Corporation",
                "contract_type": "Service Level Agreement"
            }
        }


# ==================== RESPONSE SCHEMAS ====================

class SourceCitation(BaseModel):
    """Schema for legal source citations (statute references)"""
    title: str = Field(..., description="Title of the statute or legal reference")
    url: str = Field(..., description="URL to the full statute text (e.g., indiacode.nic.in)")
    body: Optional[str] = Field(None, description="Excerpt from the statute relevant to the clause")
    section: Optional[str] = Field(None, description="Specific statute section cited (e.g., 'Section 37')")


class ClauseResponse(BaseModel):
    """Schema for individual clause response"""
    id: UUID
    clause_number: int
    clause_type: Optional[str]
    section_title: Optional[str]
    raw_text: str
    severity: ClauseSeverityEnum
    risk_description: Optional[str]
    legal_reasoning: Optional[str]
    confidence_score: int
    is_standard: bool
    is_missing_mandatory: bool
    is_jurisdiction_mismatch: bool
    applicable_statute: Optional[str]
    statute_section: Optional[str]
    sources: Optional[List[SourceCitation]] = Field(None, description="Statute references and legal sources")
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "clause_number": 1,
                "clause_type": "Indemnity",
                "section_title": "Liability and Indemnification",
                "raw_text": "Each party shall indemnify the other against all claims...",
                "severity": "high",
                "risk_description": "Non-standard indemnity clause with broad liability scope",
                "legal_reasoning": "This clause extends liability beyond standard practice...",
                "confidence_score": 85,
                "is_standard": False,
                "is_missing_mandatory": False,
                "is_jurisdiction_mismatch": False,
                "applicable_statute": "Indian Contract Act 1872",
                "statute_section": "Section 37",
                "created_at": "2026-03-23T10:30:00Z"
            }
        }


class SuggestionDetail(BaseModel):
    """Schema for a single clause suggestion"""
    clause_type: str
    title: str
    purpose: str
    difficulty: int = Field(..., ge=1, le=5)
    priority: str


class DetailedSuggestions(BaseModel):
    """Schema for detailed contract improvement suggestions"""
    total_suggestions: int
    gaps_identified: int
    improvement_potential: int = Field(..., ge=0, le=100)
    tier_1_critical: List[SuggestionDetail] = []
    tier_2_important: List[SuggestionDetail] = []
    tier_3_recommended: List[SuggestionDetail] = []


class RiskAnalysisResponse(BaseModel):
    """Schema for contract risk analysis summary"""
    contract_id: UUID
    status: ContractStatusEnum
    overall_risk_score: Optional[int] = Field(None, ge=0, le=100)
    total_clauses_found: int
    critical_issues: int
    high_issues: int
    medium_issues: int = 0
    low_issues: int = 0
    clauses: List[ClauseResponse]
    analysis_summary: Optional[str]
    recommended_actions: Optional[List[str]]
    detailed_suggestions: Optional[DetailedSuggestions] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "contract_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "analyzed",
                "overall_risk_score": 72,
                "total_clauses_found": 15,
                "critical_issues": 1,
                "high_issues": 3,
                "medium_issues": 5,
                "low_issues": 6,
                "clauses": [],
                "analysis_summary": "3 critical/high-risk clauses requiring legal review",
                "recommended_actions": [
                    "Review Section 5 - Indemnity clause",
                    "Clarify jurisdiction in dispute resolution",
                    "Adjust liability caps in Section 8"
                ],
                "updated_at": "2026-03-23T10:35:00Z"
            }
        }


class ContractResponse(BaseModel):
    """Schema for contract metadata response"""
    id: UUID
    filename: str
    counterparty_name: Optional[str]
    contract_type: Optional[str]
    status: ContractStatusEnum
    overall_risk_score: Optional[int]
    total_clauses_found: int
    critical_issues: int
    high_issues: int
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "acme_service_agreement_draft.pdf",
                "counterparty_name": "Acme Corporation",
                "contract_type": "Service Agreement",
                "status": "analyzed",
                "overall_risk_score": 72,
                "total_clauses_found": 15,
                "critical_issues": 1,
                "high_issues": 3,
                "uploaded_by": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2026-03-23T10:00:00Z",
                "updated_at": "2026-03-23T10:35:00Z"
            }
        }


class ContractListResponse(BaseModel):
    """Schema for paginated contract list"""
    total: int
    page: int
    page_size: int
    contracts: List[ContractResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 42,
                "page": 1,
                "page_size": 20,
                "contracts": []
            }
        }


class ClauseDetailResponse(BaseModel):
    """Schema for detailed clause view with contract context"""
    clause: ClauseResponse
    contract: ContractResponse
    similar_clauses: Optional[List[Dict[str, Any]]] = Field(None, description="Similar clauses from other contracts")
    precedent_matches: Optional[List[Dict[str, Any]]] = Field(None, description="Matches to standard playbook")
    
    class Config:
        from_attributes = True


class ContractAnalysisJobResponse(BaseModel):
    """Schema for async analysis job status"""
    job_id: str
    contract_id: UUID
    status: str  # pending, processing, completed, failed
    progress_percentage: int = Field(0, ge=0, le=100)
    message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_550e8400-e29b-41d4-a716-446655440000",
                "contract_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress_percentage": 45,
                "message": "Performing semantic clause analysis...",
                "created_at": "2026-03-23T10:00:00Z",
                "completed_at": None
            }
        }


# ==================== ERROR SCHEMAS ====================

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "CONTRACT_NOT_FOUND",
                "message": "The requested contract does not exist",
                "details": {"contract_id": "550e8400-e29b-41d4-a716-446655440000"},
                "timestamp": "2026-03-23T10:35:00Z"
            }
        }
