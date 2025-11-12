"""Main FastAPI application."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.routes import router as v1_router
from .core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ai_image_analyzer")

settings = get_settings()
try:
    settings.validate()
except RuntimeError as exc:
    logger.error("Configuration validation failed: %s", exc)
    raise

app = FastAPI(
    title="AI Image Analyzer API",
    version="1.0.0",
    description="Backend API for AI-powered image gallery with authentication",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "AI Image Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
