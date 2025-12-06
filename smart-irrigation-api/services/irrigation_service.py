"""Irrigation control service with business logic and safety checks."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

from models.irrigation import (
    ZONE_CONFIG, VALID_ZONE_IDS, MAX_DAILY_IRRIGATION_MINUTES,
    MOISTURE_SATURATION_THRESHOLD, IrrigationStatus, TriggerType
)
from services.mqtt_service import mqtt_service
from services.influxdb_service import influxdb_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ActiveIrrigation:
    """Tracks an active irrigation session."""
    zone_id: int
    start_time: datetime
    duration_minutes: int
    user_id: str
    trigger_type: str
    event_id: Optional[int] = None


@dataclass
class IrrigationEventRecord:
    """In-memory irrigation event record (simulates database)."""
    id: int
    zone_id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    trigger_type: str
    user_id: str
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class IrrigationScheduleRecord:
    """In-memory irrigation schedule record (simulates database)."""
    id: int
    zone_id: int
    schedule_time: datetime
    duration_minutes: int
    repeat_pattern: Optional[str]
    user_id: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class IrrigationService:
    """Service for managing irrigation operations with safety checks."""
    
    def __init__(self):
        """Initialize irrigation service."""
        # Track active irrigations per zone
        self._active_irrigations: Dict[int, ActiveIrrigation] = {}
        
        # In-memory storage (simulates PostgreSQL)
        self._events: List[IrrigationEventRecord] = []
        self._schedules: List[IrrigationScheduleRecord] = []
        self._next_event_id: int = 1
        self._next_schedule_id: int = 1
    
    # ==================== Zone Validation ====================
    
    def validate_zone(self, zone_id: int) -> Tuple[bool, Optional[str]]:
        """
        Validate zone ID.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if zone_id not in VALID_ZONE_IDS:
            return False, f"Invalid zone_id {zone_id}. Valid zones are: {VALID_ZONE_IDS}"
        return True, None
    
    def get_zone_info(self, zone_id: int) -> Dict[str, Any]:
        """Get zone configuration info."""
        return ZONE_CONFIG.get(zone_id, {})
    
    # ==================== Safety Checks ====================
    
    def is_zone_active(self, zone_id: int) -> bool:
        """Check if zone is currently irrigating."""
        return zone_id in self._active_irrigations
    
    def check_zone_conflict(self, zone_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if zone is already active (conflict prevention).
        
        Returns:
            Tuple of (has_conflict, error_message)
        """
        if self.is_zone_active(zone_id):
            active = self._active_irrigations[zone_id]
            elapsed = (datetime.now(timezone.utc) - active.start_time).seconds // 60
            return True, f"Zone {zone_id} already active for {elapsed} minutes"
        return False, None
    
    def get_daily_irrigation_total(self, zone_id: int) -> int:
        """
        Get total irrigation time for zone today.
        
        Returns:
            Total minutes irrigated today
        """
        today = datetime.now(timezone.utc).date()
        total_minutes = 0
        
        for event in self._events:
            if event.zone_id == zone_id:
                event_date = event.start_time.date()
                if event_date == today:
                    if event.status == IrrigationStatus.COMPLETED.value and event.end_time:
                        actual_duration = (event.end_time - event.start_time).seconds // 60
                        total_minutes += actual_duration
                    elif event.status == IrrigationStatus.RUNNING.value:
                        elapsed = (datetime.now(timezone.utc) - event.start_time).seconds // 60
                        total_minutes += elapsed
        
        return total_minutes
    
    def check_daily_limit(self, zone_id: int, duration_minutes: int) -> Tuple[bool, Optional[str]]:
        """
        Check if zone would exceed daily irrigation limit.
        
        Args:
            zone_id: Zone identifier
            duration_minutes: Requested duration
            
        Returns:
            Tuple of (would_exceed, error_message)
        """
        current_total = self.get_daily_irrigation_total(zone_id)
        if current_total + duration_minutes > MAX_DAILY_IRRIGATION_MINUTES:
            remaining = max(0, MAX_DAILY_IRRIGATION_MINUTES - current_total)
            return True, f"Zone {zone_id} would exceed daily limit. Already irrigated {current_total} minutes today. Max allowed: {MAX_DAILY_IRRIGATION_MINUTES} minutes. Remaining: {remaining} minutes."
        return False, None
    
    def get_zone_moisture(self, zone_id: int) -> Optional[float]:
        """
        Get current soil moisture level for zone.
        
        Returns:
            Moisture percentage or None if unavailable
        """
        try:
            # Map zone_id to sensor_id pattern (e.g., zone 1 -> sensor V1_MOISTURE)
            sensor_id = f"V{zone_id}"
            latest = influxdb_service.get_sensor_latest(sensor_id)
            if latest and 'value' in latest:
                return latest['value']
        except Exception as e:
            logger.warning(f"Could not fetch moisture for zone {zone_id}: {e}")
        return None
    
    def check_saturation_risk(self, zone_id: int) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Check if soil moisture is too high (saturation risk).
        
        Returns:
            Tuple of (has_risk, error_message, current_moisture)
        """
        moisture = self.get_zone_moisture(zone_id)
        if moisture is not None and moisture > MOISTURE_SATURATION_THRESHOLD:
            return True, f"Zone {zone_id} soil moisture is {moisture:.1f}% (threshold: {MOISTURE_SATURATION_THRESHOLD}%). Irrigation blocked to prevent saturation.", moisture
        return False, None, moisture
    
    # ==================== MQTT Commands ====================
    
    def publish_irrigation_command(self, zone_id: int, action: str, duration: Optional[int] = None) -> bool:
        """
        Publish MQTT command to control irrigation valve.
        
        Args:
            zone_id: Zone identifier
            action: "start" or "stop"
            duration: Duration in minutes (for start action)
            
        Returns:
            True if published successfully
        """
        topic = f"irrigation/control/{zone_id}"
        payload = {"action": action}
        if duration is not None:
            payload["duration"] = duration
        
        try:
            mqtt_service.publish(topic, payload)
            logger.info(f"Published MQTT command to {topic}: {payload}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish MQTT command: {e}")
            return False
    
    # ==================== Core Operations ====================
    
    def start_irrigation(
        self,
        zone_id: int,
        duration_minutes: int,
        trigger_type: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Start irrigation for a zone with all safety checks.
        
        Args:
            zone_id: Zone identifier
            duration_minutes: Irrigation duration
            trigger_type: How irrigation was triggered
            user_id: User who triggered
            
        Returns:
            Result dictionary with success status and details
        """
        # Validate zone
        is_valid, error = self.validate_zone(zone_id)
        if not is_valid:
            return {
                "success": False,
                "error": "invalid_zone",
                "error_code": "INVALID_ZONE",
                "message": error,
                "zone_id": zone_id
            }
        
        # Check zone conflict
        has_conflict, error = self.check_zone_conflict(zone_id)
        if has_conflict:
            return {
                "success": False,
                "error": "zone_conflict",
                "error_code": "ZONE_ALREADY_ACTIVE",
                "message": error,
                "zone_id": zone_id
            }
        
        # Check daily limit
        would_exceed, error = self.check_daily_limit(zone_id, duration_minutes)
        if would_exceed:
            return {
                "success": False,
                "error": "over_irrigation",
                "error_code": "DAILY_LIMIT_EXCEEDED",
                "message": error,
                "zone_id": zone_id,
                "details": {
                    "daily_total": self.get_daily_irrigation_total(zone_id),
                    "max_allowed": MAX_DAILY_IRRIGATION_MINUTES
                }
            }
        
        # Check saturation risk
        has_risk, error, moisture = self.check_saturation_risk(zone_id)
        if has_risk:
            return {
                "success": False,
                "error": "saturation_risk",
                "error_code": "MOISTURE_TOO_HIGH",
                "message": error,
                "zone_id": zone_id,
                "details": {
                    "current_moisture": moisture,
                    "threshold": MOISTURE_SATURATION_THRESHOLD
                }
            }
        
        # All checks passed - start irrigation
        now = datetime.now(timezone.utc)
        
        # Create event record
        event = IrrigationEventRecord(
            id=self._next_event_id,
            zone_id=zone_id,
            start_time=now,
            end_time=None,
            duration_minutes=duration_minutes,
            trigger_type=trigger_type,
            user_id=user_id,
            status=IrrigationStatus.RUNNING.value
        )
        self._events.append(event)
        self._next_event_id += 1
        
        # Track active irrigation
        active = ActiveIrrigation(
            zone_id=zone_id,
            start_time=now,
            duration_minutes=duration_minutes,
            user_id=user_id,
            trigger_type=trigger_type,
            event_id=event.id
        )
        self._active_irrigations[zone_id] = active
        
        # Publish MQTT command
        mqtt_published = self.publish_irrigation_command(zone_id, "start", duration_minutes)
        
        zone_info = self.get_zone_info(zone_id)
        logger.info(f"Started irrigation for zone {zone_id} ({zone_info.get('name')}) for {duration_minutes} minutes")
        
        return {
            "success": True,
            "event_id": event.id,
            "zone_id": zone_id,
            "zone_name": zone_info.get("name", f"Zone {zone_id}"),
            "duration_minutes": duration_minutes,
            "status": IrrigationStatus.RUNNING.value,
            "mqtt_published": mqtt_published,
            "message": f"Irrigation started for zone {zone_id} ({zone_info.get('name')})"
        }
    
    def stop_irrigation(self, zone_id: int, user_id: str = "system") -> Dict[str, Any]:
        """
        Stop irrigation for a specific zone.
        
        Args:
            zone_id: Zone identifier
            user_id: User who stopped
            
        Returns:
            Result dictionary
        """
        if not self.is_zone_active(zone_id):
            return {
                "success": False,
                "error": "zone_not_active",
                "error_code": "ZONE_NOT_ACTIVE",
                "message": f"Zone {zone_id} is not currently irrigating",
                "zone_id": zone_id
            }
        
        active = self._active_irrigations[zone_id]
        now = datetime.now(timezone.utc)
        actual_duration = (now - active.start_time).seconds // 60
        
        # Update event record
        for event in self._events:
            if event.id == active.event_id:
                event.end_time = now
                event.status = IrrigationStatus.STOPPED.value
                break
        
        # Remove from active
        del self._active_irrigations[zone_id]
        
        # Publish MQTT stop command
        mqtt_published = self.publish_irrigation_command(zone_id, "stop")
        
        zone_info = self.get_zone_info(zone_id)
        logger.info(f"Stopped irrigation for zone {zone_id} after {actual_duration} minutes")
        
        return {
            "success": True,
            "zone_id": zone_id,
            "zone_name": zone_info.get("name", f"Zone {zone_id}"),
            "actual_duration_minutes": actual_duration,
            "status": IrrigationStatus.STOPPED.value,
            "mqtt_published": mqtt_published,
            "message": f"Irrigation stopped for zone {zone_id}"
        }
    
    def stop_all_irrigation(self, user_id: str = "system") -> Dict[str, Any]:
        """
        Emergency stop for all active zones.
        
        Args:
            user_id: User who triggered emergency stop
            
        Returns:
            Result dictionary with list of stopped zones
        """
        stopped_zones = []
        failed_zones = []
        
        # Get copy of active zones to iterate
        active_zones = list(self._active_irrigations.keys())
        
        for zone_id in active_zones:
            result = self.stop_irrigation(zone_id, user_id)
            if result["success"]:
                stopped_zones.append(zone_id)
            else:
                failed_zones.append(zone_id)
        
        # Also publish stop to all zones (safety measure)
        mqtt_published = True
        for zone_id in VALID_ZONE_IDS:
            if not self.publish_irrigation_command(zone_id, "stop"):
                mqtt_published = False
        
        logger.warning(f"Emergency stop executed. Stopped zones: {stopped_zones}")
        
        return {
            "success": len(failed_zones) == 0,
            "stopped_zones": stopped_zones,
            "failed_zones": failed_zones,
            "mqtt_published": mqtt_published,
            "message": f"Emergency stop executed. Stopped {len(stopped_zones)} zones."
        }
    
    # ==================== Status & History ====================
    
    def get_zone_status(self, zone_id: int) -> Dict[str, Any]:
        """Get current status for a specific zone."""
        zone_info = self.get_zone_info(zone_id)
        is_active = self.is_zone_active(zone_id)
        
        status = {
            "zone_id": zone_id,
            "zone_name": zone_info.get("name", f"Zone {zone_id}"),
            "zone_type": zone_info.get("type", "unknown"),
            "is_active": is_active,
            "current_duration_minutes": None,
            "remaining_minutes": None,
            "started_at": None,
            "moisture_level": self.get_zone_moisture(zone_id),
            "daily_irrigation_minutes": self.get_daily_irrigation_total(zone_id)
        }
        
        if is_active:
            active = self._active_irrigations[zone_id]
            elapsed = (datetime.now(timezone.utc) - active.start_time).seconds // 60
            status["current_duration_minutes"] = elapsed
            status["remaining_minutes"] = max(0, active.duration_minutes - elapsed)
            status["started_at"] = active.start_time.isoformat()
        
        return status
    
    def get_all_zones_status(self) -> Dict[str, Any]:
        """Get status for all zones."""
        zones = []
        active_count = 0
        
        for zone_id in VALID_ZONE_IDS:
            status = self.get_zone_status(zone_id)
            zones.append(status)
            if status["is_active"]:
                active_count += 1
        
        return {
            "zones": zones,
            "active_count": active_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_irrigation_history(
        self,
        zone_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get irrigation event history.
        
        Args:
            zone_id: Filter by zone (optional)
            page: Page number
            page_size: Events per page
            
        Returns:
            Paginated event list
        """
        # Filter events
        events = self._events
        if zone_id is not None:
            events = [e for e in events if e.zone_id == zone_id]
        
        # Sort by start_time descending
        events = sorted(events, key=lambda e: e.start_time, reverse=True)
        
        # Paginate
        total = len(events)
        start = (page - 1) * page_size
        end = start + page_size
        page_events = events[start:end]
        
        # Convert to response format
        event_dicts = []
        for e in page_events:
            zone_info = self.get_zone_info(e.zone_id)
            actual_duration = None
            if e.end_time:
                actual_duration = (e.end_time - e.start_time).seconds // 60
            
            event_dicts.append({
                "id": e.id,
                "zone_id": e.zone_id,
                "zone_name": zone_info.get("name", f"Zone {e.zone_id}"),
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "duration_minutes": e.duration_minutes,
                "actual_duration_minutes": actual_duration,
                "trigger_type": e.trigger_type,
                "user_id": e.user_id,
                "status": e.status,
                "created_at": e.created_at.isoformat()
            })
        
        return {
            "events": event_dicts,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    # ==================== Schedule Management ====================
    
    def create_schedule(
        self,
        zone_id: int,
        schedule_time: datetime,
        duration_minutes: int,
        repeat_pattern: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """Create a new irrigation schedule."""
        # Validate zone
        is_valid, error = self.validate_zone(zone_id)
        if not is_valid:
            return {
                "success": False,
                "error": "invalid_zone",
                "message": error
            }
        
        schedule = IrrigationScheduleRecord(
            id=self._next_schedule_id,
            zone_id=zone_id,
            schedule_time=schedule_time,
            duration_minutes=duration_minutes,
            repeat_pattern=repeat_pattern,
            user_id=user_id
        )
        self._schedules.append(schedule)
        self._next_schedule_id += 1
        
        zone_info = self.get_zone_info(zone_id)
        logger.info(f"Created schedule {schedule.id} for zone {zone_id}")
        
        return {
            "success": True,
            "schedule_id": schedule.id,
            "message": f"Schedule created for zone {zone_id}",
            "schedule": {
                "id": schedule.id,
                "zone_id": schedule.zone_id,
                "zone_name": zone_info.get("name", f"Zone {zone_id}"),
                "schedule_time": schedule.schedule_time.isoformat(),
                "duration_minutes": schedule.duration_minutes,
                "repeat_pattern": schedule.repeat_pattern,
                "is_active": schedule.is_active,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
        }
    
    def update_schedule(
        self,
        schedule_id: int,
        schedule_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        repeat_pattern: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing schedule."""
        schedule = None
        for s in self._schedules:
            if s.id == schedule_id:
                schedule = s
                break
        
        if schedule is None:
            return {
                "success": False,
                "error": "not_found",
                "message": f"Schedule {schedule_id} not found"
            }
        
        if schedule_time is not None:
            schedule.schedule_time = schedule_time
        if duration_minutes is not None:
            schedule.duration_minutes = duration_minutes
        if repeat_pattern is not None:
            schedule.repeat_pattern = repeat_pattern
        if is_active is not None:
            schedule.is_active = is_active
        schedule.updated_at = datetime.now(timezone.utc)
        
        zone_info = self.get_zone_info(schedule.zone_id)
        logger.info(f"Updated schedule {schedule_id}")
        
        return {
            "success": True,
            "schedule_id": schedule.id,
            "message": f"Schedule {schedule_id} updated",
            "schedule": {
                "id": schedule.id,
                "zone_id": schedule.zone_id,
                "zone_name": zone_info.get("name", f"Zone {schedule.zone_id}"),
                "schedule_time": schedule.schedule_time.isoformat(),
                "duration_minutes": schedule.duration_minutes,
                "repeat_pattern": schedule.repeat_pattern,
                "is_active": schedule.is_active,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
        }
    
    def get_schedules(self, zone_id: Optional[int] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all schedules with optional filtering."""
        schedules = self._schedules
        
        if zone_id is not None:
            schedules = [s for s in schedules if s.zone_id == zone_id]
        if active_only:
            schedules = [s for s in schedules if s.is_active]
        
        result = []
        for s in schedules:
            zone_info = self.get_zone_info(s.zone_id)
            result.append({
                "id": s.id,
                "zone_id": s.zone_id,
                "zone_name": zone_info.get("name", f"Zone {s.zone_id}"),
                "schedule_time": s.schedule_time.isoformat(),
                "duration_minutes": s.duration_minutes,
                "repeat_pattern": s.repeat_pattern,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat()
            })
        
        return result


# Global instance
irrigation_service = IrrigationService()
