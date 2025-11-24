"""Authentication routes for user registration and login."""

import psycopg2
from fastapi import APIRouter, HTTPException, status
from psycopg2.extras import RealDictCursor

from config import settings
from models.user import UserCreate, UserLogin, Token
from utils.auth import hash_password, verify_password, create_access_token


router = APIRouter(prefix="/api/auth", tags=["authentication"])


def get_db_connection():
    """
    Create and return a PostgreSQL database connection.
    
    Returns:
        Database connection object
    """
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


def init_users_table():
    """Initialize users table if it doesn't exist."""
    conn = None
    try:
        conn = get_db_connection()
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
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


# Initialize table on module import
try:
    init_users_table()
except Exception:
    # Silently fail if database is not available during import
    pass


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register a new user.
    
    Args:
        user: UserCreate model with email, password, and role
        
    Returns:
        Token with access_token and token_type
        
    Raises:
        HTTPException: If email already exists or database error occurs
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        hashed_password = hash_password(user.password)
        
        # Insert new user
        cursor.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, %s)
            RETURNING id, email, role
            """,
            (user.email, hashed_password, user.role)
        )
        
        new_user = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        # Create access token
        access_token = create_access_token(
            data={"sub": new_user["email"], "role": new_user["role"]}
        )
        
        return Token(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )
    finally:
        if conn:
            conn.close()


@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    """
    Login an existing user.
    
    Args:
        user: UserLogin model with email and password
        
    Returns:
        Token with access_token and token_type
        
    Raises:
        HTTPException: If credentials are invalid
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user from database
        cursor.execute(
            "SELECT id, email, password_hash, role FROM users WHERE email = %s",
            (user.email,)
        )
        db_user = cursor.fetchone()
        cursor.close()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(user.password, db_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": db_user["email"], "role": db_user["role"]}
        )
        
        return Token(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
    finally:
        if conn:
            conn.close()
