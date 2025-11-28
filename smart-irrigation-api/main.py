"""Main FastAPI application for smart irrigation API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes import auth, sensors
from services.influxdb_service import influxdb_service


# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(sensors.router)


@app.on_event("startup")
async def startup_event():
    """Initialize InfluxDB connection on startup."""
    try:
        influxdb_service.connect()
        print("✅ Connected to InfluxDB")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to InfluxDB: {e}")
        print("   Sensor endpoints will not work until InfluxDB is configured.")


@app.on_event("shutdown")
async def shutdown_event():
    """Close InfluxDB connection on shutdown."""
    influxdb_service.close()
    print("🔌 Disconnected from InfluxDB")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Smart Irrigation API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
