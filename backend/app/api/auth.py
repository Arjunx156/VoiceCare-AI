"""
CommerceMind VoiceCare AI — Authentication Routes & JWT Utilities
Provides admin login and a reusable FastAPI dependency for protected routes.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import AuthError, ErrorMessages

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)

_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 24


# ----------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = _TOKEN_EXPIRE_HOURS * 3600


# ----------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------

def _create_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)},
        settings.nextauth_secret,
        algorithm=_ALGORITHM,
    )


def _verify_token(token: str) -> Optional[str]:
    """Return the subject claim, or None if token is invalid/expired."""
    try:
        payload = jwt.decode(token, settings.nextauth_secret, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ----------------------------------------------------------------
# Dependency: require a valid admin JWT
# ----------------------------------------------------------------

async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
) -> str:
    """FastAPI dependency — raises 401 if the bearer token is missing or invalid."""
    if not credentials:
        raise HTTPException(status_code=401, detail=ErrorMessages.INVALID_CREDENTIALS)
    subject = _verify_token(credentials.credentials)
    if not subject:
        raise HTTPException(status_code=401, detail="Token invalid or expired.")
    return subject


# ----------------------------------------------------------------
# Routes
# ----------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def admin_login(body: LoginRequest):
    """Authenticate with admin credentials; returns a JWT bearer token."""
    email_match = body.email.lower().strip() == settings.admin_email.lower().strip()
    # Compare provided password against stored (bcrypt if hashed, plain-text fallback for dev)
    stored = settings.admin_password
    if stored.startswith("$2"):
        password_match = _pwd_context.verify(body.password, stored)
    else:
        password_match = body.password == stored

    if not email_match or not password_match:
        logger.warning("admin_login_failed", email=body.email)
        raise HTTPException(status_code=401, detail=ErrorMessages.INVALID_CREDENTIALS)

    token = _create_token(subject=body.email)
    logger.info("admin_login_success", email=body.email)
    return TokenResponse(access_token=token)


@router.get("/me")
async def whoami(subject: str = Depends(require_admin)):
    """Return the authenticated admin's identity."""
    return {"admin_email": subject}
