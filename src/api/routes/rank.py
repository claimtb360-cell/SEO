"""Rank tracking API routes."""

from fastapi import APIRouter

from src.api.schemas import RankCheckRequest, ApiResponse
from src.rank_tracker import RankTracker

router = APIRouter()


@router.post("/rank/check", response_model=ApiResponse)
async def check_rankings(request: RankCheckRequest):
    """Check keyword rankings for a domain."""
    tracker = RankTracker()
    report = await tracker.check_keywords(request.keywords, request.domain)
    return ApiResponse(success=True, data=report.to_dict())


@router.get("/rank/history/{domain}", response_model=ApiResponse)
async def get_rank_history(domain: str):
    """Get ranking history for all tracked keywords."""
    tracker = RankTracker()
    histories = tracker.get_all_tracked(domain)
    return ApiResponse(
        success=True,
        data={
            "domain": domain,
            "keywords": [h.to_dict() for h in histories],
            "total_tracked": len(histories),
        },
    )


@router.get("/rank/keyword/{domain}/{keyword}", response_model=ApiResponse)
async def get_keyword_history(domain: str, keyword: str):
    """Get ranking history for a specific keyword."""
    tracker = RankTracker()
    history = tracker.get_history(keyword, domain)
    return ApiResponse(success=True, data=history.to_dict())
