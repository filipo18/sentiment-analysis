"""Health check API endpoints."""
from fastapi import APIRouter
from app.models import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok")
