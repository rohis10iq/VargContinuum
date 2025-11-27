# API Reference Guide

## Sensor Endpoints

### Base URL
```
http://localhost:8000/api/sensors
```

---

## Endpoints

### 1. List All Sensors

Get a list of all sensors in the system.

**Endpoint**: `GET /api/sensors`

**Authentication**: None (currently public)

**Query Parameters**: None

**Response Schema**:
```json
{
  "sensors": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "location": "string | null",
      "unit": "string",
      "status": "string",
      "last_reading": {
        "timestamp": "datetime",
        "value": "float",
        "unit": "string"
      } | null
    }
  ],
  "total": "integer"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/sensors" \
  -H "accept: application/json"
```

**Example Response**:
```json
{
  "sensors": [
    {
      "id": "sensor_temp_001",
      "name": "Temperature Sensor 1",
      "type": "temperature",
      "location": "Field A - Zone 1",
      "unit": "°C",
      "status": "active",
      "last_reading": {
        "timestamp": "2025-11-28T10:00:00Z",
        "value": 25.5,
        "unit": "°C"
      }
    }
  ],
  "total": 1
}
```

**Status Codes**:
- `200 OK`: Success
- `500 Internal Server Error`: Database connection error

---

### 2. Get Sensor Details

Get detailed information for a specific sensor.

**Endpoint**: `GET /api/sensors/{sensor_id}`

**Authentication**: None (currently public)

**Path Parameters**:
- `sensor_id` (string, required): Unique identifier of the sensor

**Response Schema**:
```json
{
  "id": "string",
  "name": "string",
  "type": "string",
  "location": "string | null",
  "unit": "string",
  "status": "string",
  "last_reading": {
    "timestamp": "datetime",
    "value": "float",
    "unit": "string"
  } | null
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/sensors/sensor_temp_001" \
  -H "accept: application/json"
```

**Example Response**:
```json
{
  "id": "sensor_temp_001",
  "name": "Temperature Sensor 1",
  "type": "temperature",
  "location": "Field A - Zone 1",
  "unit": "°C",
  "status": "active",
  "last_reading": {
    "timestamp": "2025-11-28T10:00:00Z",
    "value": 25.5,
    "unit": "°C"
  }
}
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Sensor not found
- `500 Internal Server Error`: Database connection error

---

### 3. Get Latest Reading

Get the most recent reading from a specific sensor.

**Endpoint**: `GET /api/sensors/{sensor_id}/latest`

**Authentication**: None (currently public)

**Path Parameters**:
- `sensor_id` (string, required): Unique identifier of the sensor

**Response Schema**:
```json
{
  "timestamp": "datetime",
  "value": "float",
  "unit": "string"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/sensors/sensor_temp_001/latest" \
  -H "accept: application/json"
```

**Example Response**:
```json
{
  "timestamp": "2025-11-28T10:00:00Z",
  "value": 25.5,
  "unit": "°C"
}
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Sensor not found or no readings available
- `500 Internal Server Error`: Database connection error

---

### 4. Get Historical Readings

Get historical readings for a specific sensor within a time range.

**Endpoint**: `GET /api/sensors/{sensor_id}/history`

**Authentication**: None (currently public)

**Path Parameters**:
- `sensor_id` (string, required): Unique identifier of the sensor

**Query Parameters**:
- `start_time` (datetime, optional): Start of time range in ISO 8601 format
  - Default: 24 hours ago
  - Example: `2025-11-27T00:00:00Z`
- `end_time` (datetime, optional): End of time range in ISO 8601 format
  - Default: Current time
  - Example: `2025-11-28T23:59:59Z`
- `limit` (integer, optional): Maximum number of readings to return
  - Range: 1-10000
  - Default: 1000
- `interval` (string, optional): Aggregation interval for downsampling
  - Format: number + unit (s=seconds, m=minutes, h=hours, d=days)
  - Examples: `1h`, `15m`, `30s`, `1d`
  - When specified, returns averaged values over each interval

**Response Schema**:
```json
{
  "sensor_id": "string",
  "readings": [
    {
      "timestamp": "datetime",
      "value": "float",
      "unit": "string"
    }
  ],
  "start_time": "datetime",
  "end_time": "datetime",
  "count": "integer"
}
```

**Example Request**:
```bash
# Get last 24 hours (default)
curl -X GET "http://localhost:8000/api/sensors/sensor_temp_001/history" \
  -H "accept: application/json"

# Custom time range with limit
curl "http://localhost:8000/api/sensors/sensor_temp_001/history?start_time=2025-11-27T00:00:00Z&end_time=2025-11-28T23:59:59Z&limit=100" \
  -H "accept: application/json"

# With aggregation interval (hourly averages)
curl "http://localhost:8000/api/sensors/sensor_temp_001/history?start_time=2025-11-27T00:00:00Z&end_time=2025-11-28T23:59:59Z&interval=1h" \
  -H "accept: application/json"
```

**Example Response**:
```json
{
  "sensor_id": "sensor_temp_001",
  "readings": [
    {
      "timestamp": "2025-11-28T09:00:00Z",
      "value": 24.1,
      "unit": "°C"
    },
    {
      "timestamp": "2025-11-28T09:30:00Z",
      "value": 24.8,
      "unit": "°C"
    },
    {
      "timestamp": "2025-11-28T10:00:00Z",
      "value": 25.5,
      "unit": "°C"
    }
  ],
  "start_time": "2025-11-28T09:00:00Z",
  "end_time": "2025-11-28T10:00:00Z",
  "count": 3
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid time range (start_time >= end_time)
- `404 Not Found`: No data found in specified time range
- `500 Internal Server Error`: Database connection error

---

### 5. Get Sensors Summary (Cached)

Get a summary of all sensors including current, min, max, and average values.

**Endpoint**: `GET /api/sensors/summary`

**Authentication**: None (currently public)

**Query Parameters**: None

**Caching**: 
- This endpoint is cached for 5 minutes (300 seconds)
- Subsequent requests within the cache TTL will return cached data
- Cache key: `sensors_summary`

**Response Schema**:
```json
{
  "summaries": [
    {
      "sensor_id": "string",
      "name": "string",
      "type": "string",
      "current_value": "float | null",
      "min_value": "float | null",
      "max_value": "float | null",
      "avg_value": "float | null",
      "unit": "string",
      "status": "string"
    }
  ],
  "total_sensors": "integer",
  "active_sensors": "integer",
  "timestamp": "datetime"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/sensors/summary" \
  -H "accept: application/json"
```

**Example Response**:
```json
{
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
    },
    {
      "sensor_id": "sensor_humidity_001",
      "name": "Humidity Sensor 1",
      "type": "humidity",
      "current_value": 65.2,
      "min_value": 45.0,
      "max_value": 85.0,
      "avg_value": 62.3,
      "unit": "%",
      "status": "active"
    }
  ],
  "total_sensors": 2,
  "active_sensors": 2,
  "timestamp": "2025-11-28T10:00:00Z"
}
```

**Status Codes**:
- `200 OK`: Success
- `500 Internal Server Error`: Database connection error

**Performance Notes**:
- Statistics (min/max/avg) are calculated over the last 24 hours
- First request may take longer as it queries all sensors
- Cached requests return nearly instantly

---

## Common Response Fields

### SensorReading Object
```json
{
  "timestamp": "2025-11-28T10:00:00Z",  // ISO 8601 datetime in UTC
  "value": 25.5,                         // Numeric sensor value
  "unit": "°C"                           // Unit of measurement
}
```

### SensorDetail Object
```json
{
  "id": "sensor_temp_001",               // Unique sensor identifier
  "name": "Temperature Sensor 1",        // Human-readable name
  "type": "temperature",                 // Sensor type
  "location": "Field A - Zone 1",        // Physical location (optional)
  "unit": "°C",                          // Unit of measurement
  "status": "active",                    // Status: active, inactive, error
  "last_reading": {                      // Most recent reading (optional)
    "timestamp": "2025-11-28T10:00:00Z",
    "value": 25.5,
    "unit": "°C"
  }
}
```

---

## Supported Sensor Types

| Type | Unit | Description |
|------|------|-------------|
| `temperature` | °C | Temperature sensors |
| `humidity` | % | Humidity sensors |
| `soil_moisture` | % | Soil moisture sensors |
| `pressure` | hPa | Atmospheric pressure sensors |
| `light` | lux | Light intensity sensors |
| `rainfall` | mm | Rainfall measurement |
| `wind_speed` | m/s | Wind speed sensors |

---

## Error Handling

All endpoints follow standard HTTP status codes and return error messages in JSON format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error (database connection, etc.)

### Example Error Response
```json
{
  "detail": "Sensor with id 'sensor_invalid' not found"
}
```

---

## Rate Limiting

Currently, there is no rate limiting implemented. For production use, consider:
- Implementing rate limiting per IP address
- Adding API key authentication
- Setting up request quotas

---

## Data Formats

### DateTime Format
All timestamps use ISO 8601 format in UTC:
```
YYYY-MM-DDTHH:MM:SSZ
```

Examples:
- `2025-11-28T10:00:00Z`
- `2025-11-27T00:00:00.000Z`

### Numeric Values
All sensor values are returned as floating-point numbers with appropriate precision.

---

## Python Client Example

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/sensors"

# Get all sensors
response = requests.get(BASE_URL)
sensors = response.json()
print(f"Total sensors: {sensors['total']}")

# Get specific sensor details
sensor_id = "sensor_temp_001"
response = requests.get(f"{BASE_URL}/{sensor_id}")
sensor = response.json()
print(f"Sensor: {sensor['name']}, Last value: {sensor['last_reading']['value']}")

# Get latest reading
response = requests.get(f"{BASE_URL}/{sensor_id}/latest")
reading = response.json()
print(f"Latest: {reading['value']} {reading['unit']} at {reading['timestamp']}")

# Get historical data (last 7 days)
start = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
end = datetime.utcnow().isoformat() + "Z"
response = requests.get(
    f"{BASE_URL}/{sensor_id}/history",
    params={"start_time": start, "end_time": end, "limit": 1000}
)
history = response.json()
print(f"Historical readings: {history['count']}")

# Get aggregated data (hourly averages)
response = requests.get(
    f"{BASE_URL}/{sensor_id}/history",
    params={"start_time": start, "end_time": end, "interval": "1h"}
)
aggregated = response.json()
print(f"Aggregated readings: {aggregated['count']}")

# Get summary (cached)
response = requests.get(f"{BASE_URL}/summary")
summary = response.json()
print(f"Active sensors: {summary['active_sensors']}/{summary['total_sensors']}")
for sensor_summary in summary['summaries']:
    print(f"  {sensor_summary['name']}: {sensor_summary['current_value']} {sensor_summary['unit']}")
```

---

## JavaScript/TypeScript Client Example

```typescript
const BASE_URL = 'http://localhost:8000/api/sensors';

// Get all sensors
async function getAllSensors() {
  const response = await fetch(BASE_URL);
  const data = await response.json();
  console.log(`Total sensors: ${data.total}`);
  return data.sensors;
}

// Get sensor details
async function getSensorDetails(sensorId: string) {
  const response = await fetch(`${BASE_URL}/${sensorId}`);
  if (!response.ok) {
    throw new Error(`Sensor not found: ${sensorId}`);
  }
  return await response.json();
}

// Get latest reading
async function getLatestReading(sensorId: string) {
  const response = await fetch(`${BASE_URL}/${sensorId}/latest`);
  return await response.json();
}

// Get historical data
async function getHistory(
  sensorId: string,
  startTime?: Date,
  endTime?: Date,
  limit: number = 1000,
  interval?: string
) {
  const params = new URLSearchParams();
  if (startTime) params.append('start_time', startTime.toISOString());
  if (endTime) params.append('end_time', endTime.toISOString());
  params.append('limit', limit.toString());
  if (interval) params.append('interval', interval);
  
  const response = await fetch(`${BASE_URL}/${sensorId}/history?${params}`);
  return await response.json();
}

// Get summary
async function getSummary() {
  const response = await fetch(`${BASE_URL}/summary`);
  return await response.json();
}

// Usage example
async function example() {
  const sensors = await getAllSensors();
  const summary = await getSummary();
  
  for (const sensor of sensors) {
    const latest = await getLatestReading(sensor.id);
    console.log(`${sensor.name}: ${latest.value} ${latest.unit}`);
  }
}
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all available endpoints
- View detailed request/response schemas
- Test endpoints directly from the browser
- Download OpenAPI specification (JSON/YAML)

---

## Support

For issues or questions:
1. Check the main [README.md](./README.md)
2. Review the OpenAPI documentation at `/docs`
3. Contact your team lead or refer to project documentation
