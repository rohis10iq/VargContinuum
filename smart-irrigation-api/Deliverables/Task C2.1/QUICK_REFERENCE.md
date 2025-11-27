# Quick Reference: Sensor API Endpoints

## Base URL
```
http://localhost:8000/api/sensors
```

## Endpoints Summary

| Method | Endpoint | Description | Cached |
|--------|----------|-------------|--------|
| GET | `/api/sensors` | List all sensors | ❌ |
| GET | `/api/sensors/{id}` | Get sensor details | ❌ |
| GET | `/api/sensors/{id}/latest` | Get latest reading | ❌ |
| GET | `/api/sensors/{id}/history` | Get historical data | ❌ |
| GET | `/api/sensors/summary` | Get sensors summary | ✅ (5 min) |

## Quick Commands

### List All Sensors
```bash
curl http://localhost:8000/api/sensors
```

### Get Sensor Details
```bash
curl http://localhost:8000/api/sensors/sensor_temp_001
```

### Get Latest Reading
```bash
curl http://localhost:8000/api/sensors/sensor_temp_001/latest
```

### Get History (Last 24 Hours)
```bash
curl http://localhost:8000/api/sensors/sensor_temp_001/history
```

### Get History (Custom Range)
```bash
curl "http://localhost:8000/api/sensors/sensor_temp_001/history?start_time=2025-11-27T00:00:00Z&end_time=2025-11-28T23:59:59Z&limit=1000"
```

### Get Summary (Cached)
```bash
curl http://localhost:8000/api/sensors/summary
```

## Environment Variables

```env
# Required
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token-here
INFLUXDB_ORG=smart-irrigation
INFLUXDB_BUCKET=sensors

# Optional
CACHE_TTL_SECONDS=300
```

## Supported Sensor Types

- `temperature` (°C)
- `humidity` (%)
- `soil_moisture` (%)
- `pressure` (hPa)
- `light` (lux)
- `rainfall` (mm)
- `wind_speed` (m/s)

## Response Codes

- `200` OK - Success
- `400` Bad Request - Invalid parameters
- `404` Not Found - Resource not found
- `500` Internal Server Error - Database error

## Testing

```bash
# Run all tests
pytest tests/test_sensors.py -v

# Run specific test
pytest tests/test_sensors.py::TestSensorEndpoints::test_list_sensors -v
```

## Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **Full Documentation**: `Deliverables/Task C2.1/README.md`
- **API Reference**: `Deliverables/Task C2.1/API_REFERENCE.md`
- **InfluxDB Setup**: `Deliverables/Task C2.1/INFLUXDB_SETUP.md`
