"""WebSocket endpoints for real-time sensor data streaming."""
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.exceptions import WebSocketException
import uuid

from models.websocket import SensorReadingMessage, WebSocketMessage, ConnectionStatusMessage, ErrorMessage
from utils.websocket_manager import ws_manager
from utils.mqtt_client import get_mqtt_client
from utils.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/sensors")
async def websocket_sensor_endpoint(
    websocket: WebSocket,
    token: str = Query(None, description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time sensor data streaming.
    
    **Usage:**
    - Connect: `ws://localhost:8000/ws/sensors?token=YOUR_JWT_TOKEN`
    - Receives messages in format:
        ```json
        {
            "type": "sensor_reading",
            "data": {
                "sensor_id": "V1",
                "moisture": 45.2,
                "temperature": 22.1,
                "humidity": 65.5,
                "light": 800.0
            },
            "timestamp": "2025-12-06T14:30:00Z"
        }
        ```
    
    **Authentication:**
    - Requires valid JWT token as query parameter
    - Token must be obtained from /auth/login endpoint
    
    **Features:**
    - Graceful disconnection handling
    - Rate-limited broadcasts (max 1 update/second/sensor)
    - Connection status notifications
    - Automatic cleanup on disconnect
    """
    
    # Generate unique client ID
    client_id = str(uuid.uuid4())[:8]
    
    # Authenticate
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        return
    
    try:
        # Verify token using existing auth utility
        payload = verify_token(token)
        user_id = payload.get("user_id")
        logger.info(f"WebSocket authentication successful for user {user_id}")
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Accept connection
    await ws_manager.connect(websocket, client_id)
    
    # Send connection status notification
    connection_status = {
        "type": "connection_status",
        "data": {
            "status": "connected",
            "client_id": client_id,
            "active_clients": ws_manager.get_active_count()
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    await ws_manager.send_personal(websocket, connection_status)
    
    # Initialize MQTT client and set broadcast callback
    mqtt = get_mqtt_client()
    
    async def broadcast_to_websocket(sensor_data: dict, sensor_id: str):
        """Broadcast sensor data to all WebSocket clients."""
        try:
            # Create WebSocket message wrapper
            message = WebSocketMessage(
                type="sensor_reading",
                data=sensor_data,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
            await ws_manager.broadcast(message.model_dump(), sensor_id)
        except Exception as e:
            logger.error("Error broadcasting to WebSocket clients.")
            logger.debug("Broadcasting exception details:", exc_info=True)
    
    # Set the broadcast callback
    mqtt.set_broadcast_callback(broadcast_to_websocket)
    
    # Connect MQTT if not already connected
    if not mqtt.is_connected():
        logger.info("Connecting MQTT client...")
        mqtt.connect()
    
    # Keep connection alive and handle incoming messages
    try:
        while True:
            # Wait for incoming messages from client
            # (currently server-only mode, but support future client->server commands)
            data = await websocket.receive_text()
            logger.debug(f"Received from client {client_id}: {data}")
            
            # Could implement client-side commands here in future
            # For now, just acknowledge
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnection for client {client_id}")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        ws_manager.disconnect(websocket)
        try:
            error_msg = ErrorMessage(
                error=str(e),
                code="WS_ERROR",
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
            await ws_manager.send_personal(websocket, error_msg.model_dump())
        except:
            pass
