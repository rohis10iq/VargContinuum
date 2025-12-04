"""WebSocket connection manager for handling real-time client connections."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect

from models.websocket import HeartbeatMessage, SensorUpdateMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time sensor data streaming."""
    
    def __init__(self):
        """Initialize connection manager."""
        # All connections for global stream
        self.active_connections: List[WebSocket] = []
        
        # Connections grouped by sensor_id for specific sensor streams
        self.sensor_connections: Dict[str, List[WebSocket]] = {}
        
        # Heartbeat task
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.heartbeat_interval: int = 30  # seconds
        
    async def connect(self, websocket: WebSocket, sensor_id: Optional[str] = None):
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
            sensor_id: Optional sensor ID for specific sensor subscription
        """
        await websocket.accept()
        
        if sensor_id:
            # Add to specific sensor connections
            if sensor_id not in self.sensor_connections:
                self.sensor_connections[sensor_id] = []
            self.sensor_connections[sensor_id].append(websocket)
            logger.info(f"Client connected to sensor stream: {sensor_id}")
        else:
            # Add to global connections
            self.active_connections.append(websocket)
            logger.info("Client connected to global sensor stream")
    
    def disconnect(self, websocket: WebSocket, sensor_id: Optional[str] = None):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            sensor_id: Optional sensor ID for specific sensor subscription
        """
        if sensor_id:
            # Remove from specific sensor connections
            if sensor_id in self.sensor_connections:
                if websocket in self.sensor_connections[sensor_id]:
                    self.sensor_connections[sensor_id].remove(websocket)
                    logger.info(f"Client disconnected from sensor stream: {sensor_id}")
                
                # Clean up empty lists
                if not self.sensor_connections[sensor_id]:
                    del self.sensor_connections[sensor_id]
        else:
            # Remove from global connections
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info("Client disconnected from global sensor stream")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific client.
        
        Args:
            message: Message data to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients (global stream).
        
        Args:
            message: Message data to broadcast
        """
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
                logger.warning("Client disconnected during broadcast")
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_sensor(self, sensor_id: str, message: dict):
        """
        Broadcast a message to all clients subscribed to a specific sensor.
        
        Args:
            sensor_id: Sensor identifier
            message: Message data to broadcast
        """
        if sensor_id not in self.sensor_connections:
            return
        
        disconnected = []
        
        for connection in self.sensor_connections[sensor_id]:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
                logger.warning(f"Client disconnected during sensor broadcast: {sensor_id}")
            except Exception as e:
                logger.error(f"Error broadcasting to sensor client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, sensor_id)
    
    async def broadcast_sensor_update(
        self, 
        sensor_id: str, 
        sensor_type: str, 
        value: float, 
        location: Optional[str] = None
    ):
        """
        Broadcast a sensor update to relevant clients.
        
        Args:
            sensor_id: Sensor identifier
            sensor_type: Type of sensor
            value: Sensor reading value
            location: Optional sensor location
        """
        # Create sensor update message
        update_message = SensorUpdateMessage(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            value=value,
            location=location
        )
        
        message_dict = json.loads(update_message.model_dump_json())
        
        # Broadcast to global stream
        await self.broadcast(message_dict)
        
        # Broadcast to specific sensor subscribers
        await self.broadcast_to_sensor(sensor_id, message_dict)
        
        logger.info(f"Broadcasted update for sensor {sensor_id}: {value}")
    
    async def start_heartbeat(self):
        """Start periodic heartbeat to keep connections alive."""
        logger.info(f"Starting heartbeat with {self.heartbeat_interval}s interval")
        
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat to all connections
                heartbeat = HeartbeatMessage()
                heartbeat_dict = json.loads(heartbeat.model_dump_json())
                
                # Send to global connections
                for connection in self.active_connections[:]:  # Copy to avoid modification during iteration
                    try:
                        await connection.send_json(heartbeat_dict)
                    except Exception as e:
                        logger.error(f"Heartbeat failed for global connection: {e}")
                        self.disconnect(connection)
                
                # Send to sensor-specific connections
                for sensor_id, connections in list(self.sensor_connections.items()):
                    for connection in connections[:]:  # Copy to avoid modification during iteration
                        try:
                            await connection.send_json(heartbeat_dict)
                        except Exception as e:
                            logger.error(f"Heartbeat failed for sensor {sensor_id} connection: {e}")
                            self.disconnect(connection, sensor_id)
                
                total_connections = len(self.active_connections) + sum(
                    len(conns) for conns in self.sensor_connections.values()
                )
                logger.debug(f"Heartbeat sent to {total_connections} connections")
                
            except asyncio.CancelledError:
                logger.info("Heartbeat task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    def get_connection_stats(self) -> dict:
        """
        Get statistics about active connections.
        
        Returns:
            Dictionary with connection statistics
        """
        sensor_stats = {
            sensor_id: len(connections)
            for sensor_id, connections in self.sensor_connections.items()
        }
        
        return {
            "global_connections": len(self.active_connections),
            "sensor_connections": sensor_stats,
            "total_connections": len(self.active_connections) + sum(
                len(conns) for conns in self.sensor_connections.values()
            )
        }


# Global connection manager instance
connection_manager = ConnectionManager()
