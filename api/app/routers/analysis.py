"""Analysis API endpoints."""
from typing import Dict, Optional
from fastapi import APIRouter, Query

from app.services.analysis_service import analysis_service
from app.config import get_settings

router = APIRouter(prefix="/analyse-sentiment", tags=["analysis"])


@router.post("")
async def analyse_sentiment(limit: Optional[int] = Query(default=None, ge=1, le=500)) -> Dict[str, int]:
    """Run analysis over recent comments and update rows.

    Query param 'limit' controls how many recent rows to scan.
    """
    settings = get_settings()
    effective_limit = int(limit or settings.ANALYSIS_LIMIT)
    summary = analysis_service.analyze_recent_comments(limit=effective_limit)
    return {  # type: ignore[return-value]
        "updated": int(summary.get("updated", 0)),
        "skipped": int(summary.get("skipped", 0)),
        "total_scanned": int(summary.get("total_scanned", 0)),
    }


