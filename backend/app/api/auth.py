from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse, SystemStatus, ChangePassword
from app.services.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    is_system_initialized,
    verify_password,
    get_password_hash,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """Check if system is initialized (first user created)"""
    initialized = await is_system_initialized(db)
    return SystemStatus(initialized=initialized)


@router.post("/setup", response_model=Token)
async def setup_admin(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """First time setup - create admin user"""
    # Check if already initialized
    if await is_system_initialized(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System already initialized"
        )

    # Create admin user
    user = await create_user(db, user_data.username, user_data.password)

    # Generate token
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token"""
    user = await authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.

    Requires the current password for verification and a new password.
    Passwords are sent in the request body for security (not in URL/query params).
    """
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from old password"
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}
