"""Tests for sensor data endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from services.influxdb_service import influxdb_service


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_influxdb():
    """Setup and teardown InfluxDB connection for tests."""
    try:
        influxdb_service.connect()
        yield
        influxdb_service.close()
    except Exception as e:
        pytest.skip(f"InfluxDB not available: {e}")


def test_write_sensor_data(client):
    """Test writing sensor data via API."""
    sensor_data = {
        "sensor_id": "test_sensor_api",
        "sensor_type": "temperature",
        "value": 22.5,
        "location": "test_field"
    }
    
    response = client.post("/api/sensors/write", json=sensor_data)
    
    assert response.status_code == 201
    assert "message" in response.json()
    assert response.json()["sensor_id"] == "test_sensor_api"


def test_write_sensor_data_with_timestamp(client):
    """Test writing sensor data with custom timestamp."""
    sensor_data = {
        "sensor_id": "test_sensor_time",
        "sensor_type": "humidity",
        "value": 65.0,
        "location": "greenhouse",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    response = client.post("/api/sensors/write", json=sensor_data)
    
    assert response.status_code == 201


def test_get_24h_history(client):
    """Test 24-hour history endpoint."""
    response = client.get("/api/sensors/history/24h")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert "query_info" in data
    assert data["query_info"]["range"] == "24 hours"


def test_get_24h_history_with_filter(client):
    """Test 24-hour history with sensor filter."""
    response = client.get("/api/sensors/history/24h?sensor_id=test_sensor_api")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)


def test_get_7d_history(client):
    """Test 7-day history endpoint."""
    response = client.get("/api/sensors/history/7d")
    
    assert response.status_code == 200
    data = response.json()
    assert data["query_info"]["range"] == "7 days"
    assert data["query_info"]["aggregation"] == "1 hour"


def test_get_30d_history(client):
    """Test 30-day history endpoint."""
    response = client.get("/api/sensors/history/30d")
    
    assert response.status_code == 200
    data = response.json()
    assert data["query_info"]["range"] == "30 days"
    assert data["query_info"]["aggregation"] == "6 hours"


def test_custom_aggregation(client):
    """Test custom aggregation endpoint."""
    start_time = (datetime.utcnow() - timedelta(hours=6)).isoformat() + "Z"
    
    response = client.get(
        f"/api/sensors/aggregate?start_time={start_time}&window=10m&function=mean"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["query_info"]["function"] == "mean"


def test_custom_aggregation_invalid_function(client):
    """Test custom aggregation with invalid function."""
    start_time = datetime.utcnow().isoformat() + "Z"
    
    response = client.get(
        f"/api/sensors/aggregate?start_time={start_time}&function=invalid"
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_custom_aggregation_with_filters(client):
    """Test custom aggregation with multiple filters."""
    start_time = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    
    response = client.get(
        f"/api/sensors/aggregate?start_time={start_time}"
        f"&window=1h&function=max&sensor_id=test_sensor_api&sensor_type=temperature"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["query_info"]["function"] == "max"
