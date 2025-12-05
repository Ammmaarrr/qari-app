"""
Authentication routes for Qari App
"""

from fastapi import APIRouter, Depends
from ..auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
    register_user,
    login_user,
    get_current_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user account."""
    return register_user(user_data)


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login and get access token."""
    return login_user(login_data)


@router.get("/me", response_model=TokenData)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: TokenData = Depends(get_current_user)):
    """Refresh access token."""
    from ..auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

    access_token = create_access_token(
        data={"sub": current_user.user_id, "email": current_user.email}
    )
    return Token(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
