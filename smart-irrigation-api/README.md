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

1. Install dependencies:
```bash
pip install -r requirements.txt
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

- `GET /` - Root endpoint, returns welcome message
- `GET /health` - Health check endpoint

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
