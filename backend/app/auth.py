"""
Authentication module for Qari App
JWT-based authentication with password hashing
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os

# Security settings
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "qari-app-super-secret-key-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


# In-memory user store (replace with database in production)
users_db: dict = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Dependency to get the current authenticated user."""
    token = credentials.credentials
    return decode_token(token)


def register_user(user_data: UserCreate) -> UserResponse:
    """Register a new user."""
    import uuid

    # Check if email already exists
    for user in users_db.values():
        if user["email"] == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)

    user = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
    }
    users_db[user_id] = user

    return UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        created_at=user["created_at"],
    )


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user by email and password."""
    for user in users_db.values():
        if user["email"] == email:
            if verify_password(password, user["hashed_password"]):
                return user
            return None
    return None


def login_user(login_data: UserLogin) -> Token:
    """Login a user and return access token."""
    user = authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})

    return Token(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
