"""Pydantic models for irrigation control API."""

from datetime import datetime, timezone
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TriggerType(str, Enum):
    """Irrigation trigger types."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    AUTOMATED = "automated"


class IrrigationStatus(str, Enum):
    """Irrigation event status."""
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class RepeatPattern(str, Enum):
    """Schedule repeat patterns."""
    DAILY = "daily"
    WEEKLY = "weekly"
    NONE = "none"


# Zone configuration
ZONE_CONFIG = {
    1: {"name": "Orchard A", "type": "orchard", "description": "Apple trees section"},
    2: {"name": "Orchard B", "type": "orchard", "description": "Pear trees section"},
    3: {"name": "Orchard C", "type": "orchard", "description": "Cherry trees section"},
    4: {"name": "Orchard D", "type": "orchard", "description": "Mixed fruit section"},
    5: {"name": "Potato Field", "type": "potato", "description": "Main potato cultivation"},
}

VALID_ZONE_IDS = list(ZONE_CONFIG.keys())
MAX_DURATION_MINUTES = 120
MAX_DAILY_IRRIGATION_MINUTES = 120  # 2 hours per zone per day
MOISTURE_SATURATION_THRESHOLD = 85.0  # Block if moisture > 85%


# ==================== Request Models ====================

class ManualIrrigationRequest(BaseModel):
    """Request model for manual irrigation trigger."""
    
    zone_id: int = Field(..., ge=1, le=5, description="Zone ID (1-4 for orchard, 5 for potato)")
    duration_minutes: int = Field(..., ge=1, le=MAX_DURATION_MINUTES, description="Duration in minutes (max 120)")
    trigger_type: Literal["manual"] = Field(default="manual", description="Trigger type (must be 'manual')")
    user_id: str = Field(..., min_length=1, max_length=100, description="User/technician identifier")
    
    @field_validator('zone_id')
    @classmethod
    def validate_zone(cls, v):
        if v not in VALID_ZONE_IDS:
            raise ValueError(f'Invalid zone_id. Must be one of {VALID_ZONE_IDS}')
        return v


class ScheduleIrrigationRequest(BaseModel):
    """Request model for creating scheduled irrigation."""
    
    zone_id: int = Field(..., ge=1, le=5, description="Zone ID (1-4 for orchard, 5 for potato)")
    duration_minutes: int = Field(..., ge=1, le=MAX_DURATION_MINUTES, description="Duration in minutes (max 120)")
    schedule_time: datetime = Field(..., description="Scheduled start time")
    repeat_pattern: Optional[RepeatPattern] = Field(None, description="Repeat pattern (daily, weekly, none)")
    user_id: str = Field(..., min_length=1, max_length=100, description="User who created the schedule")
    
    @field_validator('zone_id')
    @classmethod
    def validate_zone(cls, v):
        if v not in VALID_ZONE_IDS:
            raise ValueError(f'Invalid zone_id. Must be one of {VALID_ZONE_IDS}')
        return v


class UpdateScheduleRequest(BaseModel):
    """Request model for updating an irrigation schedule."""
    
    schedule_time: Optional[datetime] = Field(None, description="New scheduled start time")
    duration_minutes: Optional[int] = Field(None, ge=1, le=MAX_DURATION_MINUTES, description="New duration")
    repeat_pattern: Optional[RepeatPattern] = Field(None, description="New repeat pattern")
    is_active: Optional[bool] = Field(None, description="Enable/disable schedule")


# ==================== Response Models ====================

class IrrigationEvent(BaseModel):
    """Model for irrigation event records."""
    
    id: int = Field(..., description="Event ID")
    zone_id: int = Field(..., description="Zone ID")
    zone_name: str = Field(..., description="Zone name")
    start_time: datetime = Field(..., description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time (if completed)")
    duration_minutes: int = Field(..., description="Planned duration in minutes")
    actual_duration_minutes: Optional[int] = Field(None, description="Actual duration if completed")
    trigger_type: str = Field(..., description="How irrigation was triggered")
    user_id: str = Field(..., description="User who triggered the irrigation")
    status: IrrigationStatus = Field(..., description="Event status")
    created_at: datetime = Field(..., description="Record creation time")


class IrrigationSchedule(BaseModel):
    """Model for irrigation schedule records."""
    
    id: int = Field(..., description="Schedule ID")
    zone_id: int = Field(..., description="Zone ID")
    zone_name: str = Field(..., description="Zone name")
    schedule_time: datetime = Field(..., description="Scheduled start time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    repeat_pattern: Optional[str] = Field(None, description="Repeat pattern")
    is_active: bool = Field(..., description="Whether schedule is active")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Last update time")


class ZoneStatus(BaseModel):
    """Model for current zone status."""
    
    zone_id: int = Field(..., description="Zone ID")
    zone_name: str = Field(..., description="Zone name")
    zone_type: str = Field(..., description="Zone type (orchard/potato)")
    is_active: bool = Field(..., description="Whether irrigation is currently running")
    current_duration_minutes: Optional[int] = Field(None, description="Minutes elapsed since start")
    remaining_minutes: Optional[int] = Field(None, description="Minutes remaining")
    started_at: Optional[datetime] = Field(None, description="Start time of current irrigation")
    moisture_level: Optional[float] = Field(None, description="Current soil moisture %")
    daily_irrigation_minutes: int = Field(0, description="Total irrigation time today")


class AllZonesStatus(BaseModel):
    """Response model for all zones status."""
    
    zones: List[ZoneStatus] = Field(..., description="Status of all zones")
    active_count: int = Field(..., description="Number of currently active zones")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IrrigationResponse(BaseModel):
    """Response model for irrigation trigger."""
    
    success: bool = Field(..., description="Whether operation succeeded")
    event_id: Optional[int] = Field(None, description="Created event ID")
    zone_id: int = Field(..., description="Zone ID")
    duration_minutes: Optional[int] = Field(None, description="Irrigation duration")
    status: Optional[str] = Field(None, description="Current status")
    mqtt_published: bool = Field(False, description="Whether MQTT command was published")
    message: str = Field(..., description="Human-readable message")


class IrrigationError(BaseModel):
    """Response model for irrigation errors."""
    
    success: bool = Field(default=False)
    error: str = Field(..., description="Error type")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    zone_id: Optional[int] = Field(None, description="Zone ID if applicable")
    details: Optional[dict] = Field(None, description="Additional error details")


class IrrigationHistoryResponse(BaseModel):
    """Response model for irrigation history."""
    
    events: List[IrrigationEvent] = Field(..., description="List of irrigation events")
    total: int = Field(..., description="Total number of events")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Events per page")


class ScheduleResponse(BaseModel):
    """Response model for schedule operations."""
    
    success: bool = Field(..., description="Whether operation succeeded")
    schedule_id: Optional[int] = Field(None, description="Schedule ID")
    message: str = Field(..., description="Human-readable message")
    schedule: Optional[IrrigationSchedule] = Field(None, description="Schedule details")


class EmergencyStopResponse(BaseModel):
    """Response model for emergency stop."""
    
    success: bool = Field(..., description="Whether all zones were stopped")
    stopped_zones: List[int] = Field(..., description="List of zones that were stopped")
    failed_zones: List[int] = Field(default_factory=list, description="List of zones that failed to stop")
    mqtt_published: bool = Field(..., description="Whether MQTT commands were published")
    message: str = Field(..., description="Human-readable message")
