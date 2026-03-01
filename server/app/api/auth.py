"""Auth API: issue JWT token (no auth required for this endpoint)."""
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.auth import create_access_token
from app.models.schemas import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def login(body: TokenRequest) -> TokenResponse:
    """
    Issue JWT access token for API.
    Use credentials from env: API_USERNAME, API_PASSWORD (or defaults api/api).
    """
    if body.username != settings.api_username or body.password != settings.api_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(sub=body.username)
    return TokenResponse(access_token=token, token_type="bearer")
