"""Configuration settings for smart irrigation API."""

from typing import List


class Settings:
    """Application settings."""
    
    PROJECT_NAME: str = "Smart Irrigation API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000


settings = Settings()
