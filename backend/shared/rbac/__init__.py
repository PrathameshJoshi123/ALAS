"""
Role-Based Access Control (RBAC) utilities
"""

from .rbac_utils import (
    check_permission,
    require_permission,
    require_any_permission,
    require_all_permissions,
    PermissionDeniedError,
)

__all__ = [
    "check_permission",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "PermissionDeniedError",
]
