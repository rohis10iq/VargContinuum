from fastapi import APIRouter, HTTPException
from models.user import UserCreate, UserLogin, Token
from utils.auth import hash_password, verify_password, create_access_token
import psycopg2

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="irrigation_db",
        user="irrigation_user",
        password="secure_pass"
    )

@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    # Insert new user
    hashed = hash_password(user.password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
        (user.email, hashed, user.role)
    )
    user_id = cursor.fetchone()[0]
    conn.commit()

    # Generate JWT token
    token = create_access_token(data={"sub": user.email, "role": user.role})

    cursor.close()
    conn.close()
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password_hash, role FROM users WHERE email = %s",
        (credentials.email,)
    )
    result = cursor.fetchone()

    # If no user or password mismatch
    if not result or not verify_password(credentials.password, result[0]):
        cursor.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": credentials.email, "role": result[1]})

    cursor.close()
    conn.close()

    return {"access_token": token, "token_type": "bearer"}