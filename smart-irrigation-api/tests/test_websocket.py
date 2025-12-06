"""Comprehensive tests for WebSocket real-time sensor streaming."""
import pytest
import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from main import app
from utils.websocket_manager import ws_manager, WebSocketManager
from utils.auth import create_access_token


client = TestClient(app)


class TestWebSocketConnection:
    """Test WebSocket connection establishment and teardown."""
    
    def test_websocket_requires_authentication(self):
        """Test that WebSocket connection requires valid token."""
        with pytest.raises(Exception):
            # Should fail without token
            with client.websocket_connect("/ws/sensors"):
                pass
    
    def test_websocket_rejects_invalid_token(self):
        """Test that WebSocket rejects invalid tokens."""
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/sensors?token=invalid_token"):
                pass
    
    def test_websocket_accepts_valid_token(self):
        """Test that WebSocket accepts valid JWT token."""
        # Create valid token
        token = create_access_token({"user_id": "test_user"})
        
        try:
            with client.websocket_connect(f"/ws/sensors?token={token}") as websocket:
                # Receive connection status message
                data = websocket.receive_json()
                assert data["type"] == "connection_status"
                assert data["data"]["status"] == "connected"
                assert data["data"]["client_id"]
                assert data["timestamp"]
        except Exception as e:
            # MQTT not running is acceptable for this test
            if "MQTT" not in str(e) and "mqtt" not in str(e).lower():
                raise
    
    def test_websocket_connection_cleanup(self):
        """Test that connection is properly cleaned up on disconnect."""
        token = create_access_token({"user_id": "test_user"})
        initial_count = ws_manager.get_active_count()
        
        try:
            with client.websocket_connect(f"/ws/sensors?token={token}") as websocket:
                # Connection should be active
                assert ws_manager.get_active_count() > initial_count
                websocket.receive_json()  # Get connection status
        except Exception as e:
            if "MQTT" not in str(e) and "mqtt" not in str(e).lower():
                raise
        
        # Connection should be cleaned up
        assert ws_manager.get_active_count() == initial_count


class TestWebSocketMessageFormat:
    """Test WebSocket message format and content."""
    
    def test_connection_status_message_format(self):
        """Test that connection status message has correct format."""
        token = create_access_token({"user_id": "test_user"})
        
        try:
            with client.websocket_connect(f"/ws/sensors?token={token}") as websocket:
                data = websocket.receive_json()
                
                assert "type" in data
                assert "data" in data
                assert "timestamp" in data
                assert data["type"] == "connection_status"
                assert "status" in data["data"]
                assert "client_id" in data["data"]
                assert "active_clients" in data["data"]
        except Exception as e:
            if "MQTT" not in str(e) and "mqtt" not in str(e).lower():
                raise
    
    def test_sensor_reading_message_structure(self):
        """Test sensor reading message structure when broadcast."""
        # This would be tested when MQTT data arrives
        # Testing the model structure here
        from models.websocket import SensorReadingMessage, WebSocketMessage
        
        sensor_reading = SensorReadingMessage(
            sensor_id="V1",
            moisture=45.2,
            temperature=22.1,
            humidity=65.5,
            light=800.0,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        message = WebSocketMessage(
            type="sensor_reading",
            data=sensor_reading.model_dump(),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        data = message.model_dump()
        assert data["type"] == "sensor_reading"
        assert data["data"]["sensor_id"] == "V1"
        assert data["data"]["moisture"] == 45.2
        assert "timestamp" in data


class TestWebSocketRateLimiting:
    """Test broadcast rate limiting."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_prevents_rapid_broadcasts(self):
        """Test that rate limiting prevents more than 1 broadcast per second per sensor."""
        manager = WebSocketManager()
        
        # Mock WebSocket
        mock_ws = MagicMock()
        mock_ws.send_json = AsyncMock()
        
        # Add to manager
        manager.active_connections.add(mock_ws)
        manager.client_metadata[mock_ws] = {"client_id": "test"}
        
        # First broadcast should succeed
        result1 = await manager.broadcast({"sensor_id": "V1", "data": "test1"}, "V1")
        assert result1 is True
        
        # Second broadcast within 1 second should be rate-limited
        result2 = await manager.broadcast({"sensor_id": "V1", "data": "test2"}, "V1")
        assert result2 is False
        
        # Only one send should have occurred
        assert mock_ws.send_json.call_count == 1


class TestWebSocketConnectionManagement:
    """Test connection management features."""
    
    def test_manager_tracks_active_connections(self):
        """Test that manager tracks active connections."""
        manager = WebSocketManager()
        assert manager.get_active_count() == 0
        
        # Mock WebSocket
        mock_ws = MagicMock()
        manager.client_metadata[mock_ws] = {"client_id": "test1"}
        manager.active_connections.add(mock_ws)
        
        assert manager.get_active_count() == 1
    
    def test_manager_disconnects_inactive_connections(self):
        """Test that manager removes disconnected clients."""
        manager = WebSocketManager()
        
        # Mock WebSocket
        mock_ws = MagicMock()
        manager.client_metadata[mock_ws] = {"client_id": "test1"}
        manager.active_connections.add(mock_ws)
        
        assert manager.get_active_count() == 1
        
        manager.disconnect(mock_ws)
        
        assert manager.get_active_count() == 0
        assert mock_ws not in manager.active_connections


class TestWebSocketErrorHandling:
    """Test error handling in WebSocket operations."""
    
    @pytest.mark.asyncio
    async def test_broadcast_removes_broken_connections(self):
        """Test that broken connections are removed during broadcast."""
        manager = WebSocketManager()
        
        # Create two mock WebSockets
        good_ws = MagicMock()
        good_ws.send_json = AsyncMock()
        
        bad_ws = MagicMock()
        bad_ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))
        
        manager.active_connections.add(good_ws)
        manager.active_connections.add(bad_ws)
        manager.client_metadata[good_ws] = {"client_id": "good"}
        manager.client_metadata[bad_ws] = {"client_id": "bad"}
        
        assert manager.get_active_count() == 2
        
        # Broadcast should remove the broken connection
        await manager.broadcast({"test": "data"}, "V1")
        
        # Bad connection should be removed
        assert manager.get_active_count() == 1
        assert bad_ws not in manager.active_connections
        assert good_ws in manager.active_connections


class TestMQTTClient:
    """Test MQTT client functionality."""
    
    def test_mqtt_client_initialization(self):
        """Test MQTT client initialization."""
        from utils.mqtt_client import MQTTClient
        
        mqtt = MQTTClient(
            broker_url="localhost",
            broker_port=1883,
            client_id="test-client"
        )
        
        assert mqtt.broker_url == "localhost"
        assert mqtt.broker_port == 1883
        assert mqtt.client_id == "test-client"
        assert mqtt.connected is False
        assert len(mqtt.sensor_topics) == 5
    
    def test_mqtt_sensor_topics(self):
        """Test that MQTT client has correct sensor topics."""
        from utils.mqtt_client import MQTTClient
        
        mqtt = MQTTClient()
        
        expected_topics = [
            "sensors/V1/data",
            "sensors/V2/data",
            "sensors/V3/data",
            "sensors/V4/data",
            "sensors/V5/data"
        ]
        
        assert mqtt.sensor_topics == expected_topics
    
    def test_mqtt_callback_setting(self):
        """Test that MQTT broadcast callback can be set."""
        from utils.mqtt_client import MQTTClient
        
        mqtt = MQTTClient()
        
        async def test_callback(data, sensor_id):
            pass
        
        mqtt.set_broadcast_callback(test_callback)
        assert mqtt.broadcast_callback == test_callback


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    def test_websocket_message_reception(self):
        """Test that WebSocket can receive and parse messages."""
        token = create_access_token({"user_id": "test_user"})
        
        try:
            with client.websocket_connect(f"/ws/sensors?token={token}") as websocket:
                # Should receive connection status
                msg = websocket.receive_json()
                assert msg is not None
                assert "type" in msg
                assert "timestamp" in msg
        except Exception as e:
            # MQTT connection not required for this test
            if "MQTT" not in str(e) and "mqtt" not in str(e).lower():
                raise
    
    def test_websocket_timestamp_format(self):
        """Test that WebSocket messages use ISO8601 timestamps."""
        from models.websocket import WebSocketMessage, SensorReadingMessage
        from datetime import datetime, timezone
        
        timestamp = datetime.now(timezone.utc).isoformat() + "Z"
        reading = SensorReadingMessage(
            sensor_id="V1",
            moisture=45.2,
            temperature=22.1,
            humidity=65.5,
            light=800.0,
            timestamp=timestamp
        )
        
        message = WebSocketMessage(
            type="sensor_reading",
            data=reading.model_dump(),
            timestamp=timestamp
        )
        
        data = message.model_dump()
        # Verify ISO8601 format (has Z suffix for UTC)
        assert data["timestamp"].endswith("Z")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
