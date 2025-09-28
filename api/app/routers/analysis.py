"""Analysis API endpoints."""
from typing import Dict, Optional
from fastapi import APIRouter, Query

from app.services.analysis_service import analysis_service
from app.database import db_service
from app.config import get_settings

router = APIRouter(prefix="/analyse-sentiment", tags=["analysis"])


@router.post("")
async def analyse_sentiment(limit: Optional[int] = Query(default=None, ge=1, le=500)) -> Dict[str, int]:
    """Run analysis over unanalyzed comments and update rows.

    Query param 'limit' controls how many unanalyzed rows to scan.
    Only processes comments that haven't been analyzed yet.
    """
    settings = get_settings()
    effective_limit = int(limit or settings.ANALYSIS_LIMIT)
    summary = await analysis_service.analyze_recent_comments(limit=effective_limit)
    return {  # type: ignore[return-value]
        "updated": int(summary.get("updated", 0)),
        "skipped": int(summary.get("skipped", 0)),
        "total_scanned": int(summary.get("total_scanned", 0)),
    }


@router.get("/progress")
async def get_analysis_progress() -> Dict[str, int]:
    """Get real-time progress of comment analysis."""
    stats = db_service.get_comment_analysis_stats()
    return stats


