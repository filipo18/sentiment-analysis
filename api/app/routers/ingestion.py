"""Ingestion API endpoints."""
from typing import Any, Dict, List
from fastapi import APIRouter, Request
from app.models import IngestResponse
import logging
from app.services.ingestion_service import IngestionService
from app.config import get_settings

router = APIRouter(prefix="/ingest", tags=["ingestion"])

# Initialize service
ingestion_service = IngestionService()
settings = get_settings()
logger = logging.getLogger("app.ingestion")

@router.post("", response_model=IngestResponse)
async def ingest_sources(request: Request) -> IngestResponse:
    """Ingest content from discovered sources.

    Accepts optional JSON body: { "products": ["..."] }.
    If body is omitted, invalid, or empty, defaults to settings.DEFAULT_PRODUCTS.
    """
    client_ip = request.client.host if request.client else "-"
    logger.info(f"/ingest called from {client_ip}")
    print(f"[API] /ingest called from {client_ip}")
    products: List[str] = settings.DEFAULT_PRODUCTS
    try:
        # Attempt to parse JSON body; handle empty body gracefully
        data = await request.json()
        if isinstance(data, dict):
            maybe = data.get("products")
            if isinstance(maybe, list):
                products = [str(p).strip() for p in maybe if str(p).strip()]
                if not products:
                    products = settings.DEFAULT_PRODUCTS
    except Exception:
        # No/invalid JSON body; keep defaults
        pass
    
    logger.info(f"/ingest resolved products: {products}")
    print(f"[API] /ingest resolved products: {products}")
    logger.info("/ingest starting ingestion run_once")
    print("[API] /ingest starting ingestion run_once")
    # Run ingestion
    await ingestion_service.run_once(products)
    logger.info("/ingest completed ingestion run_once")
    print("[API] /ingest completed ingestion run_once")
    
    return IngestResponse(status="completed", products=products)

@router.post("/start", response_model=IngestResponse)
async def ingest_sources_start(request: Request) -> IngestResponse:
    """Compatibility endpoint for ingestion.

    Accepts either {"products": [...]} or {"sources": [...]} and defaults otherwise.
    """
    client_ip = request.client.host if request.client else "-"
    logger.info(f"/ingest/start called from {client_ip}")
    products: List[str] = settings.DEFAULT_PRODUCTS
    try:
        data = await request.json()
        if isinstance(data, dict):
            # Support both keys
            maybe = data.get("products") or data.get("sources")
            if isinstance(maybe, list):
                products = [str(p).strip() for p in maybe if str(p).strip()]
                if not products:
                    products = settings.DEFAULT_PRODUCTS
    except Exception:
        pass

    await ingestion_service.run_once(products)
    logger.info("/ingest/start completed ingestion run_once")
    return IngestResponse(status="completed", products=products)
