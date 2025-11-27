"""Sensor data models."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    """Model for a single sensor reading."""
    
    timestamp: datetime = Field(..., description="Time of the reading")
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., description="Unit of measurement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-28T10:00:00Z",
                "value": 25.5,
                "unit": "°C"
            }
        }


class SensorDetail(BaseModel):
    """Model for sensor details."""
    
    id: str = Field(..., description="Unique sensor identifier")
    name: str = Field(..., description="Human-readable sensor name")
    type: str = Field(..., description="Type of sensor (temperature, humidity, soil_moisture, etc.)")
    location: Optional[str] = Field(None, description="Physical location of the sensor")
    unit: str = Field(..., description="Unit of measurement")
    status: str = Field(default="active", description="Sensor status (active, inactive, error)")
    last_reading: Optional[SensorReading] = Field(None, description="Most recent reading")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "sensor_temp_001",
                "name": "Temperature Sensor 1",
                "type": "temperature",
                "location": "Field A - Zone 1",
                "unit": "°C",
                "status": "active",
                "last_reading": {
                    "timestamp": "2025-11-28T10:00:00Z",
                    "value": 25.5,
                    "unit": "°C"
                }
            }
        }


class SensorList(BaseModel):
    """Model for list of sensors."""
    
    sensors: List[SensorDetail] = Field(..., description="List of all sensors")
    total: int = Field(..., description="Total number of sensors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensors": [
                    {
                        "id": "sensor_temp_001",
                        "name": "Temperature Sensor 1",
                        "type": "temperature",
                        "location": "Field A - Zone 1",
                        "unit": "°C",
                        "status": "active"
                    }
                ],
                "total": 1
            }
        }


class SensorHistory(BaseModel):
    """Model for sensor historical data."""
    
    sensor_id: str = Field(..., description="Sensor identifier")
    readings: List[SensorReading] = Field(..., description="Historical readings")
    start_time: datetime = Field(..., description="Start of the time range")
    end_time: datetime = Field(..., description="End of the time range")
    count: int = Field(..., description="Number of readings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "sensor_temp_001",
                "readings": [
                    {
                        "timestamp": "2025-11-28T10:00:00Z",
                        "value": 25.5,
                        "unit": "°C"
                    }
                ],
                "start_time": "2025-11-28T00:00:00Z",
                "end_time": "2025-11-28T23:59:59Z",
                "count": 1
            }
        }


class SensorSummary(BaseModel):
    """Model for sensor summary statistics."""
    
    sensor_id: str = Field(..., description="Sensor identifier")
    name: str = Field(..., description="Sensor name")
    type: str = Field(..., description="Sensor type")
    current_value: Optional[float] = Field(None, description="Current reading value")
    min_value: Optional[float] = Field(None, description="Minimum value in period")
    max_value: Optional[float] = Field(None, description="Maximum value in period")
    avg_value: Optional[float] = Field(None, description="Average value in period")
    unit: str = Field(..., description="Unit of measurement")
    status: str = Field(..., description="Sensor status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "sensor_temp_001",
                "name": "Temperature Sensor 1",
                "type": "temperature",
                "current_value": 25.5,
                "min_value": 18.2,
                "max_value": 32.1,
                "avg_value": 24.8,
                "unit": "°C",
                "status": "active"
            }
        }


class SensorsSummaryResponse(BaseModel):
    """Model for summary of all sensors."""
    
    summaries: List[SensorSummary] = Field(..., description="Summary for each sensor")
    total_sensors: int = Field(..., description="Total number of sensors")
    active_sensors: int = Field(..., description="Number of active sensors")
    timestamp: datetime = Field(..., description="Time of summary generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "summaries": [
                    {
                        "sensor_id": "sensor_temp_001",
                        "name": "Temperature Sensor 1",
                        "type": "temperature",
                        "current_value": 25.5,
                        "min_value": 18.2,
                        "max_value": 32.1,
                        "avg_value": 24.8,
                        "unit": "°C",
                        "status": "active"
                    }
                ],
                "total_sensors": 1,
                "active_sensors": 1,
                "timestamp": "2025-11-28T10:00:00Z"
            }
        }
