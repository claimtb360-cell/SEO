"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.utils.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="All-in-One SEO Analysis Tool API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Register API routes
    from .routes import analyze, crawl, check, competitors, rank, generators, ai_content
    app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
    app.include_router(crawl.router, prefix="/api/v1", tags=["Crawling"])
    app.include_router(check.router, prefix="/api/v1", tags=["Health Checks"])
    app.include_router(competitors.router, prefix="/api/v1", tags=["Competitors"])
    app.include_router(rank.router, prefix="/api/v1", tags=["Rank Tracking"])
    app.include_router(generators.router, prefix="/api/v1", tags=["Generators"])
    app.include_router(ai_content.router, prefix="/api/v1", tags=["AI Content"])

    # Register web UI routes
    from .routes import ui
    app.include_router(ui.router)

    # Static files
    static_dir = Path(__file__).parent.parent.parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app
