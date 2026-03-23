"""
Audit Logging Service for compliance and security

Logs all authentication events:
- Login/Logout
- Token refresh
- Role/permission changes
- Account creation/deletion
- Failed attempts
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import datetime
import logging

from shared.database.models import AuditLog, Tenant, User

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging audit events"""
    
    def __init__(self):
        pass
    
    def log_event(
        self,
        db: Session,
        tenant_id: UUID,
        event_type: str,
        status: str,
        action: str,
        user_id: Optional[UUID] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Log an audit event to database
        
        Args:
            db: Database session
            tenant_id: UUID of tenant (required)
            event_type: Type of event (login, logout, signup, refresh, etc.)
            status: Success or failure
            action: Detailed action description
            user_id: UUID of user (optional for tenant-level events)
            description: Additional context
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            AuditLog: Created audit log record
        """
        try:
            # Verify tenant exists
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                logger.error(f"Cannot audit: tenant {tenant_id} not found")
                return None
            
            # If user_id provided, verify user exists
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.warning(f"Audit user_id {user_id} not found, logging without user reference")
                    user_id = None
            
            # Create audit log record
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                event_type=event_type,
                status=status,
                action=action,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(
                f"Audit logged - Tenant: {tenant_id}, Event: {event_type}, "
                f"Status: {status}, User: {user_id}"
            )
            
            return audit_log
        
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            db.rollback()
            return None
    
    # ==================== SPECIFIC EVENT LOGGERS ====================
    
    def log_login_success(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log successful login"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="login",
            status="success",
            action="User logged in",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_login_failure(
        self,
        db: Session,
        tenant_id: UUID,
        email_hash: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log failed login attempt"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="login",
            status="failure",
            action="Login attempt failed",
            description=f"Reason: {reason}. Email hash: {email_hash[:8]}...",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_logout(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log logout"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="logout",
            status="success",
            action="User logged out",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_token_refresh(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log token refresh"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="refresh",
            status="success",
            action="Access token refreshed",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_signup(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log user signup"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="signup",
            status="success",
            action="New user created",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_role_assignment(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        role_name: str,
        changed_by: UUID
    ) -> Optional[AuditLog]:
        """Log role assignment"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="role_assignment",
            status="success",
            action="User role changed",
            user_id=changed_by,
            description=f"Assigned {role_name} to user {user_id}"
        )
    
    def log_role_creation(
        self,
        db: Session,
        tenant_id: UUID,
        role_name: str,
        created_by: UUID
    ) -> Optional[AuditLog]:
        """Log role creation"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="role_created",
            status="success",
            action="New role created",
            user_id=created_by,
            description=f"Created role: {role_name}"
        )
    
    def log_unauthorized_access(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        resource: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log unauthorized access attempt"""
        return self.log_event(
            db=db,
            tenant_id=tenant_id,
            event_type="unauthorized_access",
            status="failure",
            action="Unauthorized access attempt",
            user_id=user_id,
            description=f"Attempted to {action} {resource}",
            ip_address=ip_address,
            user_agent=user_agent
        )


# Global instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
