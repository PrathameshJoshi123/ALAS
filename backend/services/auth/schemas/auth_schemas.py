"""
Pydantic schemas for Auth Service requests and responses
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


# ==================== REQUEST SCHEMAS ====================

class TenantCreateRequest(BaseModel):
    """Schema for tenant creation"""
    company_name: str = Field(..., min_length=1, max_length=255)
    industry: str = Field(..., min_length=1, max_length=100)
    subscription_tier: Optional[str] = Field(default="free", description="free, pro, or enterprise")
    
    @field_validator("subscription_tier", mode="before")
    @classmethod
    def validate_subscription_tier(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize subscription tier to lowercase"""
        if v is None:
            return "free"
        
        # Normalize to lowercase
        normalized = v.lower() if isinstance(v, str) else str(v).lower()
        
        # Check if it's valid (valid values: free, pro, enterprise)
        valid_values = {"free", "pro", "enterprise"}
        if normalized not in valid_values:
            raise ValueError(
                f"Invalid subscription_tier '{v}'. Must be one of: free, pro, enterprise"
            )
        return normalized


class SignupRequest(BaseModel):
    """Schema for user signup"""
    tenant_id: UUID
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """Schema for user login"""
    tenant_id: UUID
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh"""
    refresh_token: str


class RoleCreateRequest(BaseModel):
    """Schema for role creation"""
    role_name: str = Field(..., min_length=1, max_length=100)
    permission_matrix: Dict[str, Any] = Field(default={})
    description: Optional[str] = Field(default=None)


class RoleUpdateRequest(BaseModel):
    """Schema for role updates"""
    role_name: Optional[str] = None
    permission_matrix: Optional[Dict[str, Any]] = None


class UserRoleAssignmentRequest(BaseModel):
    """Schema for assigning role to user"""
    user_id: UUID
    role_id: UUID


# ==================== RESPONSE SCHEMAS ====================

class TenantResponse(BaseModel):
    """Schema for tenant response"""
    id: UUID
    company_name: str
    industry: str
    subscription_tier: str
    created_at: datetime
    updated_at: datetime
    version: int
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: UUID
    tenant_id: UUID
    email: str  # Should be decrypted plaintext
    name: str   # Should be decrypted plaintext
    role_id: UUID
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    """Schema for role response"""
    id: UUID
    tenant_id: UUID
    role_name: str
    permission_matrix: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class SignupResponse(BaseModel):
    """Schema for signup response"""
    id: UUID
    email: str
    name: str
    tenant_id: UUID
    message: str = "User created successfully"


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str
    token_type: str = "bearer"


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID] = None
    event_type: str
    status: str
    action: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Schema for error response"""
    detail: str
    code: str
    status_code: int


# ==================== DEFAULT ROLE DEFINITIONS ====================

DEFAULT_JUNIOR_ASSOCIATE_PERMISSIONS = {
    "contracts": {
        "view_contracts": True,
        "view_clauses": True,
        "create_drafts": True,
        "submit_for_review": True,
        "flag_risks": True,
        "edit_own_drafts": True,
        "delete_own_drafts": True,
    },
    "compliance": {
        "view_status": True,
        "fill_forms": True,
        "view_checklists": True,
    },
    "employment": {
        "view_templates": True,
        "create_documents": True,
        "submit_for_review": True,
    },
    "admin": {
        "manage_users": False,
        "manage_roles": False,
        "view_audit_logs": False,
    }
}

DEFAULT_SENIOR_ASSOCIATE_PERMISSIONS = {
    "contracts": {
        "view_contracts": True,
        "view_clauses": True,
        "create_drafts": True,
        "review_drafts": True,
        "approve_contracts": True,
        "edit_contracts": True,
        "submit_for_filing": True,
        "flag_risks": True,
        "edit_own_drafts": True,
        "delete_own_drafts": True,
    },
    "compliance": {
        "view_status": True,
        "manage_filings": True,
        "view_checklists": True,
        "update_compliance": True,
    },
    "employment": {
        "view_templates": True,
        "create_documents": True,
        "review_documents": True,
        "approve_documents": True,
        "submit_for_approval": True,
    },
    "admin": {
        "manage_users": False,
        "manage_roles": False,
        "view_audit_logs": True,
    }
}

DEFAULT_COMPLIANCE_OFFICER_PERMISSIONS = {
    "contracts": {
        "view_contracts": True,
        "view_clauses": True,
        "flag_compliance_risks": True,
    },
    "compliance": {
        "view_status": True,
        "manage_filings": True,
        "view_checklists": True,
        "update_compliance": True,
        "manage_deadlines": True,
        "generate_reports": True,
    },
    "employment": {
        "view_documents": True,
        "check_compliance": True,
    },
    "admin": {
        "manage_users": False,
        "manage_roles": False,
        "view_audit_logs": True,
    }
}

DEFAULT_IN_HOUSE_COUNSEL_PERMISSIONS = {
    "contracts": {
        "view_contracts": True,
        "view_clauses": True,
        "create_drafts": True,
        "review_drafts": True,
        "approve_contracts": True,
        "edit_contracts": True,
        "execute_contracts": True,
        "flag_risks": True,
        "strategic_decisions": True,
    },
    "compliance": {
        "view_status": True,
        "manage_filings": True,
        "view_checklists": True,
        "update_compliance": True,
        "manage_deadlines": True,
        "generate_reports": True,
        "policy_decisions": True,
    },
    "employment": {
        "view_templates": True,
        "create_documents": True,
        "review_documents": True,
        "approve_documents": True,
        "strategic_decisions": True,
    },
    "admin": {
        "manage_users": True,
        "manage_roles": True,
        "view_audit_logs": True,
    }
}

DEFAULT_SENIOR_PARTNER_PERMISSIONS = {
    "contracts": {
        "view_contracts": True,
        "view_clauses": True,
        "create_drafts": True,
        "review_drafts": True,
        "approve_contracts": True,
        "edit_contracts": True,
        "execute_contracts": True,
        "flag_risks": True,
        "strategic_decisions": True,
        "override_decisions": True,
    },
    "compliance": {
        "view_status": True,
        "manage_filings": True,
        "view_checklists": True,
        "update_compliance": True,
        "manage_deadlines": True,
        "generate_reports": True,
        "policy_decisions": True,
        "override_decisions": True,
    },
    "employment": {
        "view_templates": True,
        "create_documents": True,
        "review_documents": True,
        "approve_documents": True,
        "strategic_decisions": True,
        "override_decisions": True,
    },
    "admin": {
        "manage_users": True,
        "manage_roles": True,
        "view_audit_logs": True,
        "system_admin": True,
    }
}

DEFAULT_ROLES_DEFINITIONS = {
    "Junior Associate": DEFAULT_JUNIOR_ASSOCIATE_PERMISSIONS,
    "Senior Associate": DEFAULT_SENIOR_ASSOCIATE_PERMISSIONS,
    "Compliance Officer": DEFAULT_COMPLIANCE_OFFICER_PERMISSIONS,
    "In-House Counsel": DEFAULT_IN_HOUSE_COUNSEL_PERMISSIONS,
    "Senior Partner": DEFAULT_SENIOR_PARTNER_PERMISSIONS,
}
