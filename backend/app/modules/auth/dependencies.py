"""
Authentication dependencies.

Provides JWT validation dependency for FastAPI routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.security import verify_jwt_token, extract_user_from_token, CurrentUser

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    """
    Get current authenticated user from JWT token.

    This dependency is used in all protected endpoints.
    It verifies the JWT token and extracts user information.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        CurrentUser: Current authenticated user

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials

    # Verify and decode token
    payload = verify_jwt_token(token)

    # Extract user information
    current_user = extract_user_from_token(payload)

    return current_user
