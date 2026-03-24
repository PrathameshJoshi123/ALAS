from sqlalchemy import (
    Column, String, UUID, DateTime, Integer, 
    ForeignKey, Enum, JSON, Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum
from sqlalchemy import event

from shared.database.db import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tier enumeration"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """
    Tenants Table - The apex table in multi-tenant architecture
    Each tenant is a corporate entity with complete isolation via RLS (future)
    """
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=False)
    subscription_tier = Column(
        Enum(SubscriptionTier, values_callable=lambda x: [e.value for e in x], native_enum=True),
        default=SubscriptionTier.FREE
    )
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking
    
    # Relationships
    roles = relationship("Role", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")


class Role(Base):
    """
    Roles Table - Backbone of liability management
    Defines what actions users can perform across different microservices
    """
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    role_name = Column(String(100), nullable=False)
    
    # Permission matrix stored as JSONB
    # Structure: {
    #     "service_name": {
    #         "resource": ["read", "write", "delete"],
    #         "action": ["allowed", "not_allowed"]
    #     }
    # }
    permission_matrix = Column(JSON, nullable=False, default={})
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking
    
    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    users = relationship("User", back_populates="role")
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_role_name", "tenant_id", "role_name", unique=False),
    )


class User(Base):
    """
    Users Table - Individual human actors
    PII fields (name, email) are encrypted with AES-256 per DPDP Act
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # PII Fields (Encrypted)
    # name_encrypted: AES-256 encrypted full name
    # email_encrypted: AES-256 encrypted email
    # email_hash: SHA-256 hash of email for lookups/search
    name_encrypted = Column(Text, nullable=False)
    email_encrypted = Column(Text, nullable=False)
    email_hash = Column(String(255), nullable=False, unique=True, index=True)  # For login verification
    
    # Password Security
    password_hash = Column(String(255), nullable=False)  # Bcrypt hash
    
    # Authorization
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    
    # Account Status
    is_active = Column(Integer, default=1, nullable=False)  # 1 = active, 0 = inactive
    email_verified = Column(Integer, default=0, nullable=False)  # 1 = verified, 0 = not verified
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_email_hash", "tenant_id", "email_hash", unique=False),
    )


class AuditLog(Base):
    """
    Audit Logs Table - Immutable audit trail
    Every auth event is logged for compliance and security monitoring
    """
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for tenant-level events
    
    # Event Information
    event_type = Column(String(50), nullable=False)  # login, logout, signup, refresh, create_role, etc.
    status = Column(String(20), nullable=False)  # success, failure
    action = Column(String(100), nullable=False)
    
    # Details
    description = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_event_created", "tenant_id", "event_type", "created_at", unique=False),
    )


# ------------------ Model Event Listeners ------------------
def _normalize_subscription_tier(mapper, connection, target):
    """Ensure `subscription_tier` is a SubscriptionTier enum member (case-insensitive strings accepted)."""
    try:
        val = getattr(target, "subscription_tier", None)
        if val is None:
            setattr(target, "subscription_tier", SubscriptionTier.FREE)
            return

        # If it's already an enum member, nothing to do
        if isinstance(val, SubscriptionTier):
            return

        # If it's a string, try to coerce (case-insensitive)
        if isinstance(val, str):
            lowered = val.lower()
            try:
                setattr(target, "subscription_tier", SubscriptionTier(lowered))
                return
            except (ValueError, KeyError):
                # fallback to default
                setattr(target, "subscription_tier", SubscriptionTier.FREE)
                return

    except Exception:
        # Best-effort; don't raise during DB operations
        try:
            setattr(target, "subscription_tier", SubscriptionTier.FREE)
        except Exception:
            pass


event.listen(Tenant, "before_insert", _normalize_subscription_tier)
event.listen(Tenant, "before_update", _normalize_subscription_tier)


# ==================== CONTRACT SERVICE MODELS ====================

class ContractStatus(str, enum.Enum):
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


class ClauseSeverity(str, enum.Enum):
    """Risk severity levels for contract clauses"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Contract(Base):
    """
    Contracts Table - Stores metadata for uploaded contracts
    File content stored on disk in backend/files/ directory
    Analysis results stored in ChromaDB vector database
    """
    __tablename__ = "contracts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Contract Metadata
    filename = Column(String(255), nullable=False)
    counterparty_name = Column(String(255), nullable=True)  # Third-party entity name
    contract_type = Column(String(100), nullable=True)  # e.g., "NDA", "Service Agreement", "License"
    file_path = Column(String(500), nullable=False)  # Relative path in backend/files/
    
    # OCR & Extraction
    raw_text = Column(Text, nullable=True)  # Complete extracted text by PaddleOCR
    text_extraction_confidence = Column(Integer, nullable=True)  # Average confidence 0-100
    
    # AI Analysis Status
    status = Column(
        Enum(ContractStatus, values_callable=lambda x: [e.value for e in x], native_enum=True),
        default=ContractStatus.UPLOADED,
        nullable=False,
        index=True
    )
    analysis_job_id = Column(String(255), nullable=True)  # DeepAgents job tracking
    
    # Risk Summary
    overall_risk_score = Column(Integer, nullable=True)  # 0-100, null until analyzed
    total_clauses_found = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
    clauses = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_contract_tenant_status", "tenant_id", "status", unique=False),
        Index("idx_contract_created_at", "created_at", unique=False),
    )


class Clause(Base):
    """
    Clauses Table - Stores extracted and analyzed clauses from contracts
    Embeddings stored in ChromaDB with reference to this record's ID
    """
    __tablename__ = "clauses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Clause Location & Content
    clause_number = Column(Integer, nullable=False)  # Sequential position in document
    clause_type = Column(String(100), nullable=True)  # e.g., "Indemnity", "IP Rights", "Termination"
    section_title = Column(String(255), nullable=True)  # Section heading from document
    raw_text = Column(Text, nullable=False)  # Original extracted clause text
    
    # AI Analysis
    severity = Column(
        Enum(ClauseSeverity, values_callable=lambda x: [e.value for e in x], native_enum=True),
        default=ClauseSeverity.INFO,
        nullable=False
    )
    risk_description = Column(Text, nullable=True)  # AI-generated risk explanation
    legal_reasoning = Column(Text, nullable=True)  # LLM analysis output (Mistral)
    confidence_score = Column(Integer, nullable=False)  # 0-100, AI confidence in assessment
    
    # Metadata for ChromaDB reference
    chromadb_id = Column(String(255), nullable=True, unique=True)  # UUID reference in ChromaDB
    embedding_dimension = Column(Integer, default=1536)  # Mistral embedding dimension
    
    # Statutory References
    applicable_statute = Column(String(255), nullable=True)  # e.g., "Indian Contract Act 1872"
    statute_section = Column(String(100), nullable=True)  # e.g., "Section 37"
    
    # Flag Indicators
    is_standard = Column(Integer, default=1)  # 1 = standard clause, 0 = non-standard/risky
    is_missing_mandatory = Column(Integer, default=0)  # 1 = flagged as missing
    is_jurisdiction_mismatch = Column(Integer, default=0)  # 1 = jurisdiction issue detected
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    # Relationships
    contract = relationship("Contract", back_populates="clauses")
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_clause_contract_severity", "contract_id", "severity", unique=False),
        Index("idx_clause_tenant_type", "tenant_id", "clause_type", unique=False),
    )


class LegalWebSearch(Base):
    """
    LegalWebSearch - cached web search results used to provide statutory
    and precedent context to the legal reasoning subagent.

    Stores the original query, a JSON blob of results, the tenant that requested
    the search and a timestamp for cache expiry / inspection.
    """
    __tablename__ = "legal_web_search"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    query = Column(String(1024), nullable=False, index=True)
    results = Column(JSON, nullable=False)
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", foreign_keys=[tenant_id])

    __table_args__ = (
        Index("idx_legalweb_tenant_query", "tenant_id", "query", unique=False),
    )
