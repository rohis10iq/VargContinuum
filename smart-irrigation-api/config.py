"""Configuration settings for smart irrigation API."""

import os
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
    
    # Database settings
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "smart_irrigation")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "postgres")
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # InfluxDB settings for sensor data
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "your-influxdb-token")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "smart-irrigation")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "sensor-data")
    
    # Cache settings
    CACHE_TTL_SECONDS: int = 300  # 5 minutes cache for summary endpoint


settings = Settings()
