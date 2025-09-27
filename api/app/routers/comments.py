"""Comments API endpoints."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query
from app.models import CommentsResponse
from app.database import db_service

router = APIRouter(prefix="/comments", tags=["comments"])

@router.get("", response_model=CommentsResponse)
async def get_comments(
    product_name: Optional[str] = Query(None, description="Filter by product name"),
    limit: int = Query(100, description="Number of comments to return")
) -> CommentsResponse:
    """Get comments from the database."""
    result = db_service.get_comments(product_name=product_name, limit=limit)
    return CommentsResponse(**result)

@router.get("/brand/{brand_name}", response_model=CommentsResponse)
async def get_comments_by_brand(
    brand_name: str,
    limit: int = Query(100, description="Number of comments to return")
) -> CommentsResponse:
    """Get comments filtered by brand name."""
    result = db_service.get_comments_by_brand(brand_name=brand_name, limit=limit)
    return CommentsResponse(**result)

@router.get("/recent", response_model=CommentsResponse)
async def get_recent_comments(
    limit: int = Query(100, description="Number of comments to return")
) -> CommentsResponse:
    """Get the most recent comments."""
    result = db_service.get_recent_comments(limit=limit)
    return CommentsResponse(**result)
