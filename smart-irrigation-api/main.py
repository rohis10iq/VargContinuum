"""Main FastAPI application for smart irrigation API."""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes import auth, sensors, websocket
from services.influxdb_service import influxdb_service
from services.websocket_manager import connection_manager


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
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Connect to InfluxDB
    try:
        influxdb_service.connect()
        print("✅ Connected to InfluxDB")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to InfluxDB: {e}")
        print("   Sensor endpoints will not work until InfluxDB is configured.")
    
    # Start WebSocket heartbeat task
    try:
        connection_manager.heartbeat_task = asyncio.create_task(
            connection_manager.start_heartbeat()
        )
        print("✅ WebSocket heartbeat started")
    except Exception as e:
        print(f"⚠️ Warning: Could not start WebSocket heartbeat: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    # Close InfluxDB connection
    influxdb_service.close()
    print("🔌 Disconnected from InfluxDB")
    
    # Cancel WebSocket heartbeat task
    if connection_manager.heartbeat_task:
        connection_manager.heartbeat_task.cancel()
        try:
            await connection_manager.heartbeat_task
        except asyncio.CancelledError:
            pass
        print("🔌 WebSocket heartbeat stopped")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Smart Irrigation API",
        "version": settings.VERSION,
        "docs": "/docs",
        "websocket_endpoints": {
            "specific_sensor": "/ws/sensors/{sensor_id}",
            "all_sensors": "/ws/sensors/stream"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    ws_stats = connection_manager.get_connection_stats()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "websocket_connections": ws_stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
