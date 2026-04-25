from jose import JWTError, jwt
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from app.core.config import settings


async def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    Returns payload if valid, raises HTTPException if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


async def get_current_user_id(token: str) -> str:
    """
    Extract user ID from JWT token.
    Compatible with fastapi-backend token structure.
    """
    payload = await decode_jwt_token(token)
    
    # fastapi-backend uses "user_id" field
    user_id: str = payload.get("user_id") or payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID"
        )
    return user_id


async def get_user_role(token: str) -> str:
    """
    Extract user role from JWT token.
    Compatible with fastapi-backend token structure.
    """
    payload = await decode_jwt_token(token)
    role: str = payload.get("role", "patient")
    return role


async def get_user_email(token: str) -> str:
    """
    Extract user email from JWT token.
    """
    payload = await decode_jwt_token(token)
    email: str = payload.get("email")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email"
        )
    return email


def extract_token_from_header(authorization: Optional[str]) -> str:
    """
    Extract bearer token from Authorization header.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    return parts[1]
