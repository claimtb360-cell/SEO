"""Crawling API routes."""

from fastapi import APIRouter

from src.api.schemas import CrawlRequest, ApiResponse
from src.crawlers import SiteCrawler, SitemapParser

router = APIRouter()


@router.post("/crawl", response_model=ApiResponse)
async def crawl_site(request: CrawlRequest):
    """Crawl a website and return page data."""
    crawler = SiteCrawler(
        max_pages=request.max_pages,
        max_depth=request.max_depth,
    )
    result = await crawler.crawl(request.url)
    return ApiResponse(success=True, data=result.to_dict())


@router.post("/crawl/sitemap", response_model=ApiResponse)
async def parse_sitemap(request: CrawlRequest):
    """Parse a site's sitemap.xml."""
    parser = SitemapParser()
    sitemap_url = SitemapParser.get_sitemap_url(request.url)
    result = await parser.parse_recursive(sitemap_url)
    return ApiResponse(success=True, data=result.to_dict())
