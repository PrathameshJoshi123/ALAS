"""
Auth Service Routes - API endpoints for authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from shared.database.db import get_db
from shared.database.models import User, Role
from services.auth.schemas.auth_schemas import (
    SignupRequest, SignupResponse, LoginRequest, LoginResponse,
    RefreshTokenRequest, TokenRefreshResponse, UserResponse,
    TenantCreateRequest, TenantResponse, ErrorResponse,
    RoleCreateRequest, RoleUpdateRequest, RoleResponse,
    UserRoleAssignmentRequest
)
from services.auth.utils.auth_service import get_auth_service
from services.auth.utils.password_utils import verify_password
from shared.encryption.aes256 import decrypt_pii

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_client_info(request: Request):
    """Extract client IP and user agent from request"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate current user from Authorization header
    
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        from shared.jwt_handler.jwt_utils import verify_token
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        # Verify token
        payload = verify_token(token, token_type="access")
        user_id = UUID(payload.get("sub"))
        
        # Get user from database
        auth_service = get_auth_service(db)
        user = auth_service.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ==================== TENANT ENDPOINTS ====================

@router.post("/tenants", response_model=TenantResponse)
def create_tenant(
    request: TenantCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create new tenant
    
    This endpoint initializes a new company account with default roles.
    """
    try:
        auth_service = get_auth_service(db)
        tenant = auth_service.create_tenant(
            company_name=request.company_name,
            industry=request.industry,
            subscription_tier=request.subscription_tier
        )
        return tenant
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/tenants", response_model=List[TenantResponse])
def get_tenants(
    db: Session = Depends(get_db)
):
    """
    Get all tenants
    
    Returns a list of all registered tenants.
    """
    try:
        auth_service = get_auth_service(db)
        tenants = auth_service.get_all_tenants()
        return tenants
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenants"
        )



# ==================== AUTHENTICATION ENDPOINTS ====================

@router.post("/signup", response_model=SignupResponse)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
    client_info: tuple = Depends(get_client_info)
):
    """
    Register new user
    
    Creates a new user account in the specified tenant.
    Password must be:
    - At least 8 characters
    - Contain uppercase letter
    - Contain at least one digit
    
    First user in tenant becomes Senior Partner, others become Junior Associate.
    """
    try:
        ip_address, user_agent = client_info
        auth_service = get_auth_service(db)
        user, access_token, refresh_token = auth_service.signup(
            request=request,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Decrypt PII for response
        name, email = auth_service.decrypt_user_pii(user)
        
        return SignupResponse(
            id=user.id,
            email=email,
            name=name,
            tenant_id=user.tenant_id,
            message="User created successfully"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    client_info: tuple = Depends(get_client_info)
):
    """
    Authenticate user and return tokens
    
    Returns:
    - access_token: Short-lived token (15 minutes) for API requests
    - refresh_token: Long-lived token (7 days) for obtaining new access tokens
    """
    try:
        ip_address, user_agent = client_info
        auth_service = get_auth_service(db)
        user, access_token, refresh_token = auth_service.login(
            request=request,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Decrypt PII for response
        name, email = auth_service.decrypt_user_pii(user)
        
        user_response = UserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            email=email,
            name=name,
            role_id=user.role_id,
            is_active=bool(user.is_active),
            email_verified=bool(user.email_verified),
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    client_info: tuple = Depends(get_client_info)
):
    """
    Refresh access token using refresh token
    
    Returns new access token. Refresh token remains the same.
    """
    try:
        ip_address, user_agent = client_info
        auth_service = get_auth_service(db)
        access_token, _ = auth_service.refresh_access_token(
            request=request,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return TokenRefreshResponse(access_token=access_token)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
def logout(
    user_id: UUID,
    tenant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Logout user - revoke refresh token
    """
    try:
        auth_service = get_auth_service(db)
        auth_service.logout(user_id, tenant_id)
        return {"message": "Logged out successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# ==================== USER ENDPOINTS ====================

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get user details (decrypted)
    """
    try:
        auth_service = get_auth_service(db)
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        name, email = auth_service.decrypt_user_pii(user)
        
        return UserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            email=email,
            name=name,
            role_id=user.role_id,
            is_active=bool(user.is_active),
            email_verified=bool(user.email_verified),
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}


# ==================== ROLE MANAGEMENT ENDPOINTS ====================

@router.post("/tenants/{tenant_id}/roles", response_model=RoleResponse)
def create_role(
    tenant_id: UUID,
    request: RoleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new role in a tenant
    
    Only users with 'manage_roles' permission can create roles.
    Typically only Senior Partner and In-House Counsel.
    """
    try:
        # Verify user belongs to the tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot manage roles in different tenant"
            )
        
        # Check permission (would come from token in real implementation)
        # For now, we'll allow if user has role that can manage roles
        auth_service = get_auth_service(db)
        role = current_user.role
        if not role.permission_matrix.get("admin", {}).get("manage_roles", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create roles"
            )
        
        # Create role
        new_role = auth_service.create_role(
            tenant_id=tenant_id,
            role_name=request.role_name,
            permission_matrix=request.permission_matrix,
            created_by_user_id=current_user.id
        )
        
        return RoleResponse.model_validate(new_role)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role"
        )


@router.get("/tenants/{tenant_id}/roles", response_model=List[RoleResponse])
def list_roles(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all roles in a tenant
    
    Any authenticated user in the tenant can view roles.
    """
    try:
        # Verify user belongs to the tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access roles in different tenant"
            )
        
        auth_service = get_auth_service(db)
        roles = auth_service.get_roles_by_tenant(tenant_id)
        
        return [RoleResponse.model_validate(role) for role in roles]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list roles"
        )


@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: UUID,
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific role details
    
    Any authenticated user in the tenant can view role details.
    """
    try:
        # Verify user belongs to the tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access roles in different tenant"
            )
        
        auth_service = get_auth_service(db)
        role = auth_service.get_role_by_id(role_id, tenant_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        return RoleResponse.model_validate(role)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve role"
        )


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: UUID,
    request: RoleUpdateRequest,
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a role
    
    Only users with 'manage_roles' permission can update roles.
    """
    try:
        # Verify user belongs to the tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot manage roles in different tenant"
            )
        
        # Check permission
        auth_service = get_auth_service(db)
        role = current_user.role
        if not role.permission_matrix.get("admin", {}).get("manage_roles", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update roles"
            )
        
        # Update role
        updated_role = auth_service.update_role(
            role_id=role_id,
            tenant_id=tenant_id,
            role_name=request.role_name,
            permission_matrix=request.permission_matrix,
            updated_by_user_id=current_user.id
        )
        
        return RoleResponse.model_validate(updated_role)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )


# ==================== USER MANAGEMENT ENDPOINTS ====================

@router.get("/tenants/{tenant_id}/users", response_model=List[UserResponse])
def list_users(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all users in a tenant
    
    Any authenticated user in the tenant can view the user list.
    """
    try:
        # Verify user belongs to the tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access users in different tenant"
            )
        
        auth_service = get_auth_service(db)
        users = auth_service.get_users_by_tenant(tenant_id)
        
        # Decrypt PII for all users
        user_responses = []
        for user in users:
            name, email = auth_service.decrypt_user_pii(user)
            user_responses.append(
                UserResponse(
                    id=user.id,
                    tenant_id=user.tenant_id,
                    email=email,
                    name=name,
                    role_id=user.role_id,
                    is_active=bool(user.is_active),
                    email_verified=bool(user.email_verified),
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
            )
        
        return user_responses
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.put("/users/{user_id}/role", response_model=UserResponse)
def assign_role_to_user(
    user_id: UUID,
    request: UserRoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign a role to a user
    
    Only users with 'manage_users' permission can assign roles.
    The user making the change and the user being changed must be in the same tenant.
    """
    try:
        # Get the target user to verify tenant
        auth_service = get_auth_service(db)
        target_user = auth_service.get_user_by_id(user_id)
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify user belongs to the same tenant
        if current_user.tenant_id != target_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot manage users in different tenant"
            )
        
        # Check permission
        current_role = current_user.role
        if not current_role.permission_matrix.get("admin", {}).get("manage_users", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to assign roles"
            )
        
        # Assign role
        updated_user = auth_service.assign_role_to_user(
            user_id=user_id,
            role_id=request.role_id,
            tenant_id=current_user.tenant_id,
            changed_by_user_id=current_user.id
        )
        
        # Decrypt PII for response
        name, email = auth_service.decrypt_user_pii(updated_user)
        
        return UserResponse(
            id=updated_user.id,
            tenant_id=updated_user.tenant_id,
            email=email,
            name=name,
            role_id=updated_user.role_id,
            is_active=bool(updated_user.is_active),
            email_verified=bool(updated_user.email_verified),
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )
