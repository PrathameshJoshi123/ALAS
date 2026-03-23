"""
Auth Service - Business logic for authentication and authorization
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import logging

from shared.database.models import Tenant, User, Role, SubscriptionTier
from shared.encryption.aes256 import encrypt_pii, decrypt_pii, hash_email, verify_email_hash
from shared.jwt_handler.jwt_utils import create_access_token, create_refresh_token
from shared.redis_client.redis_manager import get_redis_client
from shared.audit.audit_logger import get_audit_logger
from services.auth.utils.password_utils import hash_password, verify_password
from services.auth.schemas.auth_schemas import (
    SignupRequest, LoginRequest, RefreshTokenRequest,
    RoleCreateRequest, DEFAULT_ROLES_DEFINITIONS
)

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and authorization operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis_client()
        self.audit = get_audit_logger()
    
    # ==================== TENANT MANAGEMENT ====================
    
    def create_tenant(
        self,
        company_name: str,
        industry: str,
        subscription_tier: str = "free"
    ) -> Tenant:
        """
        Create new tenant and setup default roles
        
        Args:
            company_name: Name of the company
            industry: Industry classification
            subscription_tier: Subscription level
            
        Returns:
            Tenant: Created tenant
        """
        try:
            # Normalize and validate subscription tier (accept case-insensitive strings)
            if isinstance(subscription_tier, str):
                sub_value = subscription_tier.lower()
            else:
                sub_value = subscription_tier

            try:
                if isinstance(sub_value, SubscriptionTier):
                    st = sub_value
                else:
                    st = SubscriptionTier(sub_value)
            except Exception:
                # Fallback to default when value is invalid
                st = SubscriptionTier.FREE

            # Create tenant
            tenant = Tenant(
                company_name=company_name,
                industry=industry,
                subscription_tier=st  # Pass the enum member, not the string
            )
            self.db.add(tenant)
            self.db.flush()
            
            # Create default roles for this tenant
            self._create_default_roles(tenant.id)
            
            self.db.commit()
            self.db.refresh(tenant)
            
            logger.info(f"Tenant created: {tenant.id} - {company_name}")
            
            # Log to audit
            self.audit.log_event(
                db=self.db,
                tenant_id=tenant.id,
                event_type="tenant_created",
                status="success",
                action="New tenant created",
                description=f"Company: {company_name}, Industry: {industry}"
            )
            
            return tenant
        
        except Exception as e:
            logger.error(f"Failed to create tenant: {str(e)}")
            self.db.rollback()
            raise
    
    def _create_default_roles(self, tenant_id: UUID):
        """Create default roles when tenant is created"""
        for role_name, permissions in DEFAULT_ROLES_DEFINITIONS.items():
            role = Role(
                tenant_id=tenant_id,
                role_name=role_name,
                permission_matrix=permissions
            )
            self.db.add(role)
            
            # Cache permissions in Redis
            self.redis.cache_role_permissions(role.id, tenant_id, permissions)
    
    # ==================== USER SIGNUP ====================
    
    def signup(
        self,
        request: SignupRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Register new user with tenant
        
        Args:
            request: Signup request with email, password, name, tenant_id
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            Tuple: (User, access_token, refresh_token)
        """
        try:
            # Verify tenant exists
            tenant = self.db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
            if not tenant:
                raise ValueError("Tenant not found")
            
            # Check if email already exists in tenant
            email_hash = hash_email(request.email)
            existing_user = self.db.query(User).filter(
                User.tenant_id == request.tenant_id,
                User.email_hash == email_hash
            ).first()
            
            if existing_user:
                raise ValueError("Email already registered in this tenant")
            
            # Get default role (Senior Partner for first user, Junior Associate for others)
            user_count = self.db.query(User).filter(User.tenant_id == request.tenant_id).count()
            default_role_name = "Senior Partner" if user_count == 0 else "Junior Associate"
            
            role = self.db.query(Role).filter(
                Role.tenant_id == request.tenant_id,
                Role.role_name == default_role_name
            ).first()
            
            if not role:
                raise ValueError(f"Default role '{default_role_name}' not found")
            
            # Encrypt PII
            name_encrypted = encrypt_pii(request.name)
            email_encrypted = encrypt_pii(request.email)
            
            # Hash password
            password_hash = hash_password(request.password)
            
            # Create user
            user = User(
                tenant_id=request.tenant_id,
                name_encrypted=name_encrypted,
                email_encrypted=email_encrypted,
                email_hash=email_hash,
                password_hash=password_hash,
                role_id=role.id,
                email_verified=1,  # Auto-verify for now
                is_active=1
            )
            
            self.db.add(user)
            self.db.flush()
            
            # Generate tokens
            access_token = create_access_token(
                user_id=user.id,
                tenant_id=request.tenant_id,
                role_id=role.id,
                permissions=role.permission_matrix
            )
            
            refresh_token = create_refresh_token(
                user_id=user.id,
                tenant_id=request.tenant_id
            )
            
            # Store refresh token in Redis
            self.redis.store_refresh_token(user.id, request.tenant_id, refresh_token)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User signed up: {user.id} in tenant {request.tenant_id}")
            
            # Log to audit
            self.audit.log_signup(
                db=self.db,
                tenant_id=request.tenant_id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return user, access_token, refresh_token
        
        except Exception as e:
            logger.error(f"Signup failed: {str(e)}")
            self.db.rollback()
            raise
    
    # ==================== USER LOGIN ====================
    
    def login(
        self,
        request: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and return tokens
        
        Args:
            request: Login request with email, password, tenant_id
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            Tuple: (User, access_token, refresh_token)
        """
        try:
            # Verify tenant exists
            tenant = self.db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
            if not tenant:
                logger.warning(f"Login attempt: tenant {request.tenant_id} not found")
                self.audit.log_login_failure(
                    db=self.db,
                    tenant_id=request.tenant_id,
                    email_hash=hash_email(request.email),
                    reason="Tenant not found",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise ValueError("Invalid tenant")
            
            # Find user by email hash
            email_hash = hash_email(request.email)
            user = self.db.query(User).filter(
                User.tenant_id == request.tenant_id,
                User.email_hash == email_hash
            ).first()
            
            if not user:
                logger.warning(f"Login attempt: user not found - {email_hash}")
                self.audit.log_login_failure(
                    db=self.db,
                    tenant_id=request.tenant_id,
                    email_hash=email_hash,
                    reason="User not found",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise ValueError("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt: inactive user - {user.id}")
                self.audit.log_login_failure(
                    db=self.db,
                    tenant_id=request.tenant_id,
                    email_hash=email_hash,
                    reason="User inactive",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise ValueError("User account is inactive")
            
            # Verify password
            if not verify_password(request.password, user.password_hash):
                logger.warning(f"Login attempt: invalid password - {email_hash}")
                self.audit.log_login_failure(
                    db=self.db,
                    tenant_id=request.tenant_id,
                    email_hash=email_hash,
                    reason="Invalid password",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise ValueError("Invalid email or password")
            
            # Get user's role and permissions
            role = self.db.query(Role).filter(Role.id == user.role_id).first()
            if not role:
                raise ValueError("User role not found")
            
            # Try to get cached permissions, otherwise use from database
            permissions = self.redis.get_cached_permissions(role.id, request.tenant_id)
            if permissions is None:
                permissions = role.permission_matrix
                self.redis.cache_role_permissions(role.id, request.tenant_id, permissions)
            
            # Generate tokens
            access_token = create_access_token(
                user_id=user.id,
                tenant_id=request.tenant_id,
                role_id=role.id,
                permissions=permissions
            )
            
            refresh_token = create_refresh_token(
                user_id=user.id,
                tenant_id=request.tenant_id
            )
            
            # Store refresh token in Redis
            self.redis.store_refresh_token(user.id, request.tenant_id, refresh_token)
            
            logger.info(f"User logged in: {user.id} in tenant {request.tenant_id}")
            
            # Log to audit
            self.audit.log_login_success(
                db=self.db,
                tenant_id=request.tenant_id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return user, access_token, refresh_token
        
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
    
    # ==================== TOKEN MANAGEMENT ====================
    
    def refresh_access_token(
        self,
        request: RefreshTokenRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Refresh access token using refresh token
        
        Args:
            request: Refresh token request
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            Tuple: (new_access_token, refresh_token)
        """
        try:
            from shared.jwt_handler.jwt_utils import verify_token
            
            # Verify refresh token
            payload = verify_token(request.refresh_token, token_type="refresh")
            
            user_id = UUID(payload.get("sub"))
            tenant_id = UUID(payload.get("tenant_id"))
            
            # Verify refresh token exists in Redis
            redis_token = self.redis.get_refresh_token(user_id, tenant_id)
            if redis_token != request.refresh_token:
                logger.warning(f"Refresh token mismatch for user {user_id}")
                raise ValueError("Invalid or revoked refresh token")
            
            # Get user and role
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")
            
            role = self.db.query(Role).filter(Role.id == user.role_id).first()
            if not role:
                raise ValueError("User role not found")
            
            # Get cached permissions
            permissions = self.redis.get_cached_permissions(role.id, tenant_id)
            if permissions is None:
                permissions = role.permission_matrix
            
            # Generate new access token with same refresh token
            access_token = create_access_token(
                user_id=user_id,
                tenant_id=tenant_id,
                role_id=role.id,
                permissions=permissions
            )
            
            logger.info(f"Access token refreshed for user {user_id}")
            
            # Log to audit
            self.audit.log_token_refresh(
                db=self.db,
                tenant_id=tenant_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return access_token, request.refresh_token
        
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise
    
    def logout(self, user_id: UUID, tenant_id: UUID) -> bool:
        """
        Logout user - revoke refresh token
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant
            
        Returns:
            bool: True if successful
        """
        try:
            # Revoke refresh token
            self.redis.revoke_refresh_token(user_id, tenant_id)
            
            logger.info(f"User logged out: {user_id}")
            
            # Log to audit
            self.audit.log_logout(
                db=self.db,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False
    
    # ==================== USER MANAGEMENT ====================
    
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        """Get user by email (requires decryption)"""
        email_hash = hash_email(email)
        return self.db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email_hash == email_hash
        ).first()
    
    def decrypt_user_pii(self, user: User) -> Tuple[str, str]:
        """
        Decrypt user PII
        
        Args:
            user: User object
            
        Returns:
            Tuple: (name, email)
        """
        name = decrypt_pii(user.name_encrypted)
        email = decrypt_pii(user.email_encrypted)
        return name, email
    
    # ==================== ROLE MANAGEMENT ====================
    
    def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID,
        changed_by_user_id: UUID
    ) -> User:
        """
        Assign a role to a user
        
        Args:
            user_id: UUID of user to assign role to
            role_id: UUID of role to assign
            tenant_id: UUID of tenant
            changed_by_user_id: UUID of user making the change
            
        Returns:
            User: Updated user object
        """
        try:
            # Get the user
            user = self.db.query(User).filter(
                User.id == user_id,
                User.tenant_id == tenant_id
            ).first()
            
            if not user:
                raise ValueError("User not found in this tenant")
            
            # Get the role
            role = self.db.query(Role).filter(
                Role.id == role_id,
                Role.tenant_id == tenant_id
            ).first()
            
            if not role:
                raise ValueError("Role not found in this tenant")
            
            # Update user's role
            old_role_id = user.role_id
            user.role_id = role_id
            user.updated_at = datetime.utcnow()
            user.version += 1
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Role assigned: user {user_id} -> role {role.role_name}")
            
            # Get old role name for audit
            old_role = self.db.query(Role).filter(Role.id == old_role_id).first()
            old_role_name = old_role.role_name if old_role else "Unknown"
            
            # Log to audit
            self.audit.log_role_assignment(
                db=self.db,
                tenant_id=tenant_id,
                user_id=user_id,
                role_name=role.role_name,
                changed_by=changed_by_user_id
            )
            
            # Invalidate cached permissions in Redis
            self.redis.invalidate_role_cache(old_role_id)
            
            return user
        
        except Exception as e:
            logger.error(f"Failed to assign role: {str(e)}")
            self.db.rollback()
            raise
    
    def get_users_by_tenant(self, tenant_id: UUID) -> list:
        """
        Get all users in a tenant
        
        Args:
            tenant_id: UUID of tenant
            
        Returns:
            list: List of User objects
        """
        users = self.db.query(User).filter(User.tenant_id == tenant_id).all()
        return users
    
    def get_roles_by_tenant(self, tenant_id: UUID) -> list:
        """
        Get all roles in a tenant
        
        Args:
            tenant_id: UUID of tenant
            
        Returns:
            list: List of Role objects
        """
        roles = self.db.query(Role).filter(Role.tenant_id == tenant_id).all()
        return roles
    
    def get_role_by_id(self, role_id: UUID, tenant_id: UUID) -> Optional[Role]:
        """
        Get a role by ID
        
        Args:
            role_id: UUID of role
            tenant_id: UUID of tenant
            
        Returns:
            Role: Role object or None if not found
        """
        return self.db.query(Role).filter(
            Role.id == role_id,
            Role.tenant_id == tenant_id
        ).first()
    
    def create_role(
        self,
        tenant_id: UUID,
        role_name: str,
        permission_matrix: Dict[str, Any],
        created_by_user_id: UUID
    ) -> Role:
        """
        Create a new role in a tenant
        
        Args:
            tenant_id: UUID of tenant
            role_name: Name of the role
            permission_matrix: Permission matrix (JSON)
            created_by_user_id: UUID of user creating the role
            
        Returns:
            Role: Created role object
        """
        try:
            # Check if role name already exists in tenant
            existing_role = self.db.query(Role).filter(
                Role.tenant_id == tenant_id,
                Role.role_name == role_name
            ).first()
            
            if existing_role:
                raise ValueError(f"Role '{role_name}' already exists in this tenant")
            
            # Create role
            role = Role(
                tenant_id=tenant_id,
                role_name=role_name,
                permission_matrix=permission_matrix
            )
            
            self.db.add(role)
            self.db.flush()
            
            # Cache permissions in Redis
            self.redis.cache_role_permissions(role.id, tenant_id, permission_matrix)
            
            self.db.commit()
            self.db.refresh(role)
            
            logger.info(f"Role created: {role_name} in tenant {tenant_id}")
            
            # Log to audit
            self.audit.log_role_creation(
                db=self.db,
                tenant_id=tenant_id,
                role_name=role_name,
                created_by=created_by_user_id
            )
            
            return role
        
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            self.db.rollback()
            raise
    
    def update_role(
        self,
        role_id: UUID,
        tenant_id: UUID,
        role_name: Optional[str] = None,
        permission_matrix: Optional[Dict[str, Any]] = None,
        updated_by_user_id: Optional[UUID] = None
    ) -> Role:
        """
        Update a role
        
        Args:
            role_id: UUID of role
            tenant_id: UUID of tenant
            role_name: New role name (optional)
            permission_matrix: New permission matrix (optional)
            updated_by_user_id: UUID of user updating the role
            
        Returns:
            Role: Updated role object
        """
        try:
            # Get the role
            role = self.db.query(Role).filter(
                Role.id == role_id,
                Role.tenant_id == tenant_id
            ).first()
            
            if not role:
                raise ValueError("Role not found in this tenant")
            
            # Update fields if provided
            if role_name is not None:
                # Check if new role name already exists
                existing_role = self.db.query(Role).filter(
                    Role.tenant_id == tenant_id,
                    Role.role_name == role_name,
                    Role.id != role_id
                ).first()
                
                if existing_role:
                    raise ValueError(f"Role '{role_name}' already exists in this tenant")
                
                role.role_name = role_name
            
            if permission_matrix is not None:
                role.permission_matrix = permission_matrix
                # Invalidate cache
                self.redis.invalidate_role_cache(role_id)
            
            role.updated_at = datetime.utcnow()
            role.version += 1
            
            self.db.commit()
            self.db.refresh(role)
            
            # Update cache if permissions changed
            if permission_matrix is not None:
                self.redis.cache_role_permissions(role_id, tenant_id, permission_matrix)
            
            logger.info(f"Role updated: {role.role_name} in tenant {tenant_id}")
            
            # Log to audit
            if updated_by_user_id:
                self.audit.log_event(
                    db=self.db,
                    tenant_id=tenant_id,
                    event_type="role_updated",
                    status="success",
                    action="Role updated",
                    user_id=updated_by_user_id,
                    description=f"Updated role: {role.role_name}"
                )
            
            return role
        
        except Exception as e:
            logger.error(f"Failed to update role: {str(e)}")
            self.db.rollback()
            raise


# Global instance factory
def get_auth_service(db: Session) -> AuthService:
    """Factory function to get auth service instance"""
    return AuthService(db)
