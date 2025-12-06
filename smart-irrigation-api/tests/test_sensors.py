"""Unit tests for sensor API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from main import app

client = TestClient(app)


class TestSensorEndpoints:
    """Test suite for sensor data API endpoints."""
    
    def test_list_sensors(self):
        """Test GET /api/sensors - List all sensors."""
        response = client.get("/api/sensors")
        assert response.status_code == 200
        
        data = response.json()
        assert "sensors" in data
        assert "count" in data
        assert data["count"] == 5
        assert len(data["sensors"]) == 5
        
        # Verify sensor structure
        sensor = data["sensors"][0]
        assert "sensor_id" in sensor
        assert "name" in sensor
        assert "zone_id" in sensor
        assert "zone_name" in sensor
        assert "status" in sensor
        assert sensor["status"] in ["active", "inactive", "error"]
    
    def test_get_sensor_details_valid(self):
        """Test GET /api/sensors/{id} - Get sensor details with valid ID."""
        sensor_id = "V1"
        response = client.get(f"/api/sensors/{sensor_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sensor_id"] == sensor_id
        assert "name" in data
        assert "zone_id" in data
        assert "status" in data
        assert "latest_reading" in data
        
        # If reading exists, verify structure
        if data["latest_reading"]:
            reading = data["latest_reading"]
            assert "timestamp" in reading
            assert "moisture" in reading or reading["moisture"] is None
            assert "temperature" in reading or reading["temperature"] is None
    
    def test_get_sensor_details_invalid(self):
        """Test GET /api/sensors/{id} - Get sensor with invalid ID."""
        response = client.get("/api/sensors/INVALID")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_sensor_latest_reading(self):
        """Test GET /api/sensors/{id}/latest - Get latest sensor reading."""
        sensor_id = "V1"
        response = client.get(f"/api/sensors/{sensor_id}/latest")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "moisture" in data or data["moisture"] is None
        assert "temperature" in data or data["temperature"] is None
        assert "humidity" in data or data["humidity"] is None
        assert "light" in data or data["light"] is None
    
    def test_get_sensor_history_default(self):
        """Test GET /api/sensors/{id}/history - Get history with default params."""
        sensor_id = "V1"
        response = client.get(f"/api/sensors/{sensor_id}/history")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sensor_id"] == sensor_id
        assert "start_time" in data
        assert "end_time" in data
        assert "interval" in data
        assert "readings" in data
        assert "count" in data
        assert isinstance(data["readings"], list)
        assert data["count"] == len(data["readings"])
    
    def test_get_sensor_history_with_params(self):
        """Test GET /api/sensors/{id}/history - Get history with custom params."""
        sensor_id = "V2"
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        response = client.get(
            f"/api/sensors/{sensor_id}/history",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "interval": "6h"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["sensor_id"] == sensor_id
        assert data["interval"] == "6h"
    
    def test_get_sensor_history_invalid_interval(self):
        """Test GET /api/sensors/{id}/history - Invalid interval."""
        response = client.get("/api/sensors/V1/history?interval=5m")
        assert response.status_code == 422  # Validation error
    
    def test_get_sensor_history_invalid_time_range(self):
        """Test GET /api/sensors/{id}/history - Start time after end time."""
        end_time = datetime.utcnow()
        start_time = end_time + timedelta(hours=1)  # Invalid: future start
        
        response = client.get(
            "/api/sensors/V1/history",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
        assert response.status_code == 400
    
    def test_get_sensors_summary(self):
        """Test GET /api/sensors/summary - Get all sensors summary."""
        response = client.get("/api/sensors/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "count" in data
        assert "cached" in data
        assert "cache_timestamp" in data
        assert data["count"] == 5
        assert len(data["summary"]) == 5
        
        # Verify summary structure
        item = data["summary"][0]
        assert "sensor_id" in item
        assert "name" in item
        assert "zone_id" in item
        assert "status" in item
        assert "latest_reading" in item
    
    def test_sensors_summary_caching(self):
        """Test that /api/sensors/summary uses caching."""
        # Clear cache first to ensure clean test
        from routes.sensors import summary_cache
        summary_cache.clear()
        
        # First request - should not be cached
        response1 = client.get("/api/sensors/summary")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cached"] is False
        
        # Second request - should be cached
        response2 = client.get("/api/sensors/summary")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] is True
        assert data2["cache_timestamp"] == data1["cache_timestamp"]
    
    def test_all_sensor_ids(self):
        """Test all sensor IDs (V1-V5) are accessible."""
        sensor_ids = ["V1", "V2", "V3", "V4", "V5"]
        
        for sensor_id in sensor_ids:
            response = client.get(f"/api/sensors/{sensor_id}")
            assert response.status_code == 200, f"Sensor {sensor_id} failed"
            data = response.json()
            assert data["sensor_id"] == sensor_id
    
    def test_sensor_zone_mapping(self):
        """Test that sensors are correctly mapped to zones."""
        response = client.get("/api/sensors")
        assert response.status_code == 200
        
        sensors = response.json()["sensors"]
        
        # V1-V4 should be orchard zones 1-4
        # V5 should be potato field zone 5
        zone_map = {s["sensor_id"]: s["zone_id"] for s in sensors}
        
        assert zone_map["V1"] == 1
        assert zone_map["V2"] == 2
        assert zone_map["V3"] == 3
        assert zone_map["V4"] == 4
        assert zone_map["V5"] == 5


class TestSensorDataValidation:
    """Test data validation and response formats."""
    
    def test_timestamp_format(self):
        """Test that timestamps are in ISO8601 format."""
        response = client.get("/api/sensors/V1/latest")
        assert response.status_code == 200
        
        data = response.json()
        timestamp = data["timestamp"]
        # Should be parseable as ISO8601
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_sensor_reading_ranges(self):
        """Test that sensor readings are within expected ranges."""
        response = client.get("/api/sensors/V1/latest")
        assert response.status_code == 200
        
        data = response.json()
        
        if data["moisture"] is not None:
            assert 0 <= data["moisture"] <= 100
        
        if data["temperature"] is not None:
            assert -50 <= data["temperature"] <= 50  # Reasonable range
        
        if data["humidity"] is not None:
            assert 0 <= data["humidity"] <= 100
        
        if data["light"] is not None:
            assert 0 <= data["light"] <= 1023


class TestAPIPerformance:
    """Test API response time requirements."""
    
    def test_sensor_query_response_time(self):
        """Test that sensor queries respond within 500ms."""
        import time
        
        start = time.time()
        response = client.get("/api/sensors/V1")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Response time {elapsed}s exceeds 500ms requirement"
    
    def test_summary_endpoint_response_time(self):
        """Test that summary endpoint responds quickly (should be cached)."""
        import time
        
        # Warm up cache
        client.get("/api/sensors/summary")
        
        # Test cached response
        start = time.time()
        response = client.get("/api/sensors/summary")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Cached response time {elapsed}s exceeds 500ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
