"""Sensor data API routes."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from cachetools import TTLCache
from models.sensor import (
    SensorListResponse,
    SensorDetail,
    SensorHistory,
    SensorReading,
    SensorSummaryResponse,
    SensorSummary,
    SensorInfo
)
from utils.influxdb import get_influx_manager, InfluxDBManager
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["Sensors"])

# Cache for high-traffic summary endpoint (5 minutes TTL)
summary_cache = TTLCache(maxsize=1, ttl=settings.CACHE_TTL_SECONDS)

# Sensor metadata (in production, this would come from PostgreSQL)
SENSOR_METADATA = {
    "V1": {"name": "Orchard Zone 1 Sensor", "zone_id": 1, "zone_name": "Orchard Zone 1"},
    "V2": {"name": "Orchard Zone 2 Sensor", "zone_id": 2, "zone_name": "Orchard Zone 2"},
    "V3": {"name": "Orchard Zone 3 Sensor", "zone_id": 3, "zone_name": "Orchard Zone 3"},
    "V4": {"name": "Orchard Zone 4 Sensor", "zone_id": 4, "zone_name": "Orchard Zone 4"},
    "V5": {"name": "Potato Field Sensor", "zone_id": 5, "zone_name": "Potato Field"}
}


def get_sensor_status(last_reading_time: Optional[datetime]) -> str:
    """
    Determine sensor status based on last reading time.
    
    Args:
        last_reading_time: Timestamp of last reading
        
    Returns:
        Status string: 'active', 'inactive', or 'error'
    """
    if not last_reading_time:
        return "inactive"
    
    time_since_reading = datetime.utcnow() - last_reading_time.replace(tzinfo=None)
    
    if time_since_reading < timedelta(minutes=10):
        return "active"
    elif time_since_reading < timedelta(hours=1):
        return "inactive"
    else:
        return "error"


@router.get("", response_model=SensorListResponse, summary="List all sensors")
async def list_sensors(
    influx: InfluxDBManager = Depends(get_influx_manager)
) -> SensorListResponse:
    """
    Get a list of all sensors with their basic information.
    
    Returns:
        List of all sensors with metadata and status
    """
    sensors = []
    
    # Get latest readings to determine status
    latest_readings = influx.query_all_sensors_latest()
    
    for sensor_id, metadata in SENSOR_METADATA.items():
        latest_reading = latest_readings.get(sensor_id)
        last_seen = latest_reading.get("timestamp") if latest_reading else None
        status = get_sensor_status(last_seen)
        
        sensors.append(SensorInfo(
            sensor_id=sensor_id,
            name=metadata["name"],
            zone_id=metadata["zone_id"],
            zone_name=metadata["zone_name"],
            status=status,
            last_seen=last_seen
        ))
    
    return SensorListResponse(sensors=sensors, count=len(sensors))


@router.get("/summary", response_model=SensorSummaryResponse, summary="Get all sensors summary")
async def get_sensors_summary(
    influx: InfluxDBManager = Depends(get_influx_manager)
) -> SensorSummaryResponse:
    """
    Get summary of all sensors with their latest readings.
    
    This is the high-traffic endpoint used by the dashboard grid view.
    Results are cached for 5 minutes to reduce database load.
    
    Returns:
        Summary of all sensors with latest readings and cache status
    """
    # Check cache first
    cache_key = "sensors_summary"
    
    if cache_key in summary_cache:
        cached_data = summary_cache[cache_key]
        logger.info("Serving sensors summary from cache")
        return SensorSummaryResponse(
            summary=cached_data["summary"],
            count=cached_data["count"],
            cached=True,
            cache_timestamp=cached_data["timestamp"]
        )
    
    # Cache miss - query database
    logger.info("Cache miss - querying InfluxDB for sensors summary")
    latest_readings = influx.query_all_sensors_latest()
    
    summary = []
    for sensor_id, metadata in SENSOR_METADATA.items():
        reading_data = latest_readings.get(sensor_id)
        
        latest_reading = None
        last_seen = None
        
        if reading_data:
            latest_reading = SensorReading(**reading_data)
            last_seen = reading_data.get("timestamp")
        
        status = get_sensor_status(last_seen)
        
        summary.append(SensorSummary(
            sensor_id=sensor_id,
            name=metadata["name"],
            zone_id=metadata["zone_id"],
            status=status,
            latest_reading=latest_reading
        ))
    
    # Store in cache
    cache_timestamp = datetime.utcnow()
    summary_cache[cache_key] = {
        "summary": summary,
        "count": len(summary),
        "timestamp": cache_timestamp
    }
    
    return SensorSummaryResponse(
        summary=summary,
        count=len(summary),
        cached=False,
        cache_timestamp=cache_timestamp
    )


@router.get("/{sensor_id}", response_model=SensorDetail, summary="Get sensor details")
async def get_sensor(
    sensor_id: str,
    influx: InfluxDBManager = Depends(get_influx_manager)
) -> SensorDetail:
    """
    Get detailed information about a specific sensor including its latest reading.
    
    Args:
        sensor_id: Sensor identifier (e.g., 'V1', 'V2', 'V3', 'V4', 'V5')
        
    Returns:
        Detailed sensor information with latest reading
        
    Raises:
        HTTPException: If sensor not found
    """
    if sensor_id not in SENSOR_METADATA:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
    
    metadata = SENSOR_METADATA[sensor_id]
    latest_reading_data = influx.query_latest_reading(sensor_id)
    
    latest_reading = None
    last_seen = None
    
    if latest_reading_data:
        latest_reading = SensorReading(**latest_reading_data)
        last_seen = latest_reading_data.get("timestamp")
    
    status = get_sensor_status(last_seen)
    
    return SensorDetail(
        sensor_id=sensor_id,
        name=metadata["name"],
        zone_id=metadata["zone_id"],
        zone_name=metadata["zone_name"],
        status=status,
        last_seen=last_seen,
        latest_reading=latest_reading
    )


@router.get("/{sensor_id}/history", response_model=SensorHistory, summary="Get sensor history")
async def get_sensor_history(
    sensor_id: str,
    start_time: Optional[datetime] = Query(
        None,
        description="Start time (ISO8601). Defaults to 24 hours ago"
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="End time (ISO8601). Defaults to now"
    ),
        interval: str = Query(
        "1h",
        description="Aggregation interval: 15m, 1h, 6h, 1d",
        pattern="^(15m|1h|6h|1d)$"
    ),
    influx: InfluxDBManager = Depends(get_influx_manager)
) -> SensorHistory:
    """
    Get time-series historical data for a sensor.
    
    Supports different time ranges:
    - Last 24 hours (default)
    - Last 7 days
    - Last 30 days
    - Custom range via start_time and end_time
    
    Args:
        sensor_id: Sensor identifier
        start_time: Optional start of time range (defaults to 24h ago)
        end_time: Optional end of time range (defaults to now)
        interval: Data aggregation interval (15m, 1h, 6h, 1d)
        
    Returns:
        Historical sensor readings with specified aggregation
        
    Raises:
        HTTPException: If sensor not found or time range invalid
    """
    if sensor_id not in SENSOR_METADATA:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
    
    # Set default time range (last 24 hours)
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)
    
    # Validate time range
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    
    duration = end_time - start_time
    if duration > timedelta(days=90):
        raise HTTPException(status_code=400, detail="Time range cannot exceed 90 days")
    
    # Query historical data
    readings_data = influx.query_sensor_history(sensor_id, start_time, end_time, interval)
    readings = [SensorReading(**r) for r in readings_data]
    
    return SensorHistory(
        sensor_id=sensor_id,
        start_time=start_time,
        end_time=end_time,
        interval=interval,
        readings=readings,
        count=len(readings)
    )


@router.get("/{sensor_id}/latest", response_model=SensorReading, summary="Get latest sensor reading")
async def get_latest_reading(
    sensor_id: str,
    influx: InfluxDBManager = Depends(get_influx_manager)
) -> SensorReading:
    """
    Get the most recent reading from a specific sensor.
    
    Args:
        sensor_id: Sensor identifier
        
    Returns:
        Latest sensor reading with all measurements
        
    Raises:
        HTTPException: If sensor not found or no data available
    """
    if sensor_id not in SENSOR_METADATA:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
    
    reading_data = influx.query_latest_reading(sensor_id)
    
    if not reading_data:
        raise HTTPException(
            status_code=404,
            detail=f"No recent data available for sensor {sensor_id}"
        )
    
    return SensorReading(**reading_data)
