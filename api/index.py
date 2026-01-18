"""
Vercel Serverless Function Entry Point for AIVision API

This module serves as the entry point for deploying AIVision's FastAPI
backend as a Vercel serverless function using Mangum as the ASGI adapter.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment defaults for serverless deployment
os.environ.setdefault("ENVIRONMENT", "production")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

# Try to import the main app, with fallback for missing dependencies
try:
    from app.main import app as fastapi_app
except ImportError as e:
    # Create a minimal app if main app can't be imported
    fastapi_app = FastAPI(
        title="AIVision API",
        description="Document OCR Extraction Service",
        version="1.0.0"
    )

    @fastapi_app.get("/health")
    async def health_check():
        return {"status": "healthy", "message": "AIVision API is running"}

    @fastapi_app.get("/api/v1/health")
    async def api_health_check():
        return {"status": "healthy", "version": "1.0.0"}

    # Add CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    import_error = str(e)

    @fastapi_app.get("/")
    async def root():
        return {
            "message": "AIVision API - Limited Mode",
            "note": f"Full app not available: {import_error}",
            "docs": "/docs"
        }

# Create the Mangum handler for AWS Lambda / Vercel
handler = Mangum(fastapi_app, lifespan="off")


# Vercel expects a function that handles the request
def handler_function(request, context=None):
    """
    Main handler function for Vercel serverless deployment.

    Args:
        request: The incoming HTTP request
        context: Optional context object (for Lambda compatibility)

    Returns:
        The response from the FastAPI application
    """
    return handler(request, context)


# Export for Vercel
app = handler
