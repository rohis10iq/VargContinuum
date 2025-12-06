"""WebSocket message models and schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SensorReadingMessage(BaseModel):
    """Real-time sensor reading broadcast via WebSocket."""
    
    sensor_id: str = Field(..., description="Sensor identifier (V1-V5)")
    moisture: Optional[float] = Field(None, description="Soil moisture percentage", ge=0, le=100)
    temperature: Optional[float] = Field(None, description="Temperature in Celsius", ge=-50, le=80)
    humidity: Optional[float] = Field(None, description="Relative humidity percentage", ge=0, le=100)
    light: Optional[float] = Field(None, description="Light intensity in lux", ge=0)
    timestamp: str = Field(..., description="ISO8601 timestamp of reading")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "V1",
                "moisture": 45.2,
                "temperature": 22.1,
                "humidity": 65.5,
                "light": 800.0,
                "timestamp": "2025-12-06T14:30:00Z"
            }
        }


class WebSocketMessage(BaseModel):
    """Generic WebSocket message wrapper."""
    
    type: str = Field(..., description="Message type: 'sensor_reading', 'connection_status', 'error'")
    data: dict = Field(..., description="Message payload")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


class ConnectionStatusMessage(BaseModel):
    """Connection status notification."""
    
    status: str = Field(..., description="'connected' or 'disconnected'")
    client_id: str = Field(..., description="Unique client identifier")
    active_clients: int = Field(..., description="Number of active WebSocket connections")
    timestamp: str = Field(..., description="ISO8601 timestamp")


class ErrorMessage(BaseModel):
    """Error notification message."""
    
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    timestamp: str = Field(..., description="ISO8601 timestamp")
