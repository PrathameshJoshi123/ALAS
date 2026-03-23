"""
Shared authentication dependencies for FastAPI
"""

from fastapi import HTTPException, status, Request, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from shared.database.db import get_db
from shared.jwt_handler.jwt_utils import verify_token
from shared.database.models import User
import logging

logger = logging.getLogger(__name__)


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
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header"
            )
        
        token = auth_header.replace("Bearer ", "")
        
        # Verify token and get tenant/user info
        payload = verify_token(token)
        
        # Extract user_id from "sub" claim (JWT standard)
        user_id_str = payload.get("sub")
        if not user_id_str:
            logger.error("Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        try:
            user_id = UUID(user_id_str)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user_id format in token: {user_id_str}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Extract tenant_id
        tenant_id_str = payload.get("tenant_id")
        if not tenant_id_str:
            logger.error("Token missing 'tenant_id' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        try:
            tenant_id = UUID(tenant_id_str)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid tenant_id format in token: {tenant_id_str}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Fetch user from database
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id
        ).first()
        
        if not user:
            logger.warning(f"User not found: {user_id} in tenant {tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
