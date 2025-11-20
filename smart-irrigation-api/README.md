# Smart Irrigation API

A FastAPI-based REST API for smart irrigation management.

## Project Structure

```
smart-irrigation-api/
├── models/          # Data models
│   └── __init__.py
├── routes/          # API routes
│   └── __init__.py
├── utils/           # Utility functions
│   └── __init__.py
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
pip install sqlalchemy==2.0.36
pip install psycopg2-binary==2.9.9
```

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

- `GET /` - Root endpoint, returns welcome message.
- `GET /health` - Health check endpoint.

## Configuration

The application can be configured via `config.py`:

- `PROJECT_NAME`: API project name
- `VERSION`: API version
- `ALLOWED_ORIGINS`: List of allowed CORS origins
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

## Dependencies

- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **python-jose**: JWT token handling
- **passlib**: Password hashing utilities
- **python-multipart**: Multipart form data support
