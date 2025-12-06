# Sensor Data API Specification

**Version:** 1.0  
**Base URL:** `http://localhost:8000`  
**Date:** December 6, 2025

---

## Overview

The Sensor Data API provides REST endpoints for querying IoT sensor data from the smart irrigation system. The API supports real-time data access, historical queries with aggregation, and optimized caching for high-traffic endpoints.

---

## Authentication

**Current Status:** Authentication not required for sensor read endpoints  
**Future:** JWT token authentication will be required

---

## Endpoints

### 1. List All Sensors

**Endpoint:** `GET /api/sensors`

**Description:** Retrieve a list of all sensors with their current status and metadata.

**Request Parameters:** None

**Response:** `200 OK`

```json
{
  "sensors": [
    {
      "sensor_id": "string",
      "name": "string",
      "zone_id": "integer",
      "zone_name": "string",
      "status": "active|inactive|error",
      "last_seen": "datetime|null"
    }
  ],
  "count": "integer"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/sensors"
```

**Status Definitions:**
- `active`: Last reading within 10 minutes
- `inactive`: Last reading within 1 hour
- `error`: No reading for >1 hour

---

### 2. Get Sensor Details

**Endpoint:** `GET /api/sensors/{sensor_id}`

**Description:** Get detailed information about a specific sensor including its latest reading.

**Path Parameters:**
- `sensor_id` (string, required): Sensor identifier (V1, V2, V3, V4, V5)

**Response:** `200 OK`

```json
{
  "sensor_id": "string",
  "name": "string",
  "zone_id": "integer",
  "zone_name": "string",
  "status": "string",
  "last_seen": "datetime|null",
  "latest_reading": {
    "timestamp": "datetime",
    "moisture": "float|null",
    "temperature": "float|null",
    "humidity": "float|null",
    "light": "integer|null"
  }
}
```

**Error Responses:**
- `404 Not Found`: Sensor ID does not exist

**Example:**
```bash
curl -X GET "http://localhost:8000/api/sensors/V1"
```

---

### 3. Get Sensor History

**Endpoint:** `GET /api/sensors/{sensor_id}/history`

**Description:** Retrieve time-series historical data for a sensor with aggregation.

**Path Parameters:**
- `sensor_id` (string, required): Sensor identifier

**Query Parameters:**
- `start_time` (datetime, optional): ISO8601 timestamp. Default: 24 hours ago
- `end_time` (datetime, optional): ISO8601 timestamp. Default: current time
- `interval` (string, required): Aggregation interval. Default: "1h"
  - Valid values: `15m`, `1h`, `6h`, `1d`

**Response:** `200 OK`

```json
{
  "sensor_id": "string",
  "start_time": "datetime",
  "end_time": "datetime",
  "interval": "string",
  "readings": [
    {
      "timestamp": "datetime",
      "moisture": "float|null",
      "temperature": "float|null",
      "humidity": "float|null",
      "light": "integer|null"
    }
  ],
  "count": "integer"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid time range or parameters
- `404 Not Found`: Sensor ID does not exist
- `422 Unprocessable Entity`: Invalid interval value

**Constraints:**
- Maximum time range: 90 days
- `start_time` must be before `end_time`

**Examples:**

Last 24 hours (default):
```bash
curl -X GET "http://localhost:8000/api/sensors/V1/history"
```

Last 7 days with 6-hour intervals:
```bash
curl -X GET "http://localhost:8000/api/sensors/V1/history?start_time=2025-11-29T00:00:00Z&end_time=2025-12-06T00:00:00Z&interval=6h"
```

Custom range with 15-minute intervals:
```bash
curl -X GET "http://localhost:8000/api/sensors/V1/history?start_time=2025-12-06T08:00:00Z&end_time=2025-12-06T20:00:00Z&interval=15m"
```

---

### 4. Get Latest Reading

**Endpoint:** `GET /api/sensors/{sensor_id}/latest`

**Description:** Get the most recent reading from a specific sensor.

**Path Parameters:**
- `sensor_id` (string, required): Sensor identifier

**Response:** `200 OK`

```json
{
  "timestamp": "datetime",
  "moisture": "float|null",
  "temperature": "float|null",
  "humidity": "float|null",
  "light": "integer|null"
}
```

**Error Responses:**
- `404 Not Found`: Sensor ID does not exist or no data available

**Example:**
```bash
curl -X GET "http://localhost:8000/api/sensors/V1/latest"
```

---

### 5. Get All Sensors Summary (Cached)

**Endpoint:** `GET /api/sensors/summary`

**Description:** Get a summary of all sensors with their latest readings. This endpoint is optimized for high traffic and uses caching.

**Request Parameters:** None

**Response:** `200 OK`

```json
{
  "summary": [
    {
      "sensor_id": "string",
      "name": "string",
      "zone_id": "integer",
      "status": "string",
      "latest_reading": {
        "timestamp": "datetime",
        "moisture": "float|null",
        "temperature": "float|null",
        "humidity": "float|null",
        "light": "integer|null"
      }
    }
  ],
  "count": "integer",
  "cached": "boolean",
  "cache_timestamp": "datetime|null"
}
```

**Caching Behavior:**
- Cache TTL: 5 minutes (300 seconds)
- First request: `cached: false`
- Subsequent requests: `cached: true` (until TTL expires)
- Cache automatically refreshed after expiration

**Example:**
```bash
curl -X GET "http://localhost:8000/api/sensors/summary"
```

---

## Data Types

### Timestamp Format

All timestamps use ISO8601 format with UTC timezone:
```
2025-12-06T14:30:00Z
```

**Parsing Examples:**

Python:
```python
from datetime import datetime
dt = datetime.fromisoformat("2025-12-06T14:30:00Z".replace('Z', '+00:00'))
```

JavaScript:
```javascript
const date = new Date("2025-12-06T14:30:00Z");
```

### Sensor Measurements

| Field | Type | Unit | Range | Description |
|-------|------|------|-------|-------------|
| moisture | float | % | 0-100 | Soil moisture percentage |
| temperature | float | °C | -50 to 50 | Air/soil temperature |
| humidity | float | % | 0-100 | Relative humidity |
| light | integer | ADC | 0-1023 | Light sensor reading |

**Note:** All measurements can be `null` if sensor did not report that value.

---

## Sensor IDs and Zone Mapping

| Sensor ID | Name | Zone ID | Zone Name | Location |
|-----------|------|---------|-----------|----------|
| V1 | Orchard Zone 1 Sensor | 1 | Orchard Zone 1 | Orchard Section 1 |
| V2 | Orchard Zone 2 Sensor | 2 | Orchard Zone 2 | Orchard Section 2 |
| V3 | Orchard Zone 3 Sensor | 3 | Orchard Zone 3 | Orchard Section 3 |
| V4 | Orchard Zone 4 Sensor | 4 | Orchard Zone 4 | Orchard Section 4 |
| V5 | Potato Field Sensor | 5 | Potato Field | Potato Cultivation Area |

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters or time range |
| 404 | Not Found | Sensor ID doesn't exist or no data |
| 422 | Unprocessable Entity | Validation error (e.g., invalid interval) |
| 500 | Internal Server Error | Server-side error |

---

## Rate Limiting

**Current Status:** No rate limiting implemented  
**Recommended:** 
- Summary endpoint: 60 requests/minute per client
- Other endpoints: 120 requests/minute per client

---

## Performance SLA

| Endpoint | Target Response Time | P95 |
|----------|---------------------|-----|
| GET /api/sensors | <200ms | <300ms |
| GET /api/sensors/{id} | <200ms | <300ms |
| GET /api/sensors/{id}/latest | <150ms | <250ms |
| GET /api/sensors/{id}/history | <400ms | <500ms |
| GET /api/sensors/summary (cached) | <50ms | <100ms |
| GET /api/sensors/summary (uncached) | <300ms | <500ms |

---

## Best Practices

### 1. Use Summary Endpoint for Dashboard Grids

✅ **Recommended:**
```javascript
// Single request for all sensors
fetch('/api/sensors/summary')
  .then(res => res.json())
  .then(data => renderGrid(data.summary));
```

❌ **Avoid:**
```javascript
// Multiple requests (inefficient)
['V1', 'V2', 'V3', 'V4', 'V5'].forEach(id => {
  fetch(`/api/sensors/${id}`).then(...);
});
```

### 2. Choose Appropriate Aggregation Intervals

| Time Range | Recommended Interval | Data Points |
|------------|---------------------|-------------|
| Last 6 hours | 15m | 24 |
| Last 24 hours | 1h | 24 |
| Last 7 days | 6h | 28 |
| Last 30 days | 1d | 30 |

### 3. Handle Null Values Gracefully

```javascript
const moisture = reading.moisture ?? 'N/A';
const temp = reading.temperature?.toFixed(1) ?? '--';
```

### 4. Cache Client-Side for Charts

```javascript
// Cache history data locally to avoid re-fetching
const cache = new Map();
const cacheKey = `${sensorId}-${startTime}-${endTime}`;

if (!cache.has(cacheKey)) {
  const data = await fetchHistory(sensorId, startTime, endTime);
  cache.set(cacheKey, data);
}
```

---

## Integration Examples

### React Dashboard Component

```javascript
import { useEffect, useState } from 'react';

function SensorDashboard() {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSensors = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/sensors/summary');
        const data = await response.json();
        setSensors(data.summary);
      } catch (error) {
        console.error('Error fetching sensors:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSensors();
    const interval = setInterval(fetchSensors, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="sensor-grid">
      {sensors.map(sensor => (
        <div key={sensor.sensor_id} className="sensor-card">
          <h3>{sensor.name}</h3>
          <p>Status: {sensor.status}</p>
          {sensor.latest_reading && (
            <>
              <p>Moisture: {sensor.latest_reading.moisture}%</p>
              <p>Temp: {sensor.latest_reading.temperature}°C</p>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
```

### Recharts History Chart

```javascript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

function SensorHistoryChart({ sensorId }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchHistory = async () => {
      const endTime = new Date().toISOString();
      const startTime = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      
      const response = await fetch(
        `http://localhost:8000/api/sensors/${sensorId}/history?` +
        `start_time=${startTime}&end_time=${endTime}&interval=1h`
      );
      
      const result = await response.json();
      setData(result.readings);
    };

    fetchHistory();
  }, [sensorId]);

  return (
    <LineChart width={600} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="timestamp" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey="moisture" stroke="#8884d8" name="Moisture %" />
      <Line type="monotone" dataKey="temperature" stroke="#82ca9d" name="Temperature °C" />
    </LineChart>
  );
}
```

---

## OpenAPI/Swagger

Access interactive API documentation:

**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc  
**OpenAPI JSON:** http://localhost:8000/openapi.json

---

## Support

**Contact:** Rayyan  
**Documentation:** See `IMPLEMENTATION_DOCUMENTATION.md`  
**Issues:** Report via project issue tracker

---

**Version History:**
- 1.0 (2025-12-06): Initial release with all 5 endpoints
