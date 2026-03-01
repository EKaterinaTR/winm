"""Pydantic schemas for auth API."""
from pydantic import BaseModel


class TokenRequest(BaseModel):
    """Body for POST /api/auth/token."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Response with JWT access token."""
    access_token: str
    token_type: str = "bearer"
