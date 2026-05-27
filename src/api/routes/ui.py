"""Web UI routes serving Jinja2 templates."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

templates_dir = Path(__file__).parent.parent.parent / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse(request, "dashboard.html")


@router.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    """SEO analysis page."""
    return templates.TemplateResponse(request, "analyze.html")


@router.get("/crawl", response_class=HTMLResponse)
async def crawl_page(request: Request):
    """Site crawl page."""
    return templates.TemplateResponse(request, "crawl.html")


@router.get("/competitors", response_class=HTMLResponse)
async def competitors_page(request: Request):
    """Competitor analysis page."""
    return templates.TemplateResponse(request, "competitors.html")


@router.get("/rank-tracker", response_class=HTMLResponse)
async def rank_tracker_page(request: Request):
    """Rank tracking page."""
    return templates.TemplateResponse(request, "rank_tracker.html")


@router.get("/tools", response_class=HTMLResponse)
async def tools_page(request: Request):
    """SEO tools (generators, checkers) page."""
    return templates.TemplateResponse(request, "tools.html")



@router.get("/ai-writer", response_class=HTMLResponse)
async def ai_writer_page(request: Request):
    """AI content writer page."""
    return templates.TemplateResponse(request, "ai_writer.html")
