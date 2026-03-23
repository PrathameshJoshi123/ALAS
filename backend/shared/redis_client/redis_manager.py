"""
Redis Client for session management and caching

Responsibilities:
1. Store and manage refresh tokens
2. Cache role permissions with TTL
3. Track active sessions
"""

import redis
import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import timedelta
from config.settings import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for session and cache management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = redis.from_url(self.settings.REDIS_URL, decode_responses=True)
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Redis connection on initialization"""
        try:
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise
    
    # ==================== REFRESH TOKEN MANAGEMENT ====================
    
    def store_refresh_token(
        self,
        user_id: UUID,
        tenant_id: UUID,
        refresh_token: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store refresh token in Redis
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant
            refresh_token: JWT refresh token
            ttl: Time-to-live in seconds (default from settings)
            
        Returns:
            bool: True if stored successfully
        """
        if ttl is None:
            ttl = int(self.settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        
        key = f"refresh_token:{tenant_id}:{user_id}"
        
        try:
            self.redis_client.set(key, refresh_token, ex=ttl)
            logger.info(f"Refresh token stored for user {user_id} in tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store refresh token: {str(e)}")
            return False
    
    def get_refresh_token(self, user_id: UUID, tenant_id: UUID) -> Optional[str]:
        """
        Retrieve refresh token from Redis
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant
            
        Returns:
            str: Refresh token if exists, None otherwise
        """
        key = f"refresh_token:{tenant_id}:{user_id}"
        
        try:
            token = self.redis_client.get(key)
            return token
        except Exception as e:
            logger.error(f"Failed to retrieve refresh token: {str(e)}")
            return None
    
    def revoke_refresh_token(self, user_id: UUID, tenant_id: UUID) -> bool:
        """
        Revoke (delete) refresh token
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant
            
        Returns:
            bool: True if revoked successfully
        """
        key = f"refresh_token:{tenant_id}:{user_id}"
        
        try:
            self.redis_client.delete(key)
            logger.info(f"Refresh token revoked for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {str(e)}")
            return False
    
    def revoke_all_user_tokens(self, user_id: UUID, tenant_id: UUID) -> bool:
        """
        Revoke all refresh tokens for a user (logout all sessions)
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant
            
        Returns:
            bool: True if revoked successfully
        """
        key_pattern = f"refresh_token:{tenant_id}:{user_id}"
        
        try:
            self.redis_client.delete(key_pattern)
            logger.info(f"All refresh tokens revoked for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke all tokens: {str(e)}")
            return False
    
    # ==================== PERMISSION CACHING ====================
    
    def cache_role_permissions(
        self,
        role_id: UUID,
        tenant_id: UUID,
        permissions: Dict[str, Any],
        ttl: int = 3600  # 1 hour default
    ) -> bool:
        """
        Cache role permissions in Redis with TTL
        
        Args:
            role_id: UUID of role
            tenant_id: UUID of tenant
            permissions: Permission matrix dictionary
            ttl: Time-to-live in seconds
            
        Returns:
            bool: True if cached successfully
        """
        key = f"role_permissions:{tenant_id}:{role_id}"
        
        try:
            permissions_json = json.dumps(permissions)
            self.redis_client.set(key, permissions_json, ex=ttl)
            logger.info(f"Permissions cached for role {role_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache permissions: {str(e)}")
            return False
    
    def get_cached_permissions(
        self,
        role_id: UUID,
        tenant_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached role permissions
        
        Args:
            role_id: UUID of role
            tenant_id: UUID of tenant
            
        Returns:
            Dict: Permission matrix if cached, None otherwise
        """
        key = f"role_permissions:{tenant_id}:{role_id}"
        
        try:
            permissions_json = self.redis_client.get(key)
            if permissions_json:
                return json.loads(permissions_json)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve cached permissions: {str(e)}")
            return None
    
    def invalidate_role_cache(self, role_id: UUID, tenant_id: UUID) -> bool:
        """
        Invalidate cached permissions for a role
        
        Args:
            role_id: UUID of role
            tenant_id: UUID of tenant
            
        Returns:
            bool: True if invalidated successfully
        """
        key = f"role_permissions:{tenant_id}:{role_id}"
        
        try:
            self.redis_client.delete(key)
            logger.info(f"Permission cache invalidated for role {role_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate role cache: {str(e)}")
            return False
    
    # ==================== ACTIVE SESSIONS ====================
    
    def create_session(
        self,
        user_id: UUID,
        tenant_id: UUID,
        session_data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """
        Create user session in Redis
        
        Args:
            user_id: UUID of user
            tenant_id: UUID of tenant
            session_data: Session metadata
            ttl: Time-to-live in seconds
            
        Returns:
            bool: True if session created
        """
        key = f"session:{tenant_id}:{user_id}"
        
        try:
            session_json = json.dumps(session_data)
            self.redis_client.set(key, session_json, ex=ttl)
            logger.info(f"Session created for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            return False
    
    def get_session(self, user_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve user session"""
        key = f"session:{tenant_id}:{user_id}"
        
        try:
            session_json = self.redis_client.get(key)
            if session_json:
                return json.loads(session_json)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve session: {str(e)}")
            return None
    
    def destroy_session(self, user_id: UUID, tenant_id: UUID) -> bool:
        """Destroy user session"""
        key = f"session:{tenant_id}:{user_id}"
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to destroy session: {str(e)}")
            return False
    
    def close(self):
        """Close Redis connection"""
        try:
            self.redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")


# Global instance
_redis_client = None


def get_redis_client() -> RedisClient:
    """Get or create global Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
