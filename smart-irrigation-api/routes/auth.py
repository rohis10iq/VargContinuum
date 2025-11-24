"""Authentication routes for user registration and login."""

import psycopg2
from fastapi import APIRouter, HTTPException, status
from psycopg2.extras import RealDictCursor

from config import settings
from models.user import UserCreate, UserLogin
from utils.auth import hash_password, verify_password, create_access_token


router = APIRouter(prefix="/api/auth", tags=["authentication"])


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        return conn
    except psycopg2.Error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable"
        )


def init_users_table():
    """Create users table if it doesn't exist."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'farmer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
    finally:
        if conn:
            conn.close()


# Try creating table at startup
try:
    init_users_table()
except Exception:
    pass


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = hash_password(user.password)

        # Insert user
        cursor.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, %s)
            RETURNING email, role
            """,
            (user.email, hashed_password, user.role)
        )
        new_user = cursor.fetchone()
        conn.commit()
        cursor.close()

        # Generate token
        token = create_access_token(
            data={"sub": new_user["email"], "role": new_user["role"]}
        )

        # ✅ Required deliverable format
        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )
    finally:
        if conn:
            conn.close()


@router.post("/login")
async def login(user: UserLogin):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch user
        cursor.execute(
            "SELECT email, password_hash, role FROM users WHERE email = %s",
            (user.email,)
        )
        db_user = cursor.fetchone()
        cursor.close()

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Verify password
        if not verify_password(user.password, db_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Generate token
        token = create_access_token(
            data={"sub": db_user["email"], "role": db_user["role"]}
        )

        # ✅ Required deliverable format
        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )
    finally:
        if conn:
            conn.close()
