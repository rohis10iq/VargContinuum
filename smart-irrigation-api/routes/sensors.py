"""Sensor endpoints for smart irrigation API."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from models.sensor import (
    SensorList,
    SensorDetail,
    SensorReading,
    SensorHistory,
    SensorsSummaryResponse,
    SensorSummary
)
from utils.influxdb_client import get_influxdb_manager
from utils.cache import get_sensors_cache


router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.get("", response_model=SensorList, summary="List all sensors")
async def list_sensors():
    """
    Get a list of all sensors in the system.
    
    Returns:
        SensorList: List of all sensors with their basic information
    """
    try:
        influx = get_influxdb_manager()
        sensors_data = influx.get_all_sensors()
        
        sensors = []
        for sensor_data in sensors_data:
            # Get latest reading for each sensor
            latest = influx.get_latest_reading(sensor_data["id"])
            
            sensor = SensorDetail(
                id=sensor_data["id"],
                name=sensor_data["name"],
                type=sensor_data["type"],
                location=sensor_data.get("location"),
                unit=sensor_data["unit"],
                status=sensor_data["status"],
                last_reading=SensorReading(**latest) if latest else None
            )
            sensors.append(sensor)
        
        return SensorList(sensors=sensors, total=len(sensors))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sensors: {str(e)}"
        )


@router.get("/summary", response_model=SensorsSummaryResponse, summary="Get sensors summary (cached)")
async def get_sensors_summary():
    """
    Get a summary of all sensors including current, min, max, and average values.
    
    This endpoint is cached to improve performance. The cache is refreshed based on
    the configured TTL (default: 5 minutes).
    
    Returns:
        SensorsSummaryResponse: Summary statistics for all sensors
    """
    try:
        cache = get_sensors_cache()
        cache_key = "sensors_summary"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Cache miss - fetch from InfluxDB
        influx = get_influxdb_manager()
        sensors_data = influx.get_all_sensors()
        
        summaries = []
        active_count = 0
        
        for sensor_data in sensors_data:
            sensor_id = sensor_data["id"]
            
            # Get latest reading
            latest = influx.get_latest_reading(sensor_id)
            current_value = latest["value"] if latest else None
            
            # Get statistics (last 24 hours)
            stats = influx.get_sensor_statistics(sensor_id)
            
            if sensor_data["status"] == "active":
                active_count += 1
            
            summary = SensorSummary(
                sensor_id=sensor_id,
                name=sensor_data["name"],
                type=sensor_data["type"],
                current_value=current_value,
                min_value=stats["min"] if stats else None,
                max_value=stats["max"] if stats else None,
                avg_value=stats["avg"] if stats else None,
                unit=sensor_data["unit"],
                status=sensor_data["status"]
            )
            summaries.append(summary)
        
        result = SensorsSummaryResponse(
            summaries=summaries,
            total_sensors=len(summaries),
            active_sensors=active_count,
            timestamp=datetime.utcnow()
        )
        
        # Store in cache
        cache.set(cache_key, result)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sensors summary: {str(e)}"
        )


@router.get("/{sensor_id}", response_model=SensorDetail, summary="Get sensor details")
async def get_sensor(sensor_id: str):
    """
    Get detailed information for a specific sensor.
    
    Args:
        sensor_id: Unique identifier of the sensor
        
    Returns:
        SensorDetail: Detailed sensor information including latest reading
        
    Raises:
        HTTPException: 404 if sensor not found
    """
    try:
        influx = get_influxdb_manager()
        
        # Get sensor details
        sensor_data = influx.get_sensor_details(sensor_id)
        if not sensor_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor with id '{sensor_id}' not found"
            )
        
        # Get latest reading
        latest = influx.get_latest_reading(sensor_id)
        
        return SensorDetail(
            id=sensor_data["id"],
            name=sensor_data["name"],
            type=sensor_data["type"],
            location=sensor_data.get("location"),
            unit=sensor_data["unit"],
            status=sensor_data["status"],
            last_reading=SensorReading(**latest) if latest else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sensor details: {str(e)}"
        )


@router.get("/{sensor_id}/latest", response_model=SensorReading, summary="Get latest reading")
async def get_latest_reading(sensor_id: str):
    """
    Get the most recent reading from a specific sensor.
    
    Args:
        sensor_id: Unique identifier of the sensor
        
    Returns:
        SensorReading: Latest sensor reading with timestamp and value
        
    Raises:
        HTTPException: 404 if sensor not found or no readings available
    """
    try:
        influx = get_influxdb_manager()
        
        # Get latest reading
        latest = influx.get_latest_reading(sensor_id)
        if not latest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No readings found for sensor '{sensor_id}'"
            )
        
        return SensorReading(**latest)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching latest reading: {str(e)}"
        )


@router.get("/{sensor_id}/history", response_model=SensorHistory, summary="Get historical readings")
async def get_sensor_history(
    sensor_id: str,
    start_time: Optional[datetime] = Query(
        None,
        description="Start time for historical data (ISO 8601 format)",
        example="2025-11-27T00:00:00Z"
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="End time for historical data (ISO 8601 format)",
        example="2025-11-28T23:59:59Z"
    ),
    limit: int = Query(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of readings to return"
    ),
    interval: Optional[str] = Query(
        None,
        description="Aggregation interval (e.g., '1h', '15m', '30s')",
        example="1h",
        regex="^[0-9]+(s|m|h|d)$"
    )
):
    """
    Get historical readings for a specific sensor within a time range.
    
    Args:
        sensor_id: Unique identifier of the sensor
        start_time: Start of time range (default: 24 hours ago)
        end_time: End of time range (default: now)
        limit: Maximum number of readings to return (1-10000)
        interval: Aggregation interval (e.g., '1h', '15m', '30s') for downsampling
        
    Returns:
        SensorHistory: Historical sensor readings within the specified time range
        
    Raises:
        HTTPException: 404 if sensor not found or no data in range
    """
    try:
        influx = get_influxdb_manager()
        
        # Set default time range if not provided
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Validate time range
        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time must be before end_time"
            )
        
        # Get historical readings
        readings_data = influx.get_sensor_history(sensor_id, start_time, end_time, limit, interval)
        if not readings_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data found for sensor '{sensor_id}' in the specified time range"
            )
        
        readings = [SensorReading(**r) for r in readings_data]
        
        return SensorHistory(
            sensor_id=sensor_id,
            readings=readings,
            start_time=start_time,
            end_time=end_time,
            count=len(readings)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sensor history: {str(e)}"
        )
