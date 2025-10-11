"""Discovery API endpoints."""
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from app.models import ProductInput, DiscoverResponse
from app.services.discovery_service import ChannelDiscoveryService
from app.database import db_service

router = APIRouter(prefix="/discover", tags=["discovery"])

# Initialize service
discovery_service = ChannelDiscoveryService()

@router.post("", response_model=Dict[str, List[DiscoverResponse]])
async def discover_products(payload: ProductInput) -> Dict[str, List[DiscoverResponse]]:
    """Discover relevant channels for the given products."""
    if not payload.products:
        raise HTTPException(status_code=400, detail="At least one product required")
    
    # Clean up products list
    products: List[str] = [p.strip() for p in payload.products if p.strip()]
    if not products:
        raise HTTPException(status_code=400, detail="At least one product required")
    
    # Discover channels
    discovery: Dict[str, List[Dict[str, Any]]] = await discovery_service.discover(products)

    # Persist Reddit results into source_channel by replacing existing rows
    reddit_results = discovery.get("reddit", [])
    if reddit_results:
        summary = db_service.replace_source_channels("reddit", reddit_results)
        # Optional: you can log or attach summary if needed
    
    # Convert to response format
    return {
        platform: [DiscoverResponse(**item) for item in items]
        for platform, items in discovery.items()
    }
