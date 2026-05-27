"""Health check API routes."""

from fastapi import APIRouter

from src.api.schemas import (
    BrokenLinkRequest, RedirectCheckRequest,
    CanonicalCheckRequest, MobileCheckRequest, ApiResponse,
)
from src.checkers import (
    BrokenLinkChecker, RedirectChecker,
    CanonicalChecker, MobileFriendlyChecker,
)

router = APIRouter()


@router.post("/check/broken-links", response_model=ApiResponse)
async def check_broken_links(request: BrokenLinkRequest):
    """Check for broken links on a page."""
    checker = BrokenLinkChecker()
    result = await checker.check_page(request.url)
    return ApiResponse(success=True, data=result.to_dict())


@router.post("/check/redirects", response_model=ApiResponse)
async def check_redirects(request: RedirectCheckRequest):
    """Check URLs for redirect chains."""
    checker = RedirectChecker()
    result = await checker.check_urls(request.urls)
    return ApiResponse(success=True, data=result.to_dict())


@router.post("/check/canonical", response_model=ApiResponse)
async def check_canonical(request: CanonicalCheckRequest):
    """Check canonical tag implementation."""
    checker = CanonicalChecker()
    result = await checker.check_pages(request.urls)
    return ApiResponse(success=True, data=result.to_dict())


@router.post("/check/mobile", response_model=ApiResponse)
async def check_mobile(request: MobileCheckRequest):
    """Check mobile-friendliness."""
    checker = MobileFriendlyChecker()
    result = await checker.check(request.url)
    return ApiResponse(success=True, data=result.to_dict())
