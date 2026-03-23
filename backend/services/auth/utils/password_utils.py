"""
Password hashing and verification using Argon2
"""

from passlib.context import CryptContext

# Configure Argon2 for password hashing (no 72-byte limit, more secure)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """
    Hash a password using Argon2
    
    Args:
        password: Plain text password (any length accepted)
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash
    
    Args:
        plain_password: Plain text password to verify (any length)
        hashed_password: Hashed password to compare against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
