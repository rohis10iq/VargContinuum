"""Authentication utilities for JWT and password hashing."""

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from config import settings

# Password hashing context (bcrypt)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(password: str) -> str:
    """Hash a plain password."""
    # Bcrypt has a 72-byte limit – enforce safety
    if len(password.encode("utf-8")) > 72:
        password = password[:72]

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    if len(plain_password.encode("utf-8")) > 72:
        plain_password = plain_password[:72]

    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token."""
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload as dict
    
    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.JWTClaimsError:
        raise ValueError("Token claims are invalid")
    except jwt.JWTError:
        raise ValueError("Could not validate token")

