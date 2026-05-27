"""Pydantic schemas for API request/response validation."""

from typing import List, Optional
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    url: str
    target_keyword: Optional[str] = None


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 50
    max_depth: int = 3


class BrokenLinkRequest(BaseModel):
    url: str


class RedirectCheckRequest(BaseModel):
    urls: List[str]


class CanonicalCheckRequest(BaseModel):
    urls: List[str]


class MobileCheckRequest(BaseModel):
    url: str


class CompetitorRequest(BaseModel):
    my_url: str
    competitor_urls: List[str]


class RankCheckRequest(BaseModel):
    keywords: List[str]
    domain: str


class SitemapGenerateRequest(BaseModel):
    url: str
    max_pages: int = 100


class RobotsGenerateRequest(BaseModel):
    sitemap_url: Optional[str] = None
    crawl_delay: Optional[int] = None
    mode: str = "default"  # "default", "permissive", "restrictive"


class ApiResponse(BaseModel):
    success: bool = True
    data: dict = {}
    message: str = ""
