"""
Authentication API routes.

Endpoints for user information.
"""

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import CurrentUser
from app.modules.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


class UserResponse(BaseModel):
    """User information response."""

    user_id: str
    email: str


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: User information
    """
    logger.info(f"User info requested: {current_user.email}")
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
    )
