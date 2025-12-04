"""Sensor data API routes."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Query, Path

from models.sensor import SensorReading, SensorDataResponse, SensorDataPoint
from services.influxdb_service import influxdb_service
from services.websocket_manager import connection_manager


router = APIRouter(prefix="/api/sensors", tags=["sensors"])

# Simple in-memory cache for dashboard summary
_summary_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": None,
    "ttl_seconds": 30  # Cache for 30 seconds
}


@router.get("", response_model=List[Dict[str, Any]])
async def list_sensors():
    """List all unique sensors."""
    return influxdb_service.get_all_sensors()


@router.get("/summary")
async def get_dashboard_summary():
    """Get latest reading for all sensors (cached for 30s)."""
    now = datetime.utcnow()
    
    # Check cache
    if (_summary_cache["data"] and _summary_cache["timestamp"] and 
        (now - _summary_cache["timestamp"]).total_seconds() < _summary_cache["ttl_seconds"]):
        return _summary_cache["data"]
        
    # Fetch new data
    data = influxdb_service.get_dashboard_summary()
    
    # Update cache
    _summary_cache["data"] = data
    _summary_cache["timestamp"] = now
    
    return data


@router.get("/{sensor_id}/latest")
async def get_sensor_latest_reading(sensor_id: str = Path(..., description="Sensor ID")):
    """Get the most recent reading for a sensor."""
    latest = influxdb_service.get_sensor_latest(sensor_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return latest


@router.get("/{sensor_id}/history", response_model=SensorDataResponse)
async def get_sensor_history_by_id(
    sensor_id: str = Path(..., description="Sensor ID"),
    period: str = Query("24h", description="Time period (24h, 7d, 30d)")
):
    """Get historical data for a specific sensor."""
    if period == "24h":
        return await get_24h_history(sensor_id=sensor_id)
    elif period == "7d":
        return await get_7d_history(sensor_id=sensor_id)
    elif period == "30d":
        return await get_30d_history(sensor_id=sensor_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid period. Use 24h, 7d, or 30d")


@router.get("/{sensor_id}")
async def get_sensor_details(sensor_id: str = Path(..., description="Sensor ID")):
    """Get latest details for a specific sensor."""
    latest = influxdb_service.get_sensor_latest(sensor_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return latest



@router.post("/write", status_code=status.HTTP_201_CREATED)
async def write_sensor_data(reading: SensorReading):
    """
    Write a sensor reading to InfluxDB.
    
    Example request:
    ```json
    {
        "sensor_id": "soil_sensor_01",
        "sensor_type": "soil_moisture",
        "value": 45.5,
        "location": "field_a",
        "timestamp": "2025-11-28T10:00:00Z"
    }
    ```
    """
    try:
        success = influxdb_service.write_sensor_data(
            sensor_id=reading.sensor_id,
            sensor_type=reading.sensor_type,
            value=reading.value,
            location=reading.location,
            timestamp=reading.timestamp
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to write sensor data to database"
            )
        
        # Broadcast sensor update to WebSocket clients
        try:
            await connection_manager.broadcast_sensor_update(
                sensor_id=reading.sensor_id,
                sensor_type=reading.sensor_type,
                value=reading.value,
                location=reading.location
            )
        except Exception as ws_error:
            # Log WebSocket broadcast error but don't fail the request
            print(f"Warning: WebSocket broadcast failed: {ws_error}")
        
        return {
            "message": "Sensor data written successfully",
            "sensor_id": reading.sensor_id,
            "timestamp": reading.timestamp or datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error writing sensor data: {str(e)}"
        )


@router.get("/history/24h", response_model=SensorDataResponse)
async def get_24h_history(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type")
):
    """
    Get 24-hour sensor history with 5-minute aggregation.
    
    Returns data points aggregated into 5-minute intervals.
    """
    try:
        data = influxdb_service.query_24h_history(
            sensor_id=sensor_id,
            sensor_type=sensor_type
        )
        
        data_points = [
            SensorDataPoint(
                timestamp=point["timestamp"],
                value=point["value"],
                sensor_id=point["sensor_id"],
                sensor_type=point["sensor_type"]
            )
            for point in data
        ]
        
        return SensorDataResponse(
            data=data_points,
            count=len(data_points),
            query_info={
                "range": "24 hours",
                "aggregation": "5 minutes",
                "function": "mean"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying 24h history: {str(e)}"
        )


@router.get("/history/7d", response_model=SensorDataResponse)
async def get_7d_history(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type")
):
    """
    Get 7-day sensor history with 1-hour aggregation.
    
    Returns data points aggregated into 1-hour intervals.
    """
    try:
        data = influxdb_service.query_7d_history(
            sensor_id=sensor_id,
            sensor_type=sensor_type
        )
        
        data_points = [
            SensorDataPoint(
                timestamp=point["timestamp"],
                value=point["value"],
                sensor_id=point["sensor_id"],
                sensor_type=point["sensor_type"]
            )
            for point in data
        ]
        
        return SensorDataResponse(
            data=data_points,
            count=len(data_points),
            query_info={
                "range": "7 days",
                "aggregation": "1 hour",
                "function": "mean"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying 7d history: {str(e)}"
        )


@router.get("/history/30d", response_model=SensorDataResponse)
async def get_30d_history(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type")
):
    """
    Get 30-day sensor history with 6-hour aggregation.
    
    Returns data points aggregated into 6-hour intervals.
    """
    try:
        data = influxdb_service.query_30d_history(
            sensor_id=sensor_id,
            sensor_type=sensor_type
        )
        
        data_points = [
            SensorDataPoint(
                timestamp=point["timestamp"],
                value=point["value"],
                sensor_id=point["sensor_id"],
                sensor_type=point["sensor_type"]
            )
            for point in data
        ]
        
        return SensorDataResponse(
            data=data_points,
            count=len(data_points),
            query_info={
                "range": "30 days",
                "aggregation": "6 hours",
                "function": "mean"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying 30d history: {str(e)}"
        )


@router.get("/aggregate", response_model=SensorDataResponse)
async def get_custom_aggregation(
    start_time: datetime = Query(..., description="Start time (ISO 8601 format)"),
    stop_time: Optional[datetime] = Query(None, description="Stop time (ISO 8601 format)"),
    window: str = Query("5m", description="Aggregation window (e.g., 5m, 1h, 1d)"),
    function: str = Query("mean", description="Aggregation function (mean, max, min, sum, count)"),
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type")
):
    """
    Get sensor data with custom time range and aggregation.
    
    Example query:
    ```
    /api/sensors/aggregate?start_time=2025-11-27T00:00:00Z&window=30m&function=max&sensor_id=soil_sensor_01
    ```
    """
    try:
        # Validate aggregation function
        valid_functions = ["mean", "max", "min", "sum", "count"]
        if function not in valid_functions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid aggregation function. Must be one of: {', '.join(valid_functions)}"
            )
        
        data = influxdb_service.query_custom_aggregation(
            start_time=start_time,
            stop_time=stop_time,
            aggregation_window=window,
            aggregation_function=function,
            sensor_id=sensor_id,
            sensor_type=sensor_type
        )
        
        data_points = [
            SensorDataPoint(
                timestamp=point["timestamp"],
                value=point["value"],
                sensor_id=point["sensor_id"],
                sensor_type=point["sensor_type"]
            )
            for point in data
        ]
        
        return SensorDataResponse(
            data=data_points,
            count=len(data_points),
            query_info={
                "start_time": start_time.isoformat(),
                "stop_time": stop_time.isoformat() if stop_time else "now",
                "aggregation": window,
                "function": function
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying custom aggregation: {str(e)}"
        )
