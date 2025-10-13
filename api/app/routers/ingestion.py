"""Ingestion API endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException
from app.models import IngestRequest, IngestResponse
import logging
from app.services.ingestion_service import IngestionService
from app.config import get_settings

router = APIRouter(prefix="/ingest", tags=["ingestion"])

# Initialize service
ingestion_service = IngestionService()
settings = get_settings()
logger = logging.getLogger("app.ingestion")

def normalize_subreddit_name(name: str) -> str:
    """Strip 'r/' prefix from subreddit name if present."""
    name = name.strip()
    if name.lower().startswith("r/"):
        return name[2:]
    return name

@router.post("", response_model=IngestResponse)
async def ingest_sources(request: IngestRequest) -> IngestResponse:
    """Ingest content from discovered sources."""
    logger.info("/ingest called")
    
    # Use provided products or default
    if not request.products or not any(p.strip() for p in request.products):
        raise HTTPException(status_code=400, detail="No products provided for ingestion.")
    products = [p.strip() for p in request.products if p.strip()]
    
    # Validate subreddits are provided
    if not request.subreddits or not any(s.strip() for s in request.subreddits):
        raise HTTPException(status_code=400, detail="No subreddits provided for ingestion.")
    
    # Normalize subreddit names (strip r/ prefix)
    subreddits = [normalize_subreddit_name(s) for s in request.subreddits if s.strip()]
    
    logger.info(f"Products: {products}, Subreddits: {subreddits}")
    
    # Run ingestion
    counts = await ingestion_service.run_once(products, subreddits=subreddits)
    logger.info("Ingestion completed")
    
    return IngestResponse(
        status="completed", 
        products=products, 
        subreddits=subreddits,
        comments_ingested=counts.get("ingested", 0),
        comments_failed=counts.get("failed", 0)
    )