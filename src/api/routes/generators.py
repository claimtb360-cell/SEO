"""Generator API routes."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.api.schemas import SitemapGenerateRequest, RobotsGenerateRequest, ApiResponse
from src.generators import SitemapGenerator, RobotsGenerator
from src.crawlers import SiteCrawler

router = APIRouter()


@router.post("/generate/sitemap", response_model=ApiResponse)
async def generate_sitemap(request: SitemapGenerateRequest):
    """Generate sitemap.xml by crawling the site."""
    crawler = SiteCrawler(max_pages=request.max_pages, max_depth=3)
    crawl_result = await crawler.crawl(request.url)

    generator = SitemapGenerator()
    pages = [p for p in crawl_result.to_dict()["pages"] if p["status_code"] == 200]
    result = generator.generate_from_crawl(pages)

    return ApiResponse(
        success=True,
        data={
            "total_urls": result.total_urls,
            "xml_content": result.xml_content,
        },
    )


@router.post("/generate/robots", response_model=ApiResponse)
async def generate_robots(request: RobotsGenerateRequest):
    """Generate robots.txt content."""
    generator = RobotsGenerator()

    if request.mode == "permissive":
        result = generator.generate_permissive(sitemap_url=request.sitemap_url)
    elif request.mode == "restrictive":
        result = generator.generate_restrictive(sitemap_url=request.sitemap_url)
    else:
        result = generator.generate(
            sitemap_url=request.sitemap_url,
            crawl_delay=request.crawl_delay,
        )

    return ApiResponse(
        success=True,
        data={"content": result.content},
    )
