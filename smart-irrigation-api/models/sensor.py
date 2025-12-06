"""Sensor data models for smart irrigation API."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    """Single sensor reading with timestamp."""
    timestamp: datetime = Field(..., description="ISO8601 timestamp of the reading")
    moisture: Optional[float] = Field(None, description="Soil moisture percentage (0-100)")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Air humidity percentage (0-100)")
    light: Optional[int] = Field(None, description="Light intensity (0-1023)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-12-06T14:30:00Z",
                "moisture": 45.2,
                "temperature": 22.1,
                "humidity": 65.5,
                "light": 512
            }
        }


class SensorInfo(BaseModel):
    """Sensor metadata and basic information."""
    sensor_id: str = Field(..., description="Unique sensor identifier (e.g., V1, V2)")
    name: str = Field(..., description="Human-readable sensor name")
    zone_id: int = Field(..., description="Zone number (1-4 for orchard, 5 for potato)")
    zone_name: str = Field(..., description="Zone description")
    status: str = Field(..., description="Sensor status: active, inactive, error")
    last_seen: Optional[datetime] = Field(None, description="Last data transmission time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "V1",
                "name": "Orchard Zone 1 Sensor",
                "zone_id": 1,
                "zone_name": "Orchard Zone 1",
                "status": "active",
                "last_seen": "2025-12-06T14:30:00Z"
            }
        }


class SensorDetail(SensorInfo):
    """Detailed sensor information including latest reading."""
    latest_reading: Optional[SensorReading] = Field(None, description="Most recent sensor reading")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "V1",
                "name": "Orchard Zone 1 Sensor",
                "zone_id": 1,
                "zone_name": "Orchard Zone 1",
                "status": "active",
                "last_seen": "2025-12-06T14:30:00Z",
                "latest_reading": {
                    "timestamp": "2025-12-06T14:30:00Z",
                    "moisture": 45.2,
                    "temperature": 22.1,
                    "humidity": 65.5,
                    "light": 512
                }
            }
        }


class SensorHistory(BaseModel):
    """Time-series data for a sensor."""
    sensor_id: str = Field(..., description="Sensor identifier")
    start_time: datetime = Field(..., description="Query start time")
    end_time: datetime = Field(..., description="Query end time")
    interval: str = Field(..., description="Data aggregation interval (e.g., 1h, 15m)")
    readings: List[SensorReading] = Field(..., description="Time-series readings")
    count: int = Field(..., description="Number of data points")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "V1",
                "start_time": "2025-12-05T14:30:00Z",
                "end_time": "2025-12-06T14:30:00Z",
                "interval": "1h",
                "readings": [
                    {
                        "timestamp": "2025-12-06T14:00:00Z",
                        "moisture": 45.2,
                        "temperature": 22.1,
                        "humidity": 65.5,
                        "light": 512
                    }
                ],
                "count": 24
            }
        }


class SensorSummary(BaseModel):
    """Summary of all sensors for dashboard grid."""
    sensor_id: str = Field(..., description="Sensor identifier")
    name: str = Field(..., description="Sensor name")
    zone_id: int = Field(..., description="Zone number")
    status: str = Field(..., description="Sensor status")
    latest_reading: Optional[SensorReading] = Field(None, description="Latest sensor data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "V1",
                "name": "Orchard Zone 1 Sensor",
                "zone_id": 1,
                "status": "active",
                "latest_reading": {
                    "timestamp": "2025-12-06T14:30:00Z",
                    "moisture": 45.2,
                    "temperature": 22.1,
                    "humidity": 65.5,
                    "light": 512
                }
            }
        }


class SensorListResponse(BaseModel):
    """Response model for listing all sensors."""
    sensors: List[SensorInfo] = Field(..., description="List of all sensors")
    count: int = Field(..., description="Total number of sensors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensors": [
                    {
                        "sensor_id": "V1",
                        "name": "Orchard Zone 1 Sensor",
                        "zone_id": 1,
                        "zone_name": "Orchard Zone 1",
                        "status": "active",
                        "last_seen": "2025-12-06T14:30:00Z"
                    }
                ],
                "count": 5
            }
        }


class SensorSummaryResponse(BaseModel):
    """Response model for sensor summary endpoint."""
    summary: List[SensorSummary] = Field(..., description="Summary of all sensors")
    count: int = Field(..., description="Total number of sensors")
    cached: bool = Field(..., description="Whether this response was served from cache")
    cache_timestamp: Optional[datetime] = Field(None, description="When this cache entry was created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": [
                    {
                        "sensor_id": "V1",
                        "name": "Orchard Zone 1 Sensor",
                        "zone_id": 1,
                        "status": "active",
                        "latest_reading": {
                            "timestamp": "2025-12-06T14:30:00Z",
                            "moisture": 45.2,
                            "temperature": 22.1,
                            "humidity": 65.5,
                            "light": 512
                        }
                    }
                ],
                "count": 5,
                "cached": True,
                "cache_timestamp": "2025-12-06T14:25:00Z"
            }
        }
