"""Authentication routes (Mock DB mode for deliverables)."""

from fastapi import APIRouter, HTTPException, status

from models.user import UserCreate, UserLogin
from utils.auth import hash_password, verify_password, create_access_token

# ✅ Router required by main.py
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# In-memory fake database
fake_users_db = {}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user."""
    if user.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Store hashed password
    fake_users_db[user.email] = {
        "password": hash_password(user.password),
        "role": user.role
    }

    # Generate JWT token
    token = create_access_token({
        "sub": user.email,
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/login")
async def login(user: UserLogin):
    """Login an existing user."""
    db_user = fake_users_db.get(user.email)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate JWT token
    token = create_access_token({
        "sub": user.email,
        "role": db_user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }
