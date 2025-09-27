"""Pydantic models for request/response schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ProductInput(BaseModel):
    """Input model for product discovery and ingestion."""
    products: List[str]

class DiscoverResponse(BaseModel):
    """Response model for channel discovery."""
    platform: str
    channel_id: str
    name: str
    score: float
    metrics: Dict[str, Any]

class IngestRequest(BaseModel):
    """Request model for content ingestion."""
    products: Optional[List[str]] = None
    subreddits: Optional[List[str]] = None

class CommentData(BaseModel):
    """Model for comment data to be stored in database."""
    brand_name: str
    product_name: Optional[str] = None
    comment: Optional[str] = None
    comment_sentiment: str = "neutral"
    comment_timestamp: Optional[str] = None
    thread_name: Optional[str] = None
    upvotes: Optional[int] = None
    attribute_discussed: Optional[str] = None
    attribute_sentiment: Optional[str] = None

class CommentsResponse(BaseModel):
    """Response model for comments retrieval."""
    comments: List[Dict[str, Any]]
    count: int

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str

class IngestResponse(BaseModel):
    """Response model for ingestion."""
    status: str
    products: List[str]
    subreddits: Optional[List[str]] = None
