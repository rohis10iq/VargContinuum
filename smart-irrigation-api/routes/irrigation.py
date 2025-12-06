"""Irrigation control API routes."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query

from models.irrigation import (
    ManualIrrigationRequest,
    ScheduleIrrigationRequest,
    UpdateScheduleRequest,
    IrrigationResponse,
    IrrigationError,
    AllZonesStatus,
    IrrigationHistoryResponse,
    ScheduleResponse,
    EmergencyStopResponse,
    VALID_ZONE_IDS
)
from services.irrigation_service import irrigation_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/irrigation", tags=["irrigation"])


@router.post("/manual", response_model=IrrigationResponse, responses={
    400: {"model": IrrigationError, "description": "Validation or safety check failed"},
    409: {"model": IrrigationError, "description": "Zone conflict"}
})
async def trigger_manual_irrigation(request: ManualIrrigationRequest):
    """
    Trigger manual irrigation for a specific zone.
    
    **Safety Checks:**
    - Zone must be valid (1-5)
    - Zone must not be already active
    - Daily irrigation limit (2 hours/zone) must not be exceeded
    - Soil moisture must be below 85% (saturation prevention)
    
    **MQTT Command Published:**
    - Topic: `irrigation/control/{zone_id}`
    - Payload: `{"action": "start", "duration": <minutes>}`
    """
    result = irrigation_service.start_irrigation(
        zone_id=request.zone_id,
        duration_minutes=request.duration_minutes,
        trigger_type=request.trigger_type,
        user_id=request.user_id
    )
    
    if not result["success"]:
        error_code = result.get("error_code", "UNKNOWN_ERROR")
        
        # Determine appropriate HTTP status code
        if error_code == "INVALID_ZONE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )
        elif error_code == "ZONE_ALREADY_ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result
            )
        elif error_code in ["DAILY_LIMIT_EXCEEDED", "MOISTURE_TOO_HIGH"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )
    
    return result


@router.post("/schedule", response_model=ScheduleResponse, responses={
    400: {"model": IrrigationError, "description": "Validation failed"}
})
async def create_irrigation_schedule(request: ScheduleIrrigationRequest):
    """
    Create a scheduled irrigation.
    
    **Parameters:**
    - `zone_id`: Zone to irrigate (1-5)
    - `duration_minutes`: How long to irrigate (max 120)
    - `schedule_time`: When to start irrigation
    - `repeat_pattern`: "daily", "weekly", or null for one-time
    """
    result = irrigation_service.create_schedule(
        zone_id=request.zone_id,
        schedule_time=request.schedule_time,
        duration_minutes=request.duration_minutes,
        repeat_pattern=request.repeat_pattern.value if request.repeat_pattern else None,
        user_id=request.user_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return result


@router.get("/status", response_model=AllZonesStatus)
async def get_irrigation_status():
    """
    Get current valve/irrigation states for all zones.
    
    Returns status of all 5 zones including:
    - Whether irrigation is active
    - Current duration and remaining time
    - Current soil moisture level
    - Daily irrigation total
    """
    result = irrigation_service.get_all_zones_status()
    return result


@router.get("/history", response_model=IrrigationHistoryResponse)
async def get_irrigation_history(
    zone_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by zone ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Events per page")
):
    """
    Get past irrigation events with pagination.
    
    **Query Parameters:**
    - `zone_id`: Filter by specific zone (optional)
    - `page`: Page number (default: 1)
    - `page_size`: Events per page (default: 20, max: 100)
    """
    result = irrigation_service.get_irrigation_history(
        zone_id=zone_id,
        page=page,
        page_size=page_size
    )
    return result


@router.put("/schedule/{schedule_id}", response_model=ScheduleResponse, responses={
    404: {"description": "Schedule not found"}
})
async def update_irrigation_schedule(schedule_id: int, request: UpdateScheduleRequest):
    """
    Update or cancel an existing irrigation schedule.
    
    **Parameters:**
    - `schedule_id`: ID of the schedule to update
    - Set `is_active: false` to cancel/disable a schedule
    """
    result = irrigation_service.update_schedule(
        schedule_id=schedule_id,
        schedule_time=request.schedule_time,
        duration_minutes=request.duration_minutes,
        repeat_pattern=request.repeat_pattern.value if request.repeat_pattern else None,
        is_active=request.is_active
    )
    
    if not result["success"]:
        if result.get("error") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return result


@router.post("/stop_all", response_model=EmergencyStopResponse)
async def emergency_stop_all(
    user_id: str = Query("emergency", description="User triggering emergency stop")
):
    """
    Emergency stop for all irrigation zones.
    
    **IMPORTANT:** This will immediately stop irrigation on ALL zones.
    
    Use this endpoint for:
    - Emergency situations
    - System maintenance
    - Safety shutdowns
    
    **MQTT Commands Published:**
    - Stop command sent to ALL 5 zones
    """
    logger.warning(f"Emergency stop triggered by user: {user_id}")
    result = irrigation_service.stop_all_irrigation(user_id)
    return result


@router.post("/stop/{zone_id}", response_model=IrrigationResponse, responses={
    404: {"description": "Zone not active"}
})
async def stop_zone_irrigation(
    zone_id: int,
    user_id: str = Query("manual", description="User stopping irrigation")
):
    """
    Stop irrigation for a specific zone.
    
    **Parameters:**
    - `zone_id`: Zone to stop (1-5)
    """
    if zone_id not in VALID_ZONE_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_zone", "message": f"Invalid zone_id. Must be one of {VALID_ZONE_IDS}"}
        )
    
    result = irrigation_service.stop_irrigation(zone_id, user_id)
    
    if not result["success"]:
        if result.get("error_code") == "ZONE_NOT_ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return result


@router.get("/schedules")
async def get_all_schedules(
    zone_id: Optional[int] = Query(None, ge=1, le=5, description="Filter by zone ID"),
    active_only: bool = Query(False, description="Show only active schedules")
):
    """
    Get all irrigation schedules.
    
    **Query Parameters:**
    - `zone_id`: Filter by specific zone (optional)
    - `active_only`: Show only active schedules (default: false)
    """
    schedules = irrigation_service.get_schedules(zone_id=zone_id, active_only=active_only)
    return {
        "schedules": schedules,
        "total": len(schedules)
    }


@router.get("/zone/{zone_id}/status")
async def get_zone_status(zone_id: int):
    """
    Get detailed status for a specific zone.
    
    Returns:
    - Current irrigation state
    - Soil moisture level
    - Daily irrigation total
    """
    if zone_id not in VALID_ZONE_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_zone", "message": f"Invalid zone_id. Must be one of {VALID_ZONE_IDS}"}
        )
    
    return irrigation_service.get_zone_status(zone_id)
