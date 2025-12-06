"""WebSocket connection manager for handling concurrent clients."""
from typing import Dict, Set
from datetime import datetime, timedelta
import json
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self.client_metadata: Dict[WebSocket, dict] = {}
        self.last_broadcast_time: Dict[str, datetime] = {}
        self.rate_limit_seconds = 1.0  # Max 1 update per second per sensor
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket connection
            client_id: Unique identifier for this client
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.utcnow().isoformat() + "Z",
            "messages_received": 0
        }
        logger.info(f"Client {client_id} connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a disconnected WebSocket.
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.discard(websocket)
            client_id = self.client_metadata.pop(websocket, {}).get("client_id", "unknown")
            logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict, sensor_id: str) -> None:
        """
        Broadcast a message to all connected clients with rate limiting.
        
        Args:
            message: Message dict to broadcast (SensorReadingMessage serialized)
            sensor_id: Sensor ID for rate limiting
        
        Returns:
            True if broadcast occurred, False if rate-limited
        """
        # Check rate limit
        now = datetime.utcnow()
        last_broadcast = self.last_broadcast_time.get(sensor_id)
        
        if last_broadcast:
            elapsed = (now - last_broadcast).total_seconds()
            if elapsed < self.rate_limit_seconds:
                logger.debug(f"Rate-limited broadcast for sensor {sensor_id}")
                return False
        
        # Update last broadcast time
        self.last_broadcast_time[sensor_id] = now
        
        # Broadcast to all clients
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return False
        
        dead_connections = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection)
        
        return len(self.active_connections) > 0
    
    async def send_personal(self, websocket: WebSocket, message: dict) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            websocket: Target WebSocket connection
            message: Message dict to send
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if websocket in self.active_connections:
                await websocket.send_json(message)
                return True
        except Exception as e:
            logger.warning(f"Error sending personal message: {e}")
            self.disconnect(websocket)
        
        return False
    
    def get_active_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_client_metadata(self, websocket: WebSocket) -> dict:
        """Get metadata for a specific client."""
        return self.client_metadata.get(websocket, {})


# Global instance
ws_manager = WebSocketManager()
