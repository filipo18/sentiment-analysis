"""Q&A API endpoints using Weaviate (non-breaking)."""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from app.database import db_service
from app.services.weaviate_service import weaviate_service
import logging


router = APIRouter(prefix="/qa", tags=["question-answering"])
logger = logging.getLogger("app.qa_router")


class QuestionRequest(BaseModel):
    question: str
    limit: Optional[int] = 5


class QuestionResponse(BaseModel):
    answer: str
    relevant_comments: list
    sources: int


class SyncResponse(BaseModel):
    status: str
    synced_count: int
    total_count: int


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    try:
        result = weaviate_service.answer_question(
            question=request.question, limit=request.limit or 5
        )
        return QuestionResponse(**result)
    except Exception as e:  # pragma: no cover - robust API
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(status_code=500, detail="Failed to answer question")


@router.get("/search")
async def search_comments(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Number of results to return"),
    brand_name: Optional[str] = Query(None, description="Filter by brand name"),
    product_name: Optional[str] = Query(None, description="Filter by product name"),
) -> Dict[str, Any]:
    try:
        where_filter = None
        if brand_name or product_name:
            operands = []
            if brand_name:
                operands.append({
                    "path": ["brand_name"],
                    "operator": "Equal",
                    "valueString": brand_name,
                })
            if product_name:
                operands.append({
                    "path": ["product_name"],
                    "operator": "Equal",
                    "valueString": product_name,
                })
            where_filter = operands[0] if len(operands) == 1 else {"operator": "And", "operands": operands}

        items = weaviate_service.search_comments(query=query, limit=limit, where_filter=where_filter)
        return {"query": query, "comments": items, "count": len(items)}
    except Exception as e:  # pragma: no cover
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/sync", response_model=SyncResponse)
async def sync_comments_to_weaviate(
    limit: int = Query(1000, description="Number of comments to sync"),
) -> SyncResponse:
    try:
        result = db_service.get_recent_comments(limit=limit)
        comments = result.get("comments", [])
        if not comments:
            return SyncResponse(status="no_data", synced_count=0, total_count=0)

        synced = weaviate_service.add_comments_batch(comments)
        return SyncResponse(status="success", synced_count=synced, total_count=len(comments))
    except Exception as e:  # pragma: no cover
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail="Sync failed")


@router.get("/stats")
async def get_weaviate_stats() -> Dict[str, Any]:
    try:
        return weaviate_service.get_stats()
    except Exception as e:  # pragma: no cover
        logger.error(f"Stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")


