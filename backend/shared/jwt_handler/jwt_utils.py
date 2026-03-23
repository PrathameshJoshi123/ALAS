"""
JWT (JSON Web Token) Handler for authentication

Manages:
1. Access tokens (short-lived, 15 min default)
2. Refresh tokens (long-lived, 7 days default)
3. Token validation and claims extraction
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from uuid import UUID
from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)


class JWTHandler:
    """JWT token generation and validation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.SECRET_KEY
        self.algorithm = self.settings.ALGORITHM
    
    def create_access_token(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role_id: UUID,
        permissions: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant (critical for multi-tenancy)
            role_id: UUID of user's role
            permissions: Permission matrix from role
            expires_delta: Custom expiration time
            
        Returns:
            str: Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        claims = {
            "sub": str(user_id),  # Subject (user_id)
            "tenant_id": str(tenant_id),
            "role_id": str(role_id),
            "permissions": permissions,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        encoded_jwt = jwt.encode(
            claims,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def create_refresh_token(
        self,
        user_id: UUID,
        tenant_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token
        
        Refresh tokens are stored in Redis and can be revoked.
        They contain minimal claims to reduce size.
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant
            expires_delta: Custom expiration time
            
        Returns:
            str: Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        expire = datetime.utcnow() + expires_delta
        
        claims = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        encoded_jwt = jwt.encode(
            claims,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Dict: Token claims if valid
            
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise JWTError("Invalid token type")
            
            return payload
        
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise
    
    def get_user_id_from_token(self, token: str) -> UUID:
        """Extract user_id from token claims"""
        payload = self.verify_token(token, token_type="access")
        return UUID(payload.get("sub"))
    
    def get_tenant_id_from_token(self, token: str) -> UUID:
        """Extract tenant_id from token claims"""
        payload = self.verify_token(token, token_type="access")
        return UUID(payload.get("tenant_id"))
    
    def get_permissions_from_token(self, token: str) -> Dict[str, Any]:
        """Extract permissions from token claims"""
        payload = self.verify_token(token, token_type="access")
        return payload.get("permissions", {})


# Global instance
_jwt_handler = None


def get_jwt_handler() -> JWTHandler:
    """Get or create global JWT handler instance"""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler


# Convenience functions
def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    role_id: UUID,
    permissions: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create access token"""
    return get_jwt_handler().create_access_token(
        user_id, tenant_id, role_id, permissions, expires_delta
    )


def create_refresh_token(
    user_id: UUID,
    tenant_id: UUID,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create refresh token"""
    return get_jwt_handler().create_refresh_token(user_id, tenant_id, expires_delta)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify token"""
    return get_jwt_handler().verify_token(token, token_type)
