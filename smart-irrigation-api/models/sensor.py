"""Sensor data models for time-series storage."""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    """Model for a single sensor reading."""
    
    sensor_id: str = Field(..., description="Unique identifier for the sensor")
    sensor_type: str = Field(..., description="Type of sensor (e.g., soil_moisture, temperature)")
    value: float = Field(..., description="Sensor reading value")
    location: Optional[str] = Field(None, description="Physical location of sensor")
    timestamp: Optional[datetime] = Field(None, description="Reading timestamp (defaults to now)")


class SensorQuery(BaseModel):
    """Model for querying sensor data."""
    
    sensor_id: Optional[str] = Field(None, description="Filter by sensor ID")
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    location: Optional[str] = Field(None, description="Filter by location")
    start_time: Optional[datetime] = Field(None, description="Query start time")
    stop_time: Optional[datetime] = Field(None, description="Query end time")
    aggregation_window: Optional[str] = Field(None, description="Aggregation window (e.g., 5m, 1h, 1d)")
    aggregation_function: Literal["mean", "max", "min", "sum", "count"] = Field("mean", description="Aggregation function")


class SensorDataPoint(BaseModel):
    """Model for a single data point in query results."""
    
    timestamp: datetime
    value: float
    sensor_id: str
    sensor_type: str


class SensorDataResponse(BaseModel):
    """Model for sensor data query response."""
    
    data: List[SensorDataPoint]
    count: int
    query_info: dict
