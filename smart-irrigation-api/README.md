# Smart Irrigation API

A FastAPI-based REST API for smart irrigation management with JWT authentication and InfluxDB time-series sensor data storage.

## Project Structure

```
smart-irrigation-api/
├── models/              # Data models
│   ├── __init__.py
│   ├── user.py          # User authentication models
│   └── sensor.py        # Sensor data models (NEW)
├── routes/              # API routes
│   ├── __init__.py
│   ├── user.py      # User authentication models
│   └── sensor.py    # Sensor data models
├── routes/          # API routes
│   ├── __init__.py
│   ├── auth.py      # Authentication endpoints
│   └── sensors.py   # Sensor data endpoints
├── services/        # Business logic layer
│   ├── __init__.py
│   └── influxdb_service.py  # InfluxDB integration
├── utils/           # Utility functions
│   ├── __init__.py
│   └── auth.py      # Password hashing and JWT utilities
├── tests/           # Test suite
│   ├── test_auth.py
│   └── test_sensors.py
├── config.py        # Application configuration
├── main.py          # FastAPI application entry point
├── test_influxdb.py # InfluxDB integration test
├── INFLUXDB_SETUP.md  # InfluxDB setup guide
└── requirements.txt # Python dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
cd smart-irrigation-api
pip install -r requirements.txt
```

### 2. Set Up Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration (PostgreSQL - for user authentication)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=smart_irrigation
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production

# InfluxDB Configuration (for sensor data)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token-here
INFLUXDB_ORG=smart-irrigation
INFLUXDB_BUCKET=sensor-data
```

**Important**: 
- Change the `SECRET_KEY` to a secure random string in production
- Get your InfluxDB token from http://localhost:8086 (Data → API Tokens)
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
- `GET /` - Root endpoint, returns welcome message
- `GET /health` - Health check endpoint

### Authentication Endpoints (`/api/auth`)
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - User login

### Sensor Endpoints (`/api/sensors`) 🆕
- `GET /api/sensors` - List all sensors
- `GET /api/sensors/{id}` - Get sensor details
- `GET /api/sensors/{id}/latest` - Get latest reading
- `GET /api/sensors/{id}/history` - Get historical readings
- `GET /api/sensors/summary` - Get sensors summary (cached)

For detailed API documentation, see:
- **Complete API Reference**: [Deliverables/Task C2.1/API_REFERENCE.md](./Deliverables/Task%20C2.1/API_REFERENCE.md)
- **Interactive Docs**: http://localhost:8000/docs (when running)

### Quick Examples

#### Get All Sensors
```bash
curl http://localhost:8000/api/sensors
```

#### Get Sensor History
```bash
curl "http://localhost:8000/api/sensors/sensor_temp_001/history?limit=100"
```

#### Get Sensors Summary (Cached)
```bash
curl http://localhost:8000/api/sensors/summary
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

## Configuration

The application can be configured via `config.py` or environment variables:

### Application Settings
- `PROJECT_NAME`: API project name
- `VERSION`: API version
- `ALLOWED_ORIGINS`: List of allowed CORS origins
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

### Database Settings (PostgreSQL)
- `DATABASE_HOST`: PostgreSQL host (default: localhost)
- `DATABASE_PORT`: PostgreSQL port (default: 5432)
- `DATABASE_NAME`: Database name (default: smart_irrigation)
- `DATABASE_USER`: Database user (default: postgres)
- `DATABASE_PASSWORD`: Database password (default: postgres)

### InfluxDB Settings 🆕
- `INFLUXDB_URL`: InfluxDB server URL (default: http://localhost:8086)
- `INFLUXDB_TOKEN`: Authentication token (required)
- `INFLUXDB_ORG`: Organization name (default: smart-irrigation)
- `INFLUXDB_BUCKET`: Bucket name (default: sensors)

### Cache Settings 🆕
- `CACHE_TTL_SECONDS`: Cache time-to-live in seconds (default: 300)

### JWT Settings
- `SECRET_KEY`: Secret key for JWT signing (required in production)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_HOURS`: Token expiration time in hours (default: 24)

## Dependencies

### Core Framework
- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **pydantic**: Data validation using Python type annotations
- **pydantic-settings**: Settings management
- **python-dotenv**: Environment variable management

### Authentication
- **python-jose**: JWT token handling
- **passlib**: Password hashing utilities with bcrypt
- **email-validator**: Email validation for Pydantic

### Databases
- **influxdb-client**: InfluxDB 2.x client for time-series data 🆕
- **sqlalchemy**: SQL toolkit and ORM
- **psycopg2-binary**: PostgreSQL database adapter
- **influxdb-client**: InfluxDB Python client for time-series data

### Performance
- **cachetools**: In-memory caching with TTL 🆕

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

## Security Features

- Passwords are hashed using bcrypt before storage
- JWT tokens are signed with HS256 algorithm
- Database connection errors don't expose sensitive information
- Timezone-aware datetime for token expiration
- Proper HTTP status codes for different error scenarios
- Environment-based configuration (no hardcoded credentials)
- Input validation with Pydantic models

## Performance Features 🆕

- **Caching**: TTL-based in-memory caching for summary endpoint
- **Query Optimization**: Efficient InfluxDB Flux queries with proper filtering
- **Configurable Limits**: Prevent excessive data retrieval
- **Time-range Filtering**: Query only needed data ranges

## Documentation 📚

Project documentation is available in the `Deliverables/` directory, organized by task.

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_sensors.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Development

### Project Status
✅ Week 1: Authentication system with JWT
✅ Week 2: Sensor API with InfluxDB integration and caching

### Recent Updates (Week 2)
- Added 5 sensor endpoints for real-time and historical data
- Integrated InfluxDB for time-series data storage
- Implemented caching for performance optimization
- Created comprehensive documentation and test suite
- Added Pydantic models for sensor data validation

## Troubleshooting

### InfluxDB Connection Issues
If you encounter InfluxDB connection errors:
1. Verify InfluxDB is running: `curl http://localhost:8086/health`
2. Check your token and credentials in `.env`
3. See [INFLUXDB_SETUP.md](./Deliverables/Task%20C2.1/INFLUXDB_SETUP.md) for setup help

### Import Errors
If you get module import errors:
```bash
# Make sure you're in the project directory
cd smart-irrigation-api

# Reinstall dependencies
pip install -r requirements.txt
```

## Contributing

When adding new features:
1. Follow existing code structure and patterns
2. Add comprehensive tests in `tests/`
3. Update documentation in `Deliverables/`
4. Use type hints for all functions
5. Validate input with Pydantic models

## Contact

For questions or issues, please refer to the documentation in the `Deliverables/` directory or contact your team lead.
