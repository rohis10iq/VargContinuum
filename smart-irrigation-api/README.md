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
