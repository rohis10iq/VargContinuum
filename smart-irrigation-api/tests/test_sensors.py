"""Tests for sensor endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app
from models.sensor import SensorReading, SensorDetail, SensorList, SensorHistory, SensorsSummaryResponse


client = TestClient(app)


class TestSensorEndpoints:
    """Test suite for sensor endpoints."""
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_list_sensors(self, mock_influx_manager):
        """Test GET /api/sensors - List all sensors."""
        # Mock data
        mock_influx = Mock()
        mock_influx.get_all_sensors.return_value = [
            {
                "id": "sensor_temp_001",
                "name": "Temperature Sensor 1",
                "type": "temperature",
                "location": "Field A",
                "unit": "°C",
                "status": "active"
            }
        ]
        mock_influx.get_latest_reading.return_value = {
            "timestamp": datetime.utcnow(),
            "value": 25.5,
            "unit": "°C"
        }
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "sensors" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["sensors"]) == 1
        assert data["sensors"][0]["id"] == "sensor_temp_001"
        assert data["sensors"][0]["status"] == "active"
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_sensor_details_success(self, mock_influx_manager):
        """Test GET /api/sensors/{id} - Get sensor details (success)."""
        # Mock data
        mock_influx = Mock()
        mock_influx.get_sensor_details.return_value = {
            "id": "sensor_temp_001",
            "name": "Temperature Sensor 1",
            "type": "temperature",
            "location": "Field A",
            "unit": "°C",
            "status": "active"
        }
        mock_influx.get_latest_reading.return_value = {
            "timestamp": datetime.utcnow(),
            "value": 25.5,
            "unit": "°C"
        }
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors/sensor_temp_001")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sensor_temp_001"
        assert data["name"] == "Temperature Sensor 1"
        assert data["type"] == "temperature"
        assert "last_reading" in data
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_sensor_details_not_found(self, mock_influx_manager):
        """Test GET /api/sensors/{id} - Sensor not found."""
        # Mock data
        mock_influx = Mock()
        mock_influx.get_sensor_details.return_value = None
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors/invalid_sensor")
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_latest_reading_success(self, mock_influx_manager):
        """Test GET /api/sensors/{id}/latest - Get latest reading (success)."""
        # Mock data
        timestamp = datetime.utcnow()
        mock_influx = Mock()
        mock_influx.get_latest_reading.return_value = {
            "timestamp": timestamp,
            "value": 25.5,
            "unit": "°C"
        }
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors/sensor_temp_001/latest")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert data["value"] == 25.5
        assert data["unit"] == "°C"
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_latest_reading_not_found(self, mock_influx_manager):
        """Test GET /api/sensors/{id}/latest - No readings available."""
        # Mock data
        mock_influx = Mock()
        mock_influx.get_latest_reading.return_value = None
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors/sensor_temp_001/latest")
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "no readings" in data["detail"].lower()
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_sensor_history_default_params(self, mock_influx_manager):
        """Test GET /api/sensors/{id}/history - Default parameters."""
        # Mock data
        readings = [
            {"timestamp": datetime.utcnow() - timedelta(hours=2), "value": 24.0, "unit": "°C"},
            {"timestamp": datetime.utcnow() - timedelta(hours=1), "value": 24.5, "unit": "°C"},
            {"timestamp": datetime.utcnow(), "value": 25.0, "unit": "°C"}
        ]
        mock_influx = Mock()
        mock_influx.get_sensor_history.return_value = readings
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors/sensor_temp_001/history")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_id"] == "sensor_temp_001"
        assert "readings" in data
        assert len(data["readings"]) == 3
        assert data["count"] == 3
        assert "start_time" in data
        assert "end_time" in data
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_sensor_history_custom_params(self, mock_influx_manager):
        """Test GET /api/sensors/{id}/history - Custom time range and limit."""
        # Mock data
        readings = [
            {"timestamp": datetime.utcnow(), "value": 25.0, "unit": "°C"}
        ]
        mock_influx = Mock()
        mock_influx.get_sensor_history.return_value = readings
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        start_time = "2025-11-27T00:00:00Z"
        end_time = "2025-11-28T23:59:59Z"
        response = client.get(
            f"/api/sensors/sensor_temp_001/history"
            f"?start_time={start_time}&end_time={end_time}&limit=100"
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_id"] == "sensor_temp_001"
        assert data["count"] == 1
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_sensor_history_invalid_time_range(self, mock_influx_manager):
        """Test GET /api/sensors/{id}/history - Invalid time range."""
        # Mock data
        mock_influx = Mock()
        mock_influx_manager.return_value = mock_influx
        
        # Make request with start_time after end_time
        start_time = "2025-11-28T23:59:59Z"
        end_time = "2025-11-27T00:00:00Z"
        response = client.get(
            f"/api/sensors/sensor_temp_001/history"
            f"?start_time={start_time}&end_time={end_time}"
        )
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "before" in data["detail"].lower()
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_get_sensor_history_no_data(self, mock_influx_manager):
        """Test GET /api/sensors/{id}/history - No data in range."""
        # Mock data
        mock_influx = Mock()
        mock_influx.get_sensor_history.return_value = []
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors/sensor_temp_001/history")
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "no historical data" in data["detail"].lower()
    
    @patch('routes.sensors.get_influxdb_manager')
    @patch('routes.sensors.get_sensors_cache')
    def test_get_sensors_summary_no_cache(self, mock_cache, mock_influx_manager):
        """Test GET /api/sensors/summary - Cache miss."""
        # Mock cache (cache miss)
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance
        
        # Mock InfluxDB data
        mock_influx = Mock()
        mock_influx.get_all_sensors.return_value = [
            {
                "id": "sensor_temp_001",
                "name": "Temperature Sensor 1",
                "type": "temperature",
                "unit": "°C",
                "status": "active"
            }
        ]
        mock_influx.get_latest_reading.return_value = {"value": 25.5}
        mock_influx.get_sensor_statistics.return_value = {
            "min": 18.2,
            "max": 32.1,
            "avg": 24.8
        }
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors/summary")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "summaries" in data
        assert "total_sensors" in data
        assert "active_sensors" in data
        assert "timestamp" in data
        assert data["total_sensors"] == 1
        assert data["active_sensors"] == 1
        assert len(data["summaries"]) == 1
        
        # Verify cache was set
        mock_cache_instance.set.assert_called_once()
    
    @patch('routes.sensors.get_sensors_cache')
    def test_get_sensors_summary_with_cache(self, mock_cache):
        """Test GET /api/sensors/summary - Cache hit."""
        # Mock cache (cache hit)
        cached_data = {
            "summaries": [
                {
                    "sensor_id": "sensor_temp_001",
                    "name": "Temperature Sensor 1",
                    "type": "temperature",
                    "current_value": 25.5,
                    "min_value": 18.2,
                    "max_value": 32.1,
                    "avg_value": 24.8,
                    "unit": "°C",
                    "status": "active"
                }
            ],
            "total_sensors": 1,
            "active_sensors": 1,
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = cached_data
        mock_cache.return_value = mock_cache_instance
        
        # Make request
        response = client.get("/api/sensors/summary")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data == cached_data
        
        # Verify InfluxDB was not queried (cache hit)
        mock_cache_instance.get.assert_called_once_with("sensors_summary")
    
    def test_list_sensors_empty(self):
        """Test GET /api/sensors - Empty result when no sensors."""
        with patch('routes.sensors.get_influxdb_manager') as mock_influx_manager:
            mock_influx = Mock()
            mock_influx.get_all_sensors.return_value = []
            mock_influx_manager.return_value = mock_influx
            
            response = client.get("/api/sensors")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert len(data["sensors"]) == 0
    
    @patch('routes.sensors.get_influxdb_manager')
    def test_error_handling(self, mock_influx_manager):
        """Test error handling for database errors."""
        # Mock database error
        mock_influx = Mock()
        mock_influx.get_all_sensors.side_effect = Exception("Database connection error")
        mock_influx_manager.return_value = mock_influx
        
        # Make request
        response = client.get("/api/sensors")
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"].lower()


class TestDataModels:
    """Test Pydantic data models."""
    
    def test_sensor_reading_model(self):
        """Test SensorReading model validation."""
        reading = SensorReading(
            timestamp=datetime.utcnow(),
            value=25.5,
            unit="°C"
        )
        assert reading.value == 25.5
        assert reading.unit == "°C"
    
    def test_sensor_detail_model(self):
        """Test SensorDetail model validation."""
        reading = SensorReading(
            timestamp=datetime.utcnow(),
            value=25.5,
            unit="°C"
        )
        sensor = SensorDetail(
            id="sensor_temp_001",
            name="Temperature Sensor 1",
            type="temperature",
            location="Field A",
            unit="°C",
            status="active",
            last_reading=reading
        )
        assert sensor.id == "sensor_temp_001"
        assert sensor.last_reading.value == 25.5
    
    def test_sensor_list_model(self):
        """Test SensorList model validation."""
        sensors = SensorList(sensors=[], total=0)
        assert sensors.total == 0
        assert len(sensors.sensors) == 0
    
    def test_sensor_history_model(self):
        """Test SensorHistory model validation."""
        readings = [
            SensorReading(timestamp=datetime.utcnow(), value=25.5, unit="°C")
        ]
        history = SensorHistory(
            sensor_id="sensor_temp_001",
            readings=readings,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            count=1
        )
        assert history.sensor_id == "sensor_temp_001"
        assert history.count == 1
        assert len(history.readings) == 1


class TestCacheManager:
    """Test cache manager functionality."""
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        from utils.cache import CacheManager
        
        cache = CacheManager(maxsize=10, ttl=60)
        cache.set("test_key", {"value": 123})
        
        result = cache.get("test_key")
        assert result == {"value": 123}
    
    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        from utils.cache import CacheManager
        import time
        
        cache = CacheManager(maxsize=10, ttl=1)  # 1 second TTL
        cache.set("test_key", {"value": 123})
        
        # Value should exist
        assert cache.get("test_key") is not None
        
        # Wait for expiration
        time.sleep(2)
        
        # Value should be expired
        assert cache.get("test_key") is None
    
    def test_cache_clear(self):
        """Test cache clearing."""
        from utils.cache import CacheManager
        
        cache = CacheManager(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_delete(self):
        """Test deleting specific cache entry."""
        from utils.cache import CacheManager
        
        cache = CacheManager(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.delete("key1")
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_cache_has(self):
        """Test checking if key exists in cache."""
        from utils.cache import CacheManager
        
        cache = CacheManager(maxsize=10, ttl=60)
        cache.set("test_key", "value")
        
        assert cache.has("test_key") is True
        assert cache.has("nonexistent") is False
    
    def test_cache_stats(self):
        """Test cache statistics."""
        from utils.cache import CacheManager
        
        cache = CacheManager(maxsize=50, ttl=300)
        cache.set("key1", "value1")
        
        stats = cache.get_stats()
        assert stats["max_size"] == 50
        assert stats["ttl_seconds"] == 300
        assert stats["current_size"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
