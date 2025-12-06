"""MQTT client for subscribing to sensor updates and broadcasting to WebSocket clients."""
import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client for receiving sensor data and broadcasting to WebSocket clients."""
    
    def __init__(
        self,
        broker_url: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "irrigation-api",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize MQTT client.
        
        Args:
            broker_url: MQTT broker hostname/IP
            broker_port: MQTT broker port
            client_id: Client identifier
            username: Optional MQTT username
            password: Optional MQTT password
        """
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.broadcast_callback: Optional[Callable] = None
        self.sensor_topics = [
            "sensors/V1/data",
            "sensors/V2/data",
            "sensors/V3/data",
            "sensors/V4/data",
            "sensors/V5/data"
        ]
    
    def set_broadcast_callback(self, callback: Callable) -> None:
        """
        Set the callback function for broadcasting messages.
        
        Args:
            callback: Async function to call with (message_dict, sensor_id) when data arrives
        """
        self.broadcast_callback = callback
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"MQTT client connected to {self.broker_url}:{self.broker_port}")
            
            # Subscribe to sensor topics
            for topic in self.sensor_topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (code {rc})")
        else:
            logger.info("MQTT client disconnected")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            # Extract sensor ID from topic (e.g., "sensors/V1/data" -> "V1")
            sensor_id = topic.split("/")[1]
            
            # Ensure timestamp exists
            if "timestamp" not in payload:
                payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            # Ensure sensor_id is in payload
            payload["sensor_id"] = sensor_id
            
            logger.debug(f"Received message from {topic}: {payload}")
            
            # Call broadcast callback if set
            if self.broadcast_callback:
                # Create a task to run the async callback
                asyncio.create_task(self.broadcast_callback(payload, sensor_id))
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received on {msg.topic}: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def connect(self) -> None:
        """Connect to the MQTT broker."""
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set credentials if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            self.client.connect(self.broker_url, self.broker_port, keepalive=60)
            
            # Start network loop in background
            self.client.loop_start()
            logger.info("MQTT client initialized and loop started")
        
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT client disconnected")
    
    def is_connected(self) -> bool:
        """Check if MQTT client is connected."""
        return self.connected


# Global MQTT client instance
mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    """Get or create the global MQTT client."""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient()
    return mqtt_client
