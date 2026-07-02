"""
CommerceMind VoiceCare AI — Authentication Routes & JWT Utilities
Provides admin login and a reusable FastAPI dependency for protected routes.
"""

import secrets as _secrets
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

import bcrypt
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_JWT_SECRET,
    DEV_LIKE_ENVIRONMENTS,
    get_settings,
)
from app.core.errors import ErrorMessages
from app.core.rate_limit import enforce as enforce_rate_limit, get_client_ip
from app.services.memory_service import get_memory_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

_bearer = HTTPBearer(auto_error=False)

_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 8
_LOGIN_WINDOW_SECONDS = 15 * 60


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

@lru_cache(maxsize=4)
def _bcrypt_hash_for(stored: str) -> bytes:
    """Return a bcrypt hash for the configured admin password.

    Pre-hashed values (``$2…``) pass through; a plaintext value is hashed once
    and cached so every login attempt runs the same constant-time bcrypt
    verify regardless of whether email or password matched. bcrypt only reads
    the first 72 bytes, so longer inputs are truncated explicitly.
    """
    if stored.startswith("$2"):
        return stored.encode()
    return bcrypt.hashpw(stored.encode()[:72], bcrypt.gensalt())


def _default_credentials_blocked() -> bool:
    """True when default secrets are configured outside a dev-like environment.

    This is the runtime backstop for deploys that never set ENVIRONMENT (which
    defaults to "development" and therefore skips the startup validators).
    """
    if str(settings.environment).lower() in DEV_LIKE_ENVIRONMENTS:
        return False
    return (
        settings.nextauth_secret == DEFAULT_JWT_SECRET
        or settings.admin_password == DEFAULT_ADMIN_PASSWORD
    )


def _create_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            # Unique token id — lets logout revoke this token server-side.
            "jti": uuid.uuid4().hex,
        },
        settings.nextauth_secret,
        algorithm=_ALGORITHM,
    )


def _decode_claims(token: str) -> Optional[dict]:
    """Return all verified claims, or None if the token is invalid/expired."""
    try:
        return jwt.decode(token, settings.nextauth_secret, algorithms=[_ALGORITHM])
    except JWTError:
        return None


def _verify_token(token: str) -> Optional[str]:
    """Return the subject claim, or None if token is invalid/expired."""
    claims = _decode_claims(token)
    return claims.get("sub") if claims else None


def _revocation_key(jti: str) -> str:
    return f"revoked_jti:{jti}"


async def _is_revoked(claims: dict) -> bool:
    """True when the token's jti is on the logout denylist.

    Tokens minted before jti existed carry no jti and cannot be individually
    revoked — they simply age out at their 8h expiry.
    """
    jti = claims.get("jti")
    if not jti:
        return False
    memory = await get_memory_service()
    return await memory.get_cache(_revocation_key(jti)) is not None


# ----------------------------------------------------------------
# Dependency: require a valid admin JWT
# ----------------------------------------------------------------

async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
) -> str:
    """FastAPI dependency — raises 401 if the bearer token is missing, invalid,
    or has been revoked by logout."""
    if not credentials:
        raise HTTPException(status_code=401, detail=ErrorMessages.INVALID_CREDENTIALS)
    claims = _decode_claims(credentials.credentials)
    subject = claims.get("sub") if claims else None
    if not claims or not subject:
        raise HTTPException(status_code=401, detail="Token invalid or expired.")
    if await _is_revoked(claims):
        # Same message as an expired token — no oracle for revocation state.
        raise HTTPException(status_code=401, detail="Token invalid or expired.")
    return subject


# ----------------------------------------------------------------
# Routes
# ----------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def admin_login(body: LoginRequest, request: Request):
    """Authenticate with admin credentials; returns a JWT bearer token."""
    if _default_credentials_blocked():
        logger.error(
            "admin_login_blocked_default_credentials",
            environment=str(settings.environment),
        )
        raise HTTPException(
            status_code=403,
            detail=(
                "Admin login is disabled: default credentials are configured. "
                "Set ADMIN_PASSWORD and NEXTAUTH_SECRET for this deployment."
            ),
        )

    limits = get_settings()
    await enforce_rate_limit(
        key=f"rate_limit:login:{get_client_ip(request)}",
        limit=limits.login_rate_limit_per_15min,
        window_seconds=_LOGIN_WINDOW_SECONDS,
        detail="Too many login attempts. Try again later.",
    )

    # Both comparisons always run (no short-circuit) and are constant-time:
    # compare_digest for the email, bcrypt verify for the password.
    email_match = _secrets.compare_digest(
        body.email.lower().strip().encode(),
        settings.admin_email.lower().strip().encode(),
    )
    password_match = bcrypt.checkpw(
        body.password.encode()[:72], _bcrypt_hash_for(settings.admin_password)
    )

    if not (email_match and password_match):
        logger.warning("admin_login_failed", client_ip=get_client_ip(request))
        raise HTTPException(status_code=401, detail=ErrorMessages.INVALID_CREDENTIALS)

    token = _create_token(subject=body.email)
    logger.info("admin_login_success")
    return TokenResponse(access_token=token)


@router.post("/logout")
async def admin_logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
):
    """Revoke the presented token server-side (jti denylist until its expiry).

    Idempotent: revoking an already-revoked token succeeds. Legacy tokens
    without a jti can't be individually revoked; they age out at expiry.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail=ErrorMessages.INVALID_CREDENTIALS)
    claims = _decode_claims(credentials.credentials)
    if not claims or not claims.get("sub"):
        raise HTTPException(status_code=401, detail="Token invalid or expired.")

    jti = claims.get("jti")
    if jti:
        # Denylist only needs to outlive the token itself.
        now = datetime.now(timezone.utc).timestamp()
        ttl = max(int(claims.get("exp", now) - now), 60)
        memory = await get_memory_service()
        await memory.set_cache(_revocation_key(jti), {"revoked": True}, ttl_seconds=ttl)
        logger.info("admin_logout", jti=jti[:8])
    else:
        logger.warning("admin_logout_legacy_token_no_jti")

    return {"detail": "Logged out."}


@router.get("/me")
async def whoami(subject: str = Depends(require_admin)):
    """Return the authenticated admin's identity."""
    return {"admin_email": subject}
