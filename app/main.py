"""
AIVision OCR API - FastAPI Application
Multi-LLM document extraction service with template-based field extraction.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.db.session import init_db
from app.api.v1 import extractions, templates, countries, analytics, accounts

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting AIVision OCR API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database
    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")

    # Check API keys
    api_keys = {
        "Gemini": bool(settings.GOOGLE_API_KEY),
        "OpenAI": bool(settings.OPENAI_API_KEY),
        "Anthropic": bool(settings.ANTHROPIC_API_KEY)
    }
    logger.info(f"API Keys configured: {api_keys}")

    yield

    # Shutdown
    logger.info("Shutting down AIVision OCR API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    AIVision OCR API - Enterprise-grade document extraction service

    Features:
    - Multi-LLM support (Gemini, OpenAI, Claude)
    - Template-based extraction with country-specific templates
    - Auto document classification and tagging
    - Bank statement transaction extraction
    - Field validation and quality scoring
    - Multi-tenant with account-specific templates

    Authentication:
    - Use Bearer token: `Authorization: Bearer aiv_your_token_here`
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AIVision OCR API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_PREFIX}/accounts",
    tags=["Accounts"]
)

app.include_router(
    extractions.router,
    prefix=f"{settings.API_V1_PREFIX}/extractions",
    tags=["Extractions"]
)

app.include_router(
    templates.router,
    prefix=f"{settings.API_V1_PREFIX}/templates",
    tags=["Templates"]
)

app.include_router(
    countries.router,
    prefix=f"{settings.API_V1_PREFIX}/countries",
    tags=["Countries"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_PREFIX}/analytics",
    tags=["Analytics"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
