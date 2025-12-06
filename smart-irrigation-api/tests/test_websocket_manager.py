"""Unit tests for WebSocket connection manager."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from services.websocket_manager import ConnectionManager
from models.websocket import SensorUpdateMessage, HeartbeatMessage


@pytest.fixture
def manager():
    """Create a fresh connection manager for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestConnectionManager:
    """Test suite for WebSocket connection manager."""
    
    @pytest.mark.asyncio
    async def test_connect_global_stream(self, manager, mock_websocket):
        """Test connecting to global stream."""
        await manager.connect(mock_websocket)
        
        assert mock_websocket in manager.active_connections
        assert len(manager.active_connections) == 1
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_sensor_stream(self, manager, mock_websocket):
        """Test connecting to specific sensor stream."""
        sensor_id = "test_sensor_01"
        await manager.connect(mock_websocket, sensor_id=sensor_id)
        
        assert sensor_id in manager.sensor_connections
        assert mock_websocket in manager.sensor_connections[sensor_id]
        assert len(manager.sensor_connections[sensor_id]) == 1
        mock_websocket.accept.assert_called_once()
    
    def test_disconnect_global_stream(self, manager, mock_websocket):
        """Test disconnecting from global stream."""
        manager.active_connections.append(mock_websocket)
        
        manager.disconnect(mock_websocket)
        
        assert mock_websocket not in manager.active_connections
        assert len(manager.active_connections) == 0
    
    def test_disconnect_sensor_stream(self, manager, mock_websocket):
        """Test disconnecting from specific sensor stream."""
        sensor_id = "test_sensor_01"
        manager.sensor_connections[sensor_id] = [mock_websocket]
        
        manager.disconnect(mock_websocket, sensor_id=sensor_id)
        
        assert sensor_id not in manager.sensor_connections
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager, mock_websocket):
        """Test sending message to specific client."""
        test_message = {"type": "test", "data": "hello"}
        
        await manager.send_personal_message(test_message, mock_websocket)
        
        mock_websocket.send_json.assert_called_once_with(test_message)
    
    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """Test broadcasting to all global connections."""
        # Create multiple mock connections
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        
        manager.active_connections = [ws1, ws2, ws3]
        test_message = {"type": "broadcast", "data": "test"}
        
        await manager.broadcast(test_message)
        
        ws1.send_json.assert_called_once_with(test_message)
        ws2.send_json.assert_called_once_with(test_message)
        ws3.send_json.assert_called_once_with(test_message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_sensor(self, manager):
        """Test broadcasting to specific sensor subscribers."""
        sensor_id = "test_sensor_01"
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        
        manager.sensor_connections[sensor_id] = [ws1, ws2]
        test_message = {"type": "update", "sensor_id": sensor_id}
        
        await manager.broadcast_to_sensor(sensor_id, test_message)
        
        ws1.send_json.assert_called_once_with(test_message)
        ws2.send_json.assert_called_once_with(test_message)
    
    @pytest.mark.asyncio
    async def test_broadcast_sensor_update(self, manager):
        """Test broadcasting sensor update to both global and sensor-specific clients."""
        sensor_id = "soil_sensor_01"
        global_ws = AsyncMock()
        sensor_ws = AsyncMock()
        
        manager.active_connections = [global_ws]
        manager.sensor_connections[sensor_id] = [sensor_ws]
        
        await manager.broadcast_sensor_update(
            sensor_id=sensor_id,
            sensor_type="soil_moisture",
            value=45.5,
            location="field_a"
        )
        
        # Both global and sensor-specific connections should receive the update
        assert global_ws.send_json.called
        assert sensor_ws.send_json.called
    
    def test_get_connection_stats(self, manager):
        """Test getting connection statistics."""
        # Add some connections
        ws1 = MagicMock()
        ws2 = MagicMock()
        ws3 = MagicMock()
        
        manager.active_connections = [ws1]
        manager.sensor_connections["sensor_A"] = [ws2]
        manager.sensor_connections["sensor_B"] = [ws3]
        
        stats = manager.get_connection_stats()
        
        assert stats["global_connections"] == 1
        assert stats["sensor_connections"]["sensor_A"] == 1
        assert stats["sensor_connections"]["sensor_B"] == 1
        assert stats["total_connections"] == 3
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_sensor(self, manager):
        """Test multiple clients connecting to the same sensor."""
        sensor_id = "test_sensor_01"
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        
        await manager.connect(ws1, sensor_id=sensor_id)
        await manager.connect(ws2, sensor_id=sensor_id)
        await manager.connect(ws3, sensor_id=sensor_id)
        
        assert len(manager.sensor_connections[sensor_id]) == 3
        
        # Disconnect one
        manager.disconnect(ws2, sensor_id=sensor_id)
        assert len(manager.sensor_connections[sensor_id]) == 2
        assert ws2 not in manager.sensor_connections[sensor_id]
