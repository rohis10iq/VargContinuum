# Smart Irrigation API

A comprehensive FastAPI-based REST API for smart irrigation management with real-time WebSocket streaming, MQTT integration, JWT authentication, and InfluxDB time-series sensor data storage.

## Features

- 🔐 **JWT Authentication**: Secure user registration and login with token-based auth
- 📊 **Time-Series Data**: InfluxDB integration for sensor data storage and querying
- 🌐 **Real-Time Streaming**: WebSocket support for live sensor updates with JWT authentication
- 📡 **MQTT Integration**: Subscribe to MQTT broker for sensor data and publish irrigation commands
- 💧 **Irrigation Control**: Manual and automated irrigation triggers with safety checks
- 🛡️ **Safety Mechanisms**: Over-irrigation prevention, saturation risk detection, conflict prevention
- 🔄 **Auto-Broadcasting**: Sensor data automatically streams to connected clients (rate-limited)
- 💓 **Heartbeat Mechanism**: Keeps WebSocket connections alive (30s interval)
- 📈 **Historical Data**: Query sensor history with custom aggregations (24h, 7d, 30d)
- 🧪 **Comprehensive Testing**: Unit tests, Postman collections, and interactive HTML test UI
- 📚 **Auto-Documentation**: Swagger UI and ReDoc included

## Project Structure

```
smart-irrigation-api/
├── models/          # Data models
│   ├── __init__.py
│   ├── user.py      # User authentication models
│   ├── sensor.py    # Sensor data models
│   ├── websocket.py # WebSocket message models
│   └── irrigation.py # Irrigation control models
├── routes/          # API routes
│   ├── __init__.py
│   ├── auth.py      # Authentication endpoints
│   ├── sensors.py   # Sensor data endpoints
│   ├── websocket.py # WebSocket endpoints
│   └── irrigation.py # Irrigation control endpoints
├── services/        # Business logic layer
│   ├── __init__.py
│   ├── influxdb_service.py  # InfluxDB integration
│   ├── websocket_manager.py # WebSocket connection manager
│   ├── mqtt_service.py      # MQTT broker integration
│   └── irrigation_service.py # Irrigation control logic
├── utils/           # Utility functions
│   ├── __init__.py
│   └── auth.py      # Password hashing and JWT utilities
├── tests/           # Test suite
│   ├── test_auth.py
│   ├── test_sensors.py
│   ├── test_websocket_manager.py  # WebSocket unit tests
│   ├── test_websocket_manual.py   # Manual WebSocket tests
│   └── websocket_test.html        # Interactive WebSocket test UI
├── config.py        # Application configuration
├── main.py          # FastAPI application entry point
├── test_influxdb.py # InfluxDB integration test
├── INFLUXDB_SETUP.md  # InfluxDB setup guide
├── Smart_Irrigation_Control.postman_collection.json  # Irrigation API tests
├── Smart_Irrigation_Sensors.postman_collection.json  # Sensor API tests
└── requirements.txt # Python dependencies
```

## Installation

### Option 1: Install dependencies from requirements.txt:
```bash
pip install -r requirements.txt
```
### Option 2: Install dependencies manually:

```bash
pip install fastapi==0.115.5
pip install "uvicorn[standard]==0.32.0"
pip install python-jose==3.3.0
pip install "passlib[bcrypt]==1.7.4"
pip install python-multipart==0.0.9
pip install pydantic==2.9.2
pip install pydantic-settings==2.5.2
pip install python-dotenv==1.0.1
pip install email-validator==2.2.0
pip install sqlalchemy==2.0.36
pip install psycopg2-binary==2.9.9
```

## Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database Configuration (PostgreSQL - for user authentication)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=smart_irrigation
DATABASE_USER=syedkhadeen
DATABASE_PASSWORD=12345678

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production

# InfluxDB Configuration (for sensor data)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token-here
INFLUXDB_ORG=SmartIrrigation
INFLUXDB_BUCKET=sensor_data

# MQTT Broker Configuration (for sensor updates and irrigation commands)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_TOPIC_PREFIX=sensors/#
MQTT_CLIENT_ID=smart-irrigation-api

# WebSocket Configuration
WS_RATE_LIMIT_SECONDS=1.0
```

**Important**: 
- Change the `SECRET_KEY` to a secure random string in production
- Get your InfluxDB token from http://localhost:8086 (Data → API Tokens)
- MQTT broker is optional for testing - API will work without it
- See [INFLUXDB_SETUP.md](INFLUXDB_SETUP.md) for detailed InfluxDB setup instructions

## Running the Server

Start the development server:
```bash
python main.py
```

The server will start on `http://0.0.0.0:8000`

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Available Endpoints

### General Endpoints
- `GET /` - Root endpoint, returns welcome message and WebSocket endpoint information
- `GET /health` - Health check endpoint with WebSocket connection statistics

### Authentication Endpoints

#### Register a New User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "farmer"  # Optional, defaults to "farmer"
}
```

**Response**: 
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Sensor Data Endpoints

#### Write Sensor Data
```bash
POST /api/sensors/write
Content-Type: application/json

{
  "sensor_id": "soil_sensor_01",
  "sensor_type": "soil_moisture",
  "value": 45.5,
  "location": "field_a"
}
```

#### Get Historical Data
```bash
# 24-hour history (5-minute aggregation)
GET /api/sensors/history/24h?sensor_id=soil_sensor_01

# 7-day history (1-hour aggregation)
GET /api/sensors/history/7d?sensor_type=soil_moisture

# 30-day history (6-hour aggregation)
GET /api/sensors/history/30d?sensor_id=soil_sensor_01

# Custom aggregation
GET /api/sensors/aggregate?start_time=2025-11-27T00:00:00Z&window=30m&function=max
```

**Supported aggregation functions**: `mean`, `max`, `min`, `sum`, `count`

### WebSocket Endpoints (Real-Time Streaming)

The API provides WebSocket endpoints for real-time sensor data streaming. These endpoints allow clients to receive live updates as sensor data changes.

#### Connect to Specific Sensor Stream
```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/sensors/soil_sensor_01');

ws.onopen = () => {
  console.log('Connected to sensor stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  // Message types:
  // - type: "connect" - Connection confirmation
  // - type: "update" - Sensor data update
  // - type: "heartbeat" - Keep-alive ping (every 30s)
  // - type: "error" - Error notification
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Endpoint**: `ws://localhost:8000/ws/sensors/{sensor_id}`

**What you receive:**
1. Connection confirmation message
2. Latest sensor data (if available)
3. Real-time updates when this sensor's data changes
4. Heartbeat messages every 30 seconds

**Example messages:**
```json
// Connection confirmation
{
  "type": "connect",
  "timestamp": "2025-12-04T20:00:00Z",
  "message": "Connected to sensor stream: soil_sensor_01",
  "sensor_id": "soil_sensor_01"
}

// Sensor update
{
  "type": "update",
  "timestamp": "2025-12-04T20:01:30Z",
  "sensor_id": "soil_sensor_01",
  "sensor_type": "soil_moisture",
  "value": 45.5,
  "location": "field_a"
}

// Heartbeat
{
  "type": "heartbeat",
  "timestamp": "2025-12-04T20:02:00Z",
  "message": "ping"
}
```

#### Connect to All Sensors Stream
```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/sensors/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'summary') {
    // Initial dashboard summary with all sensors
    console.log('All sensors:', data.data);
  } else if (data.type === 'update') {
    // Real-time update from any sensor
    console.log(`${data.sensor_id}: ${data.value}`);
  }
};
```

**Endpoint**: `ws://localhost:8000/ws/sensors/stream`

**What you receive:**
1. Connection confirmation message
2. Dashboard summary (latest data from all sensors)
3. Real-time updates from ALL sensors
4. Heartbeat messages every 30 seconds

**Example messages:**
```json
// Connection confirmation
{
  "type": "connect",
  "timestamp": "2025-12-04T20:00:00Z",
  "message": "Connected to global sensor stream"
}

// Dashboard summary
{
  "type": "summary",
  "message": "Current sensor summary",
  "count": 3,
  "data": [
    {
      "sensor_id": "soil_sensor_01",
      "sensor_type": "soil_moisture",
      "value": 45.5,
      "location": "field_a",
      "timestamp": "2025-12-04T19:59:00Z"
    },
    // ... more sensors
  ]
}

// Real-time update from any sensor
{
  "type": "update",
  "timestamp": "2025-12-04T20:01:30Z",
  "sensor_id": "temp_sensor_02",
  "sensor_type": "temperature",
  "value": 22.3,
  "location": "field_b"
}
```

#### WebSocket Connection Statistics
```bash
GET /ws/stats
```

**Response:**
```json
{
  "global_connections": 5,
  "sensor_connections": {
    "soil_sensor_01": 2,
    "temp_sensor_02": 1
  },
  "total_connections": 8
}
```

#### Testing WebSocket Connections

**Option 1: Interactive HTML Test Interface**
```bash
# Open in your browser
open tests/websocket_test.html
```

Features:
- Connect to specific sensor or all sensors
- View real-time messages with color coding
- Send test data via REST API
- Monitor connection statistics
- Clear log functionality

**Option 2: Python Test Script**
```bash
python tests/test_websocket_manual.py
```

**Option 3: Using `wscat` (command-line tool)**
```bash
# Install wscat
npm install -g wscat

# Connect to specific sensor
wscat -c ws://localhost:8000/ws/sensors/soil_sensor_01

# Connect to all sensors
wscat -c ws://localhost:8000/ws/sensors/stream
```

#### WebSocket Message Types

All WebSocket messages follow a structured format:

| Type | Description | When Sent |
|------|-------------|-----------|
| `connect` | Connection confirmation | When client first connects |
| `update` | Sensor data update | When sensor data is written via POST /api/sensors/write |
| `summary` | Dashboard summary | On connection to global stream |
| `heartbeat` | Keep-alive ping | Every 30 seconds to all connections |
| `error` | Error notification | When an error occurs |

#### WebSocket Features

✅ **Automatic Reconnection Handling**: Clients should implement reconnection logic  
✅ **Heartbeat/Ping**: Keeps connections alive (30-second interval)  
✅ **Broadcast to Multiple Clients**: All connected clients receive updates  
✅ **Sensor-Specific Subscriptions**: Subscribe to individual sensors  
✅ **Global Stream**: Monitor all sensors simultaneously  
✅ **Error Handling**: Graceful disconnection and error messages  
✅ **Connection Tracking**: Monitor active connections via `/ws/stats`  
✅ **CORS Enabled**: Cross-origin WebSocket connections supported  

#### Integration with REST API

When you write sensor data via the REST API, it automatically broadcasts to WebSocket clients:

```bash
# 1. Write sensor data via REST API
POST /api/sensors/write
{
  "sensor_id": "soil_sensor_01",
  "sensor_type": "soil_moisture",
  "value": 45.5,
  "location": "field_a"
}

# 2. All connected WebSocket clients receive the update immediately
# - Clients on ws://localhost:8000/ws/sensors/soil_sensor_01
# - Clients on ws://localhost:8000/ws/sensors/stream
```

This creates a complete real-time pipeline:
```
Sensor → REST API → InfluxDB → WebSocket Broadcast → All Clients
```

---

## Irrigation Control API (B2.3)

The API provides comprehensive irrigation control endpoints for manual and automated irrigation triggers with built-in safety mechanisms.

### Zone Configuration

| Zone ID | Name | Type | Description |
|---------|------|------|-------------|
| 1 | Orchard A | orchard | Apple trees section |
| 2 | Orchard B | orchard | Pear trees section |
| 3 | Orchard C | orchard | Cherry trees section |
| 4 | Orchard D | orchard | Mixed fruit section |
| 5 | Potato Field | potato | Main potato cultivation |

### Safety Mechanisms

All irrigation requests are validated against multiple safety checks:

- ✅ **Zone Validation**: Only zones 1-5 are valid
- ✅ **Conflict Prevention**: Cannot start irrigation if zone is already active
- ✅ **Daily Limit**: Maximum 2 hours (120 minutes) per zone per day
- ✅ **Saturation Prevention**: Blocks irrigation if soil moisture > 85%

### Irrigation Endpoints

#### Trigger Manual Irrigation
```bash
POST /api/irrigation/manual
Content-Type: application/json

{
  "zone_id": 1,
  "duration_minutes": 30,
  "trigger_type": "manual",
  "user_id": "technician_01"
}
```

**Response (Success):**
```json
{
  "success": true,
  "event_id": 1,
  "zone_id": 1,
  "zone_name": "Orchard A",
  "duration_minutes": 30,
  "status": "running",
  "mqtt_published": true,
  "message": "Irrigation started for zone 1 (Orchard A)"
}
```

**Response (Safety Block - Saturation):**
```json
{
  "success": false,
  "error": "saturation_risk",
  "error_code": "MOISTURE_TOO_HIGH",
  "message": "Zone 1 soil moisture is 87.5% (threshold: 85%). Irrigation blocked to prevent saturation.",
  "zone_id": 1
}
```

#### Create Irrigation Schedule
```bash
POST /api/irrigation/schedule
Content-Type: application/json

{
  "zone_id": 2,
  "duration_minutes": 20,
  "schedule_time": "2025-12-07T06:00:00Z",
  "repeat_pattern": "daily",
  "user_id": "scheduler_01"
}
```

**Response:**
```json
{
  "success": true,
  "schedule_id": 1,
  "message": "Schedule created for zone 2",
  "schedule": {
    "id": 1,
    "zone_id": 2,
    "zone_name": "Orchard B",
    "schedule_time": "2025-12-07T06:00:00Z",
    "duration_minutes": 20,
    "repeat_pattern": "daily",
    "is_active": true
  }
}
```

#### Get All Zones Status
```bash
GET /api/irrigation/status
```

**Response:**
```json
{
  "zones": [
    {
      "zone_id": 1,
      "zone_name": "Orchard A",
      "zone_type": "orchard",
      "is_active": true,
      "current_duration_minutes": 5,
      "remaining_minutes": 25,
      "started_at": "2025-12-06T10:00:00Z",
      "moisture_level": 45.2,
      "daily_irrigation_minutes": 35
    },
    {
      "zone_id": 2,
      "zone_name": "Orchard B",
      "is_active": false,
      "moisture_level": 62.1,
      "daily_irrigation_minutes": 0
    }
    // ... zones 3, 4, 5
  ],
  "active_count": 1,
  "timestamp": "2025-12-06T10:05:00Z"
}
```

#### Get Irrigation History
```bash
# All events
GET /api/irrigation/history?page=1&page_size=20

# Filter by zone
GET /api/irrigation/history?zone_id=1
```

**Response:**
```json
{
  "events": [
    {
      "id": 1,
      "zone_id": 1,
      "zone_name": "Orchard A",
      "start_time": "2025-12-06T10:00:00Z",
      "end_time": "2025-12-06T10:30:00Z",
      "duration_minutes": 30,
      "actual_duration_minutes": 30,
      "trigger_type": "manual",
      "user_id": "technician_01",
      "status": "completed"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

#### Update/Cancel Schedule
```bash
PUT /api/irrigation/schedule/1
Content-Type: application/json

{
  "is_active": false  # Cancel schedule
}
```

#### Emergency Stop All Zones
```bash
POST /api/irrigation/stop_all?user_id=emergency_operator
```

**Response:**
```json
{
  "success": true,
  "stopped_zones": [1, 3],
  "failed_zones": [],
  "mqtt_published": true,
  "message": "Emergency stop executed. Stopped 2 zones."
}
```

#### Stop Specific Zone
```bash
POST /api/irrigation/stop/1?user_id=technician_01
```

### MQTT Integration

When irrigation is triggered, the API publishes commands to the MQTT broker:

**Topic Pattern:** `irrigation/control/{zone_id}`

**Start Command:**
```json
{
  "action": "start",
  "duration": 30
}
```

**Stop Command:**
```json
{
  "action": "stop"
}
```

**Example:**
- Trigger irrigation for zone 1 → Publishes to `irrigation/control/1`
- IoT devices subscribed to this topic receive the command
- Physical valves are controlled by IoT devices (not directly by API)

### Testing Irrigation Endpoints

**Postman Collection:**
```bash
# Import the collection
Smart_Irrigation_Control.postman_collection.json
```

**Swagger UI:**
```
http://localhost:8000/docs
# Navigate to "irrigation" section
```

**curl Examples:**
```bash
# Trigger irrigation
curl -X POST http://localhost:8000/api/irrigation/manual \
  -H "Content-Type: application/json" \
  -d '{"zone_id": 1, "duration_minutes": 30, "trigger_type": "manual", "user_id": "tech_01"}'

# Get status
curl http://localhost:8000/api/irrigation/status

# Emergency stop
curl -X POST "http://localhost:8000/api/irrigation/stop_all?user_id=emergency"
```



## Configuration

The application can be configured via `config.py` or environment variables:

### Application Settings
- `PROJECT_NAME`: API project name
- `VERSION`: API version
- `ALLOWED_ORIGINS`: List of allowed CORS origins
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

### Database Settings
- `DATABASE_HOST`: PostgreSQL host (default: localhost)
- `DATABASE_PORT`: PostgreSQL port (default: 5432)
- `DATABASE_NAME`: Database name (default: smart_irrigation)
- `DATABASE_USER`: Database user (default: postgres)
- `DATABASE_PASSWORD`: Database password (default: postgres)

### JWT Settings
- `SECRET_KEY`: Secret key for JWT signing (required in production)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_HOURS`: Token expiration time in hours (default: 24)

## Dependencies

- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **python-jose**: JWT token handling
- **passlib**: Password hashing utilities with bcrypt
- **python-multipart**: Multipart form data support
- **pydantic**: Data validation using Python type annotations
- **pydantic-settings**: Settings management
- **python-dotenv**: Environment variable management
- **email-validator**: Email validation for Pydantic
- **sqlalchemy**: SQL toolkit and ORM
- **psycopg2-binary**: PostgreSQL database adapter
- **influxdb-client**: InfluxDB Python client for time-series data
- **websockets**: WebSocket client/server implementation for real-time communication
- **pytest**: Testing framework (dev dependency)

## Authentication Features

- **JWT (JSON Web Tokens)**: Secure token-based authentication
- **Password Hashing**: Using bcrypt via passlib for secure password storage
- **Token Expiry**: 24-hour access token validity
- **Role-based Access**: Users have roles (e.g., "farmer") for future authorization
- **Email Validation**: Ensures valid email format during registration
- **PostgreSQL Storage**: User data stored in PostgreSQL database

## WebSocket Features

The Smart Irrigation API includes a complete WebSocket infrastructure for real-time sensor data streaming:

### Core Components

#### 1. Connection Manager (`services/websocket_manager.py`)
- **Connection Tracking**: Maintains separate lists for global and sensor-specific connections
- **Lifecycle Management**: Handles connect/disconnect events with automatic cleanup
- **Broadcasting System**: 
  - `broadcast()` - Send to all global stream clients
  - `broadcast_to_sensor()` - Send to sensor-specific clients
  - `broadcast_sensor_update()` - High-level sensor update broadcaster
- **Heartbeat Mechanism**: Sends ping every 30 seconds to keep connections alive
- **Statistics**: Real-time connection monitoring via `get_connection_stats()`

#### 2. WebSocket Routes (`routes/websocket.py`)
- **`/ws/sensors/{sensor_id}`**: Stream data from a specific sensor
- **`/ws/sensors/stream`**: Stream data from all sensors
- **`/ws/stats`**: Get connection statistics (REST endpoint)

#### 3. Message Models (`models/websocket.py`)
Structured message types with Pydantic validation:
- `ConnectMessage` - Connection confirmation
- `SensorUpdateMessage` - Real-time sensor updates
- `HeartbeatMessage` - Keep-alive pings
- `ErrorMessage` - Error notifications
- `MessageType` enum - Type safety for all messages

### Real-Time Pipeline

```
IoT Sensor → POST /api/sensors/write → InfluxDB → WebSocket Broadcast → All Connected Clients
```

When sensor data is written via REST API, it automatically broadcasts to:
1. All clients connected to the global stream (`/ws/sensors/stream`)
2. All clients connected to that specific sensor (`/ws/sensors/{sensor_id}`)

### Connection Features

- ✅ **Automatic Heartbeat**: 30-second ping/pong to prevent timeouts
- ✅ **Graceful Disconnection**: Proper cleanup on connection loss
- ✅ **Error Handling**: Comprehensive error messages and logging
- ✅ **Multiple Clients**: Support for unlimited concurrent connections
- ✅ **Sensor Filtering**: Subscribe to specific sensors or all sensors
- ✅ **Initial Data**: Sends latest data immediately on connection
- ✅ **CORS Support**: Cross-origin WebSocket connections enabled
- ✅ **Monitoring**: Real-time connection statistics

### Testing Tools

1. **Interactive HTML UI**: `tests/websocket_test.html`
   - Visual connection testing
   - Real-time message log with color coding
   - Statistics dashboard
   - Send test data functionality

2. **Python Test Script**: `tests/test_websocket_manual.py`
   - Automated connection testing
   - Multi-client simulation
   - Concurrent connection testing

3. **Unit Tests**: `tests/test_websocket_manager.py`
   - Connection manager tests
   - Broadcast functionality tests
   - Statistics tests

### Lifecycle Management

The WebSocket infrastructure is integrated into the FastAPI application lifecycle:

**On Startup** (`main.py`):
```python
# Start heartbeat task
connection_manager.heartbeat_task = asyncio.create_task(
    connection_manager.start_heartbeat()
)
```

**On Shutdown** (`main.py`):
```python
# Cancel heartbeat task gracefully
if connection_manager.heartbeat_task:
    connection_manager.heartbeat_task.cancel()
```

### Production Ready

- ✅ Comprehensive error handling throughout
- ✅ Logging configured for debugging and monitoring
- ✅ Automatic cleanup of dead connections
- ✅ Type hints and Pydantic validation
- ✅ Tested with multiple concurrent clients
- ✅ Documentation in code and README
- ✅ Health check integration

## Database Schema

The authentication system automatically creates a `users` table with the following schema:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'farmer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Features

- Passwords are hashed using bcrypt before storage
- JWT tokens are signed with HS256 algorithm
- Database connection errors don't expose sensitive information
- Timezone-aware datetime for token expiration
- Proper HTTP status codes for different error scenarios
