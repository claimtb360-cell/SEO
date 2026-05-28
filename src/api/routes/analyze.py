"""Analysis API routes."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse

from src.api.schemas import AnalyzeRequest, ApiResponse, SERPCheckRequest
from src.utils.http_client import HttpClient
from src.analyzers import (
    MetaAnalyzer, HeadingAnalyzer, LinkAnalyzer,
    ImageAnalyzer, PerformanceAnalyzer, ContentAnalyzer,
)
from src.analyzers.seo_geo_analyzer import SEOGEOAnalyzer
from src.analyzers.geo_checker import GEOChecker
from src.generators.export_manager import ExportManager
from src.rank_tracker.serp_checker import SERPChecker, SearchEngine

router = APIRouter()

# Store last analysis for export
_last_analysis: dict = {}


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



@router.post("/analyze/full", response_model=ApiResponse)
async def analyze_full(request: AnalyzeRequest):
    """Run comprehensive 80-factor SEO & GEO analysis."""
    global _last_analysis

    async with HttpClient() as client:
        html = await client.fetch_page(request.url)

    if not html:
        raise HTTPException(status_code=400, detail="Could not fetch URL")

    analyzer = SEOGEOAnalyzer()
    result = analyzer.analyze(html, request.url, request.target_keyword)
    data = result.to_dict()
    _last_analysis = data

    return ApiResponse(success=True, data=data)


@router.post("/analyze/geo", response_model=ApiResponse)
async def analyze_geo(request: AnalyzeRequest):
    """Run GEO (Generative Engine Optimization) signals check only."""
    async with HttpClient() as client:
        html = await client.fetch_page(request.url)

    if not html:
        raise HTTPException(status_code=400, detail="Could not fetch URL")

    checker = GEOChecker()
    result = checker.check(html, request.url, request.target_keyword)
    data = result.to_dict()

    return ApiResponse(success=True, data=data)


@router.post("/analyze/technical", response_model=ApiResponse)
async def analyze_technical(request: AnalyzeRequest):
    """Run Technical SEO analysis only."""
    async with HttpClient() as client:
        html = await client.fetch_page(request.url)

    if not html:
        raise HTTPException(status_code=400, detail="Could not fetch URL")

    analyzer = SEOGEOAnalyzer()
    result = analyzer.analyze(html, request.url, request.target_keyword)

    # Return only technical categories
    technical_cats = {}
    for key in ["technical_seo", "core_web_vitals", "schema_structured_data"]:
        if key in result.categories:
            technical_cats[key] = result.categories[key].to_dict()

    tech_scores = [c.score for c in result.categories.values()
                   if c.name in ["Technical SEO", "Core Web Vitals", "Schema & Structured Data"]]
    overall = round(sum(tech_scores) / max(len(tech_scores), 1), 1)

    return ApiResponse(success=True, data={
        "url": request.url,
        "overall_score": overall,
        "categories": technical_cats,
    })



@router.get("/analyze/export/{format}")
async def export_analysis(format: str):
    """Export last analysis as PDF, JSON, or CSV."""
    global _last_analysis

    if not _last_analysis:
        raise HTTPException(status_code=404, detail="No analysis data available. Run an analysis first.")

    export_mgr = ExportManager()

    if format.lower() == "json":
        content = export_mgr.export_json_string(_last_analysis)
        return PlainTextResponse(content=content, media_type="application/json",
                                 headers={"Content-Disposition": "attachment; filename=seo_report.json"})

    elif format.lower() == "csv":
        content = export_mgr.export_csv_string(_last_analysis, data_type="full")
        return PlainTextResponse(content=content, media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=seo_report.csv"})

    elif format.lower() == "pdf":
        content = export_mgr.export_pdf_string(_last_analysis)
        return HTMLResponse(content=content,
                           headers={"Content-Disposition": "attachment; filename=seo_report.html"})

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use json, csv, or pdf.")


@router.post("/rank/serp-check", response_model=ApiResponse)
async def serp_check(request: SERPCheckRequest):
    """Advanced SERP check with AI Overview detection."""
    checker = SERPChecker()

    engine = SearchEngine.GOOGLE
    if request.engine and request.engine.lower() == "bing":
        engine = SearchEngine.BING

    result = await checker.check_serp(
        keyword=request.keyword,
        engine=engine,
        num_results=request.num_results or 100,
        track_domain=request.track_domain,
    )

    return ApiResponse(success=True, data=result.to_dict())


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
