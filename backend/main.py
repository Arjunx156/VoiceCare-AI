"""
CommerceMind VoiceCare AI — FastAPI Application Entry Point
"""

import asyncio
import time
import statistics
import structlog
from collections import deque
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import VoiceCareError, RateLimitError, AuthError

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.http import close_http_client
from app.api.voice import router as voice_router
from app.api.tickets import router as tickets_router
from app.api.customers import router as customers_router
from app.api.auth import router as auth_router
from app.api.auth import require_admin

settings = get_settings()

# ---- Sentry (initialise before anything else so startup errors are caught) ----
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[
            StarletteIntegration(transaction_style="url"),
            FastApiIntegration(transaction_style="url"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.2,   # 20 % of requests recorded for perf tracing
        send_default_pii=False,   # GDPR-friendly — no IP / user data by default
    )

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

# Rolling window of the last 1 000 request durations (seconds)
_request_latencies: deque[float] = deque(maxlen=1000)


from app.services.chroma_service import get_chroma_service
from app.services.memory_service import get_memory_service
from data.policies.policy_documents import get_all_policies

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("starting_app", environment=settings.environment)
    if settings.has_default_secrets:
        logger.warning(
            "default_secrets_in_use",
            hint=(
                "NEXTAUTH_SECRET and/or ADMIN_PASSWORD are still the shipped defaults. "
                "Admin login is disabled outside development until they are replaced."
            ),
        )
    await init_db()
    logger.info("database_initialized")
    
    # Auto-seed ChromaDB if empty
    try:
        chroma = get_chroma_service()
        if chroma.get_collection_count() == 0:
            logger.info("seeding_chromadb_policies")
            policies = get_all_policies()
            chroma.ingest_policies(policies)
        # Force the ONNX embedding model to load now. Seeding only warms it when
        # the collection was empty; on a restart against an existing chroma_data
        # volume the first *query* pays a 1-3s model load — i.e. the first
        # customer of the day waits for it.
        await asyncio.to_thread(chroma.query_policies, "warmup", 1)
        logger.info("chroma_embedder_warm")
    except Exception as e:
        logger.error("chromadb_seeding_failed", error=str(e))

    # Pay the memory-backend handshake at boot. get_memory_service() pings
    # Upstash with a timeout on first call; without this that lands on the first
    # customer turn after a cold start.
    try:
        await get_memory_service()
        logger.info("memory_backend_warm")
    except Exception as e:
        logger.warning("memory_warmup_failed", error=str(e))

    yield

    # Let in-flight deferred stages (TTS + ticket writes) finish before the
    # engine is disposed — otherwise close_db() yanks the connection pool out
    # from under a ticket that is mid-write.
    from app.api.voice import _deferred_tasks
    if _deferred_tasks:
        logger.info("draining_deferred_tasks", count=len(_deferred_tasks))
        await asyncio.wait(list(_deferred_tasks), timeout=10)

    await close_http_client()
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


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects oversized request bodies before they are read into memory.

    Defense in depth alongside the Pydantic field limits — a huge body is
    refused from the declared Content-Length without buffering it.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.core.constants import MAX_BODY_BYTES

        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": "PAYLOAD_TOO_LARGE", "detail": "Request body too large."},
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Records per-request latency, logs it, and adds X-Response-Time header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        _request_latencies.append(duration)
        ms = round(duration * 1000, 1)
        response.headers["X-Response-Time"] = f"{ms}ms"
        logger.debug(
            "request_handled",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=ms,
        )
        return response


app.add_middleware(RequestTimingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

# CORS — production allows the explicit frontend URL(s) from FRONTEND_URL.
# The vercel.app wildcard is always on outside production, and can be opted
# into for production via CORS_ALLOW_VERCEL_PREVIEWS=true when the frontend
# lives on a Vercel URL that changes between deploys.
_cors_origins = settings.allowed_origins  # narrows to FRONTEND_URL list in production
_allow_vercel = (not settings.is_production) or settings.cors_allow_vercel_previews
_cors_origin_regex = r"https://.*\.vercel\.app" if _allow_vercel else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(voice_router)
app.include_router(tickets_router)
app.include_router(customers_router)


@app.get("/health")
async def health_check():
    """Health check — verifies DB and Chroma are reachable."""
    from sqlalchemy import text
    from app.core.database import async_session
    from app.services.chroma_service import get_chroma_service

    checks: dict[str, str] = {}

    # Database — log the real error, expose only a generic status publicly.
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.error("health_check_database_failed", error=str(exc))
        checks["database"] = "error"

    # Chroma (in-process, just confirm collection is accessible)
    try:
        count = get_chroma_service().get_collection_count()
        checks["chroma"] = f"ok ({count} policies)"
    except Exception as exc:
        logger.error("health_check_chroma_failed", error=str(exc))
        checks["chroma"] = "error"

    # Gemini — reported from the last real call rather than probed, so a health
    # ping never spends generation quota. A model withdrawn by Google 404s on
    # every call while still appearing in models.list(), and the pipeline
    # swallows that by design to keep answering the customer; without this the
    # only symptom is that every reply turns apologetic.
    try:
        from app.services.gemini_service import get_gemini_service

        llm = get_gemini_service().status()
        if not llm["configured"]:
            checks["gemini"] = "error (no api key)"
        elif llm["consecutive_failures"] >= 3:
            logger.error(
                "health_check_gemini_failing",
                model=llm["model"],
                failures=llm["consecutive_failures"],
                error=llm["last_error"],
            )
            checks["gemini"] = f"error ({llm['model']}: {llm['consecutive_failures']} failures)"
        elif llm["last_success_at"] is None:
            checks["gemini"] = f"ok ({llm['model']}, untested)"
        else:
            checks["gemini"] = f"ok ({llm['model']})"
    except Exception as exc:
        logger.error("health_check_gemini_failed", error=str(exc))
        checks["gemini"] = "error"

    overall = "healthy" if all(v == "ok" or v.startswith("ok") for v in checks.values()) else "degraded"
    return {
        "status": overall,
        "app": settings.app_name,
        "environment": settings.environment,
        "checks": checks,
    }


@app.get("/metrics")
async def get_metrics(admin_email: str = Depends(require_admin)):  # noqa: ARG001
    """Latency percentiles — admin-only, not exposed publicly."""
    sample = list(_request_latencies)
    if not sample:
        return {"request_count": 0, "note": "No requests recorded yet."}

    sample_ms = [round(v * 1000, 2) for v in sample]
    qs = statistics.quantiles(sample_ms, n=100)  # returns 99 cut-points

    return {
        "request_count": len(sample_ms),
        "latency_ms": {
            "min": round(min(sample_ms), 2),
            "p50": round(qs[49], 2),
            "p95": round(qs[94], 2),
            "p99": round(qs[98], 2),
            "max": round(max(sample_ms), 2),
            "mean": round(statistics.mean(sample_ms), 2),
        },
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "CommerceMind VoiceCare AI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }
