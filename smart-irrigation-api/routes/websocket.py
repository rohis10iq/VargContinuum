"""WebSocket routes for real-time sensor data streaming."""

import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Path

from services.websocket_manager import connection_manager
from services.influxdb_service import influxdb_service
from models.websocket import ConnectMessage, ErrorMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/sensors/{sensor_id}")
async def websocket_sensor_stream(
    websocket: WebSocket,
    sensor_id: str = Path(..., description="Sensor ID to stream data from")
):
    """
    WebSocket endpoint for streaming data from a specific sensor.
    
    Clients connecting to this endpoint will receive:
    1. Initial connection confirmation with latest sensor data
    2. Real-time updates whenever new data arrives for this sensor
    3. Periodic heartbeat messages (every 30 seconds)
    
    Args:
        websocket: WebSocket connection
        sensor_id: Unique sensor identifier
    """
    await connection_manager.connect(websocket, sensor_id=sensor_id)
    
    try:
        # Send connection confirmation
        connect_msg = ConnectMessage(
            message=f"Connected to sensor stream: {sensor_id}",
            sensor_id=sensor_id
        )
        await connection_manager.send_personal_message(
            json.loads(connect_msg.model_dump_json()),
            websocket
        )
        
        # Send latest sensor data if available
        try:
            latest_data = influxdb_service.get_sensor_latest(sensor_id)
            if latest_data:
                await connection_manager.send_personal_message(
                    {
                        "type": "update",
                        "message": "Latest sensor data",
                        "data": latest_data
                    },
                    websocket
                )
            else:
                await connection_manager.send_personal_message(
                    {
                        "type": "info",
                        "message": f"No recent data available for sensor {sensor_id}"
                    },
                    websocket
                )
        except Exception as e:
            logger.error(f"Error fetching latest data for sensor {sensor_id}: {e}")
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Receive messages from client (for potential future bidirectional communication)
                data = await websocket.receive_text()
                logger.debug(f"Received message from client on sensor {sensor_id}: {data}")
                
                # Echo acknowledgment (can be extended for client commands)
                await connection_manager.send_personal_message(
                    {
                        "type": "ack",
                        "message": "Message received",
                        "received_data": data
                    },
                    websocket
                )
            except WebSocketDisconnect:
                logger.info(f"Client disconnected from sensor stream: {sensor_id}")
                break
            except Exception as e:
                logger.error(f"Error in sensor stream {sensor_id}: {e}")
                error_msg = ErrorMessage(
                    error="Communication error",
                    details=str(e)
                )
                await connection_manager.send_personal_message(
                    json.loads(error_msg.model_dump_json()),
                    websocket
                )
                break
    
    except Exception as e:
        logger.error(f"Error in WebSocket connection for sensor {sensor_id}: {e}")
    
    finally:
        connection_manager.disconnect(websocket, sensor_id=sensor_id)


@router.websocket("/sensors/stream")
async def websocket_all_sensors_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming data from all sensors.
    
    Clients connecting to this endpoint will receive:
    1. Initial connection confirmation with summary of all sensors
    2. Real-time updates whenever any sensor data changes
    3. Periodic heartbeat messages (every 30 seconds)
    
    Args:
        websocket: WebSocket connection
    """
    await connection_manager.connect(websocket)
    
    try:
        # Send connection confirmation
        connect_msg = ConnectMessage(
            message="Connected to global sensor stream"
        )
        await connection_manager.send_personal_message(
            json.loads(connect_msg.model_dump_json()),
            websocket
        )
        
        # Send initial dashboard summary
        try:
            summary_data = influxdb_service.get_dashboard_summary()
            await connection_manager.send_personal_message(
                {
                    "type": "summary",
                    "message": "Current sensor summary",
                    "data": summary_data,
                    "count": len(summary_data)
                },
                websocket
            )
        except Exception as e:
            logger.error(f"Error fetching dashboard summary: {e}")
            await connection_manager.send_personal_message(
                {
                    "type": "info",
                    "message": "No sensor data available"
                },
                websocket
            )
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Receive messages from client (for potential future bidirectional communication)
                data = await websocket.receive_text()
                logger.debug(f"Received message from client on global stream: {data}")
                
                # Echo acknowledgment (can be extended for client commands)
                await connection_manager.send_personal_message(
                    {
                        "type": "ack",
                        "message": "Message received",
                        "received_data": data
                    },
                    websocket
                )
            except WebSocketDisconnect:
                logger.info("Client disconnected from global sensor stream")
                break
            except Exception as e:
                logger.error(f"Error in global sensor stream: {e}")
                error_msg = ErrorMessage(
                    error="Communication error",
                    details=str(e)
                )
                await connection_manager.send_personal_message(
                    json.loads(error_msg.model_dump_json()),
                    websocket
                )
                break
    
    except Exception as e:
        logger.error(f"Error in WebSocket connection for global stream: {e}")
    
    finally:
        connection_manager.disconnect(websocket)


@router.get("/stats")
async def get_connection_stats():
    """
    Get statistics about active WebSocket connections.
    
    Returns:
        Dictionary with connection statistics
    """
    return connection_manager.get_connection_stats()
