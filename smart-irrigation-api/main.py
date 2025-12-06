"""Main FastAPI application for smart irrigation API."""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes import auth, sensors, websocket, irrigation
from services.influxdb_service import influxdb_service
from services.websocket_manager import connection_manager
from services.mqtt_service import mqtt_service


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
app.include_router(irrigation.router)


async def handle_mqtt_sensor_update(data: dict):
    """
    Handle sensor updates from MQTT broker.
    
    This callback is triggered when MQTT receives sensor data,
    and broadcasts it to connected WebSocket clients with rate limiting.
    """
    await connection_manager.broadcast_live_sensor_data(data)


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
    
    # Connect to MQTT broker
    try:
        loop = asyncio.get_event_loop()
        mqtt_service.on_sensor_update = handle_mqtt_sensor_update
        mqtt_service.connect(loop)
        print(f"✅ MQTT client started (broker: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT})")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to MQTT broker: {e}")
        print("   Live sensor updates via MQTT will not work.")


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
    
    # Disconnect MQTT client
    try:
        mqtt_service.disconnect()
        print("🔌 Disconnected from MQTT broker")
    except Exception as e:
        print(f"⚠️ Error disconnecting MQTT: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Smart Irrigation API",
        "version": settings.VERSION,
        "docs": "/docs",
        "websocket_endpoints": {
            "live_stream": "/ws/sensors/live?token=<jwt_token>",
            "specific_sensor": "/ws/sensors/{sensor_id}?token=<jwt_token>",
            "all_sensors": "/ws/sensors/stream?token=<jwt_token>"
        },
        "note": "WebSocket endpoints require JWT authentication token in query parameter"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    ws_stats = connection_manager.get_connection_stats()
    mqtt_status = mqtt_service.get_status()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "websocket_connections": ws_stats,
        "mqtt_status": mqtt_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
