"""
Security utilities for password hashing and verification.
Centralizing these ensures consistency across the application.
"""
import bcrypt
import logging
from ..constants.security_constants import BCRYPT_ROUNDS

logger = logging.getLogger(__name__)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    pwd_bytes = password.encode('utf-8')
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed one.
    Supports on-the-fly identification of legacy plain-text passwords.
    """
    if not hashed_password:
        return False
        
    # Identification of bcrypt hash (starts with $2b$, $2a$, or $2y$)
    is_bcrypt = hashed_password.startswith(('$2a$', '$2b$', '$2y$'))
    
    if is_bcrypt:
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying bcrypt hash: {e}")
            return False
    else:
        # Legacy/Plain-text fallback
        # If it's not a bcrypt hash, we compare directly (but this shouldn't happen in production)
        logger.warning("Detected non-bcrypt password format. Falling back to plain-text comparison.")
        return plain_password == hashed_password

def is_hashed(password_str: str) -> bool:
    """
    Check if a string is a valid bcrypt hash.
    """
    return password_str.startswith(('$2a$', '$2b$', '$2y$')) and len(password_str) >= 59

def check_password_history(new_password: str, history: list[str]) -> bool:
    """
    Check if the new password matches any of the previously used passwords.
    """
    for old_hash in history:
        if verify_password(new_password, old_hash):
            return True
    return False
