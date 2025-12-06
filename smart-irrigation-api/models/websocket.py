"""WebSocket message models for real-time sensor data streaming."""

from datetime import datetime, timezone
from typing import Optional, Any, Dict, Literal
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    UPDATE = "update"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""
    
    type: MessageType = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Message timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Message payload")


class SensorUpdateMessage(BaseModel):
    """Sensor data update message for WebSocket."""
    
    type: Literal[MessageType.UPDATE] = MessageType.UPDATE
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sensor_id: str = Field(..., description="Sensor identifier")
    sensor_type: str = Field(..., description="Type of sensor")
    value: float = Field(..., description="Sensor reading value")
    location: Optional[str] = Field(None, description="Sensor location")


class HeartbeatMessage(BaseModel):
    """Heartbeat/ping message to keep connection alive."""
    
    type: Literal[MessageType.HEARTBEAT] = MessageType.HEARTBEAT
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = Field(default="ping", description="Heartbeat message")


class ErrorMessage(BaseModel):
    """Error notification message."""
    
    type: Literal[MessageType.ERROR] = MessageType.ERROR
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


class ConnectMessage(BaseModel):
    """Connection confirmation message."""
    
    type: Literal[MessageType.CONNECT] = MessageType.CONNECT
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = Field(..., description="Welcome message")
    sensor_id: Optional[str] = Field(None, description="Sensor ID if specific sensor stream")


class LiveSensorMessage(BaseModel):
    """
    Live sensor data message matching B2.2 specification format.
    
    Format: { "sensor_id": "V1", "moisture": 45.2, "temperature": 22.1, "timestamp": "2025-11-25T14:30:00Z" }
    """
    
    model_config = {"ser_json_timedelta": "iso8601"}
    
    sensor_id: str = Field(..., description="Sensor identifier (e.g., V1)")
    moisture: Optional[float] = Field(None, description="Soil moisture percentage")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Air humidity percentage")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Reading timestamp")
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override to format timestamp in ISO format."""
        data = super().model_dump(**kwargs)
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')
        return data
    
    def to_broadcast_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for WebSocket broadcast."""
        result = {
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        if self.moisture is not None:
            result["moisture"] = self.moisture
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.humidity is not None:
            result["humidity"] = self.humidity
        return result

