# Smart Irrigation API

A FastAPI-based REST API for smart irrigation management with JWT authentication.

## Project Structure

```
smart-irrigation-api/
├── models/          # Data models
│   ├── __init__.py
│   └── user.py      # User authentication models
├── routes/          # API routes
│   ├── __init__.py
│   └── auth.py      # Authentication endpoints
├── utils/           # Utility functions
│   ├── __init__.py
│   └── auth.py      # Password hashing and JWT utilities
├── config.py        # Application configuration
├── main.py          # FastAPI application entry point
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
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=smart_irrigation
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production
```

**Important**: Change the `SECRET_KEY` to a secure random string in production.

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
- `GET /` - Root endpoint, returns welcome message.
- `GET /health` - Health check endpoint.

### Authentication Endpoints (Task C1.x)

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

### InfluxDB Settings (Task B2.1)
- `INFLUXDB_URL`: InfluxDB server URL (default: http://localhost:8086)
- `INFLUXDB_TOKEN`: InfluxDB authentication token
- `INFLUXDB_ORG`: InfluxDB organization name (default: smart-irrigation)
- `INFLUXDB_BUCKET`: InfluxDB bucket for sensor data (default: sensor-data)

### Cache Settings
- `CACHE_TTL_SECONDS`: Cache time-to-live for summary endpoint (default: 300)

## Dependencies

### Core Framework
- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **pydantic**: Data validation using Python type annotations
- **pydantic-settings**: Settings management
- **python-dotenv**: Environment variable management

### Authentication (Task C1.x)
- **python-jose**: JWT token handling
- **passlib**: Password hashing utilities with bcrypt
- **python-multipart**: Multipart form data support
- **email-validator**: Email validation for Pydantic

### Database
- **sqlalchemy**: SQL toolkit and ORM
- **psycopg2-binary**: PostgreSQL database adapter
- **influxdb-client**: InfluxDB client for time-series sensor data (Task B2.1)

### Caching & Performance
- **cachetools**: In-memory caching with TTL support (Task B2.1)

### Testing
- **pytest**: Testing framework
- **httpx**: HTTP client for testing

## Authentication Features

- **JWT (JSON Web Tokens)**: Secure token-based authentication
- **Password Hashing**: Using bcrypt via passlib for secure password storage
- **Token Expiry**: 24-hour access token validity
- **Role-based Access**: Users have roles (e.g., "farmer") for future authorization
- **Email Validation**: Ensures valid email format during registration
- **PostgreSQL Storage**: User data stored in PostgreSQL database

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

### Sensor Data Endpoints (Task B2.1) ✅ COMPLETED

The Sensor Data API provides comprehensive access to IoT sensor data for the smart irrigation dashboard.

#### Endpoints

1. **`GET /api/sensors`** - List all sensors with status and metadata
2. **`GET /api/sensors/{id}`** - Get detailed sensor information with latest reading
3. **`GET /api/sensors/{id}/history`** - Get time-series historical data with aggregation
4. **`GET /api/sensors/{id}/latest`** - Get the most recent sensor reading
5. **`GET /api/sensors/summary`** - Get all sensors summary (cached, optimized for dashboard)

#### Features

- ⚡ **High Performance**: All endpoints respond in <500ms
- 📊 **Time-Series Data**: Historical queries with flexible aggregation (15m, 1h, 6h, 1d)
- 🗄️ **Caching**: 5-minute cache for high-traffic summary endpoint
- 📡 **Real-time Status**: Sensor status monitoring (active/inactive/error)
- 🌐 **ISO8601 Timestamps**: Standard timestamp format for all responses
- 📈 **Chart-Ready Data**: Responses optimized for Recharts library

#### Quick Examples

```bash
# List all sensors
curl http://localhost:8000/api/sensors

# Get sensor V1 details
curl http://localhost:8000/api/sensors/V1

# Get 24-hour history with 1-hour intervals
curl "http://localhost:8000/api/sensors/V1/history?interval=1h"

# Get latest reading
curl http://localhost:8000/api/sensors/V1/latest

# Get dashboard summary (cached)
curl http://localhost:8000/api/sensors/summary
```

#### Sensor-Zone Mapping

| Sensor ID | Zone | Description |
|-----------|------|-------------|
| V1 | Zone 1 | Orchard Zone 1 |
| V2 | Zone 2 | Orchard Zone 2 |
| V3 | Zone 3 | Orchard Zone 3 |
| V4 | Zone 4 | Orchard Zone 4 |
| V5 | Zone 5 | Potato Field |

#### Documentation

See **`Deliverables/TaskR B2.1/`** for complete documentation:
- `IMPLEMENTATION_DOCUMENTATION.md` - Full implementation details
- `API_SPECIFICATION.md` - Complete API reference
- `TESTING_GUIDE.md` - Testing instructions and results
- `Sensor_Data_API.postman_collection.json` - Postman collection

## Security Features

- Passwords are hashed using bcrypt before storage
- JWT tokens are signed with HS256 algorithm
- Database connection errors don't expose sensitive information
- Timezone-aware datetime for token expiration
- Proper HTTP status codes for different error scenarios
