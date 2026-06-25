"""
CommerceMind VoiceCare AI — FastAPI Application Entry Point
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import VoiceCareError, RateLimitError, AuthError

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.api.voice import router as voice_router
from app.api.tickets import router as tickets_router
from app.api.auth import router as auth_router

settings = get_settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


from app.services.chroma_service import get_chroma_service
from data.policies.policy_documents import get_all_policies

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("starting_app", environment=settings.environment)
    await init_db()
    logger.info("database_initialized")
    
    # Auto-seed ChromaDB if empty
    try:
        chroma = get_chroma_service()
        if chroma.get_collection_count() == 0:
            logger.info("seeding_chromadb_policies")
            policies = get_all_policies()
            chroma.ingest_policies(policies)
    except Exception as e:
        logger.error("chromadb_seeding_failed", error=str(e))
        
    yield
    await close_db()
    logger.info("app_shutdown")


app = FastAPI(
    title="CommerceMind VoiceCare AI",
    description="Voice-first multilingual e-commerce customer support",
    version="1.0.0",
    lifespan=lifespan,
)

# ----------------------------------------------------------------
# Global exception handlers — standardised JSON error shape
# ----------------------------------------------------------------

@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": exc.code, "detail": exc.message},
        headers={"Retry-After": str(exc.retry_after_seconds)},
    )


@app.exception_handler(VoiceCareError)
async def voicecare_error_handler(request: Request, exc: VoiceCareError) -> JSONResponse:
    logger.error("voicecare_error", code=exc.code, detail=exc.message)
    return JSONResponse(
        status_code=500,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "detail": "An unexpected error occurred."},
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(voice_router)
app.include_router(tickets_router)


@app.get("/health")
async def health_check():
    """Health check — verifies DB and Chroma are reachable."""
    from sqlalchemy import text
    from app.core.database import async_session
    from app.services.chroma_service import get_chroma_service

    checks: dict[str, str] = {}

    # Database
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Chroma (in-process, just confirm collection is accessible)
    try:
        count = get_chroma_service().get_collection_count()
        checks["chroma"] = f"ok ({count} policies)"
    except Exception as exc:
        checks["chroma"] = f"error: {exc}"

    overall = "healthy" if all(v == "ok" or v.startswith("ok") for v in checks.values()) else "degraded"
    return {
        "status": overall,
        "app": settings.app_name,
        "environment": settings.environment,
        "checks": checks,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "CommerceMind VoiceCare AI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
