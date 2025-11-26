"""User models for authentication."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Model for user registration."""
    
    email: EmailStr
    password: str
    role: str = "farmer"


class UserLogin(BaseModel):
    """Model for user login."""
    
    email: EmailStr
    password: str


class Token(BaseModel):
    """Model for JWT token response."""
    
    access_token: str
    token_type: str = "bearer"
