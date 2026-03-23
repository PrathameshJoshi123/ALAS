"""
RBAC Utilities - Permission checking and enforcement
"""

from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List, Dict, Any, Callable

from shared.database.db import get_db
from shared.database.models import User, Role
from shared.redis_client.redis_manager import RedisClient
from shared.auth.auth_dependency import get_current_user
import logging

logger = logging.getLogger(__name__)


class PermissionDeniedError(HTTPException):
    """Exception raised when user lacks required permissions"""
    def __init__(self, resource: str, action: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: Cannot {action} {resource}"
        )


def get_redis_manager() -> RedisClient:
    """Get Redis client instance"""
    return RedisClient()


def get_user_permissions(
    user: User,
    db: Session
) -> Dict[str, Any]:
    """
    Get all permissions for a user from their role
    
    Args:
        user: User object with role_id
        db: Database session
        
    Returns:
        Dict: Permission matrix
    """
    try:
        redis_manager = get_redis_manager()
        
        # Try to get cached permissions first
        cached_permissions = redis_manager.get_cached_permissions(
            user.role_id,
            user.tenant_id
        )
        
        if cached_permissions:
            logger.debug(f"Using cached permissions for role {user.role_id}")
            return cached_permissions
        
        # If not cached, fetch from database
        role = db.query(Role).filter(Role.id == user.role_id).first()
        
        if not role:
            logger.error(f"Role {user.role_id} not found for user {user.id}")
            return {}
        
        # Cache the permissions
        redis_manager.cache_role_permissions(
            user.role_id,
            user.tenant_id,
            role.permission_matrix
        )
        
        return role.permission_matrix
        
    except Exception as e:
        logger.error(f"Failed to get user permissions: {str(e)}")
        return {}


def check_permission(
    user: User,
    service: str,
    action: str,
    db: Session
) -> bool:
    """
    Check if user has a specific permission
    
    Args:
        user: User object
        service: Service name (e.g., "contracts", "compliance")
        action: Action name (e.g., "view_contracts", "approve_contracts")
        db: Database session
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    permissions = get_user_permissions(user, db)
    
    # Check if service exists in permissions
    if service not in permissions:
        return False
    
    # Check if action exists and is allowed
    service_perms = permissions.get(service, {})
    return service_perms.get(action, False) is True


def require_permission(
    service: str,
    action: str
) -> Callable:
    """
    Create a FastAPI dependency that requires a specific permission
    
    Args:
        service: Service name (e.g., "contracts")
        action: Action name (e.g., "view_contracts")
        
    Returns:
        Callable: FastAPI dependency function
        
    Example:
        @router.get("/contracts")
        def list_contracts(
            current_user: User = Depends(get_current_user),
            _ = Depends(require_permission("contracts", "view_contracts", 
                    lambda: current_user))
        ):
            pass
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        if not check_permission(current_user, service, action, db):
            logger.warning(
                f"User {current_user.id} denied access to {service}.{action}"
            )
            raise PermissionDeniedError(service, action)
    
    return permission_checker


def require_any_permission(
    service: str,
    actions: List[str]
) -> Callable:
    """
    Create a FastAPI dependency that requires ANY of the listed permissions
    
    Args:
        service: Service name
        actions: List of action names (user needs at least one)
        
    Returns:
        Callable: FastAPI dependency function
        
    Example:
        @router.post("/contracts/{contract_id}/analyze")
        def analyze_contract(
            contract_id: UUID,
            current_user: User = Depends(get_current_user),
            _ = Depends(require_any_permission("contracts", 
                ["review_drafts", "approve_contracts", "execute_contracts"]))
        ):
            pass
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        has_permission = any(
            check_permission(current_user, service, action, db)
            for action in actions
        )
        
        if not has_permission:
            logger.warning(
                f"User {current_user.id} denied access to {service}.{actions}"
            )
            raise PermissionDeniedError(service, f"one of {actions}")
    
    return permission_checker


def require_all_permissions(
    permissions: List[tuple]
) -> Callable:
    """
    Create a FastAPI dependency that requires ALL listed permissions
    
    Args:
        permissions: List of (service, action) tuples
        
    Returns:
        Callable: FastAPI dependency function
        
    Example:
        @router.delete("/contracts/{contract_id}")
        def delete_contract(
            contract_id: UUID,
            current_user: User = Depends(get_current_user),
            _ = Depends(require_all_permissions([
                ("contracts", "view_contracts"),
                ("admin", "manage_users")
            ]))
        ):
            pass
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        for service, action in permissions:
            if not check_permission(current_user, service, action, db):
                logger.warning(
                    f"User {current_user.id} denied access to {service}.{action}"
                )
                raise PermissionDeniedError(service, action)
    
    return permission_checker


def require_admin_permission() -> Callable:
    """
    Create a FastAPI dependency that requires admin permissions
    
    Returns:
        Callable: FastAPI dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        if not check_permission(current_user, "admin", "manage_users", db):
            logger.warning(
                f"User {current_user.id} attempted admin-only operation"
            )
            raise PermissionDeniedError("admin", "access")
    
    return permission_checker


def check_own_resource_or_admin(
    user_id: UUID,
    current_user: User,
    db: Session
) -> bool:
    """
    Check if user owns a resource or is admin
    
    Useful for operations like delete_own_drafts where:
    - Owner can delete their own
    - Admin can delete anyone's
    
    Args:
        user_id: UUID of resource owner
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        bool: True if user is owner or admin
    """
    # If it's their own resource
    if current_user.id == user_id:
        return True
    
    # If user is admin
    return check_permission(current_user, "admin", "manage_users", db)
