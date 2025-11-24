"""Authentication routes for user registration and login (Deliverable Mode)."""

from fastapi import APIRouter, HTTPException, status
from models.user import UserCreate, UserLogin
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# In-memory "fake database"
fake_users_db = {}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    if user.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and store
    fake_users_db[user.email] = {
        "password": hash_password(user.password),
        "role": user.role
    }

    # Generate token
    token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/login")
async def login(user: UserLogin):
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

    # Generate token
    token = create_access_token(
        data={"sub": user.email, "role": db_user["role"]}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
