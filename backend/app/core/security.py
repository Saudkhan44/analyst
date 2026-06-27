"""
Security and JWT authentication module.

Handles Supabase JWT verification using the JWKS public keys.
"""

import logging
from typing import Optional

import requests
from fastapi import HTTPException, status
from jose import jwt, jwk
from jose.exceptions import JWTError

from app.core.config import settings

logger = logging.getLogger(__name__)

_jwks_cache = None


def get_supabase_jwks() -> dict:
    """Fetch and cache Supabase JWKS for JWT verification."""
    global _jwks_cache
    if _jwks_cache is None:
        try:
            response = requests.get(settings.SUPABASE_JWKS_URL, timeout=10)
            response.raise_for_status()
            _jwks_cache = response.json()
        except Exception as exc:
            logger.error(f"Unable to fetch Supabase JWKS: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to fetch authentication keys",
            )
    return _jwks_cache


def get_public_key_for_kid(kid: str):
    """Return the public key object for a given JWKS key id."""
    jwks = get_supabase_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwk.construct(key)

    logger.error(f"Unknown JWT key id: {kid}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unknown JWT key id",
        headers={"WWW-Authenticate": "Bearer"},
    )


class CurrentUser:
    """Current authenticated user information."""

    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email

    def __repr__(self) -> str:
        return f"<User {self.user_id}: {self.email}>"


def verify_jwt_token(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing JWT key id",
                headers={"WWW-Authenticate": "Bearer"},
            )

        public_key = get_public_key_for_kid(kid)

        payload = jwt.decode(
            token,
            public_key.to_dict(),
            algorithms=["ES256"],
            issuer=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
            options={
                "verify_aud": False,
            },
        )

        if payload.get("role") != "authenticated":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except HTTPException:
        raise

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as e:
        logger.exception("Unexpected JWT verification error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_user_from_token(payload: dict) -> CurrentUser:
    """
    Extract user information from JWT payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        CurrentUser: User information

    Raises:
        HTTPException: If required fields are missing
    """
    try:
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return CurrentUser(user_id=user_id, email=email)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting user from token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
