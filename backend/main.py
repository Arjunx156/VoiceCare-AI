"""
CommerceMind VoiceCare AI — FastAPI Application Entry Point
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.api.voice import router as voice_router
from app.api.tickets import router as tickets_router

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
app.include_router(voice_router)
app.include_router(tickets_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
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
