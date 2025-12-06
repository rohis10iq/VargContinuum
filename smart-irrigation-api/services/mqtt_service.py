"""MQTT service for subscribing to sensor data updates from MQTT broker."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any
import threading

import paho.mqtt.client as mqtt

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTService:
    """MQTT client service for subscribing to sensor updates."""
    
    def __init__(self):
        """Initialize MQTT service."""
        self.client: Optional[mqtt.Client] = None
        self.is_connected: bool = False
        self.on_sensor_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._mqtt_thread: Optional[threading.Thread] = None
        
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback when connected to MQTT broker."""
        if reason_code == 0:
            logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
            self.is_connected = True
            
            # Subscribe to sensor topics
            client.subscribe(settings.MQTT_TOPIC_PREFIX)
            logger.info(f"Subscribed to topic: {settings.MQTT_TOPIC_PREFIX}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")
            self.is_connected = False
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        """Callback when disconnected from MQTT broker."""
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")
        self.is_connected = False
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received from MQTT broker."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received MQTT message on {topic}: {payload}")
            
            # Parse the message
            data = self._parse_sensor_message(topic, payload)
            
            if data and self.on_sensor_update and self._loop:
                # Schedule the async callback in the main event loop
                asyncio.run_coroutine_threadsafe(
                    self._async_callback(data),
                    self._loop
                )
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    async def _async_callback(self, data: Dict[str, Any]):
        """Async wrapper for sensor update callback."""
        if self.on_sensor_update:
            await self.on_sensor_update(data)
    
    def _parse_sensor_message(self, topic: str, payload: str) -> Optional[Dict[str, Any]]:
        """
        Parse incoming MQTT message into standard format.
        
        Expected formats:
        1. JSON payload with sensor data
        2. Topic-based routing: sensors/{sensor_id}/{measurement_type}
        
        Returns standardized format:
        {
            "sensor_id": "V1",
            "moisture": 45.2,
            "temperature": 22.1,
            "timestamp": "2025-11-25T14:30:00Z"
        }
        """
        try:
            # Try parsing as JSON first
            data = json.loads(payload)
            
            # Extract sensor_id from topic if not in payload
            if 'sensor_id' not in data:
                # Parse topic like "sensors/V1/data" or "sensors/V1"
                parts = topic.split('/')
                if len(parts) >= 2:
                    data['sensor_id'] = parts[1]
            
            # Ensure timestamp is present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            # Validate required fields
            if 'sensor_id' not in data:
                logger.warning(f"Message missing sensor_id: {payload}")
                return None
            
            return data
            
        except json.JSONDecodeError:
            # Handle non-JSON payloads (simple value format)
            parts = topic.split('/')
            if len(parts) >= 3:
                sensor_id = parts[1]
                measurement_type = parts[2]
                
                try:
                    value = float(payload)
                    return {
                        'sensor_id': sensor_id,
                        measurement_type: value,
                        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    }
                except ValueError:
                    pass
            
            logger.warning(f"Could not parse MQTT message: {payload}")
            return None
    
    def connect(self, loop: asyncio.AbstractEventLoop):
        """
        Connect to MQTT broker.
        
        Args:
            loop: Asyncio event loop for scheduling callbacks
        """
        self._loop = loop
        
        try:
            # Create MQTT client (v2 API)
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=settings.MQTT_CLIENT_ID,
                protocol=mqtt.MQTTv5
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Connect to broker
            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                keepalive=60
            )
            
            # Start MQTT loop in a separate thread
            self._mqtt_thread = threading.Thread(target=self.client.loop_forever, daemon=True)
            self._mqtt_thread.start()
            
            logger.info("MQTT client started")
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.is_connected = False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            logger.info("MQTT client disconnected")
    
    def publish(self, topic: str, payload: Dict[str, Any]):
        """
        Publish a message to MQTT broker (for testing/simulation).
        
        Args:
            topic: MQTT topic
            payload: Message payload as dictionary
        """
        if self.client and self.is_connected:
            self.client.publish(topic, json.dumps(payload))
            logger.debug(f"Published to {topic}: {payload}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get MQTT connection status."""
        return {
            "is_connected": self.is_connected,
            "broker_host": settings.MQTT_BROKER_HOST,
            "broker_port": settings.MQTT_BROKER_PORT,
            "topic_prefix": settings.MQTT_TOPIC_PREFIX
        }


# Global MQTT service instance
mqtt_service = MQTTService()
