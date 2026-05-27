"""Analysis API routes."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import AnalyzeRequest, ApiResponse
from src.utils.http_client import HttpClient
from src.analyzers import (
    MetaAnalyzer, HeadingAnalyzer, LinkAnalyzer,
    ImageAnalyzer, PerformanceAnalyzer, ContentAnalyzer,
)

router = APIRouter()


@router.post("/analyze", response_model=ApiResponse)
async def analyze_page(request: AnalyzeRequest):
    """Perform full SEO analysis on a URL."""
    async with HttpClient() as client:
        html = await client.fetch_page(request.url)

    if not html:
        raise HTTPException(status_code=400, detail="Could not fetch URL")

    url = request.url
    results = {
        "meta": MetaAnalyzer().analyze(html, url).to_dict(),
        "headings": HeadingAnalyzer().analyze(html, url).to_dict(),
        "links": LinkAnalyzer().analyze(html, url).to_dict(),
        "images": ImageAnalyzer().analyze(html, url).to_dict(),
        "performance": PerformanceAnalyzer().analyze(html, url).to_dict(),
        "content": ContentAnalyzer().analyze(html, url, request.target_keyword).to_dict(),
    }

    # Calculate overall score
    scores = [v.get("score", 0) for v in results.values()]
    overall_score = round(sum(scores) / len(scores), 1)

    return ApiResponse(
        success=True,
        data={"url": url, "overall_score": overall_score, "analysis": results},
    )


@router.post("/analyze/meta", response_model=ApiResponse)
async def analyze_meta(request: AnalyzeRequest):
    """Analyze meta tags only."""
    async with HttpClient() as client:
        html = await client.fetch_page(request.url)
    if not html:
        raise HTTPException(status_code=400, detail="Could not fetch URL")

    result = MetaAnalyzer().analyze(html, request.url)
    return ApiResponse(success=True, data=result.to_dict())


@router.post("/analyze/content", response_model=ApiResponse)
async def analyze_content(request: AnalyzeRequest):
    """Analyze content quality only."""
    async with HttpClient() as client:
        html = await client.fetch_page(request.url)
    if not html:
        raise HTTPException(status_code=400, detail="Could not fetch URL")

    result = ContentAnalyzer().analyze(html, request.url, request.target_keyword)
    return ApiResponse(success=True, data=result.to_dict())
