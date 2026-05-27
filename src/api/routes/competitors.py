"""Competitor analysis API routes."""

from fastapi import APIRouter

from src.api.schemas import CompetitorRequest, ApiResponse
from src.competitors import CompetitorAnalyzer

router = APIRouter()


@router.post("/competitors/compare", response_model=ApiResponse)
async def compare_competitors(request: CompetitorRequest):
    """Compare your site against competitors."""
    analyzer = CompetitorAnalyzer()
    result = await analyzer.compare(request.my_url, request.competitor_urls)
    return ApiResponse(success=True, data=result.to_dict())


@router.post("/competitors/analyze", response_model=ApiResponse)
async def analyze_competitor(request: CompetitorRequest):
    """Analyze a single competitor site."""
    analyzer = CompetitorAnalyzer()
    profile = await analyzer.analyze_site(request.my_url)
    return ApiResponse(success=True, data=profile.to_dict())
