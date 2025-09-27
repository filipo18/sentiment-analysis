"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import discovery, ingestion, comments, health, analysis
import logging
import time
import sys
import asyncio

# Get settings
settings = get_settings()

# On Windows, use SelectorEventLoop to avoid aiohttp/asyncpraw timeout issues
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("[API] WindowsSelectorEventLoopPolicy set")
    except Exception as _e:
        print(f"[API] Failed to set WindowsSelectorEventLoopPolicy: {_e}")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="A FastAPI application for discovering and ingesting social media content for product analysis"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic logger configuration (works with uvicorn too)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Log every request (also print to ensure visibility in simple runners)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    client = request.client.host if request.client else "-"
    logger.info(f"{client} {request.method} {request.url.path} -> {response.status_code} {duration_ms:.1f}ms")
    print(f"[API] {client} {request.method} {request.url.path} -> {response.status_code} {duration_ms:.1f}ms")
    return response

# Include routers
app.include_router(health.router)
app.include_router(discovery.router)
app.include_router(ingestion.router)
app.include_router(comments.router)
app.include_router(analysis.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
