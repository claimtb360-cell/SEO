"""Site crawler - crawl entire website with configurable depth."""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Optional, Callable
from urllib.parse import urlparse
from datetime import datetime

from src.utils.http_client import HttpClient
from src.utils.html_parser import HtmlParser
from src.utils.logger import logger
from src.utils.config import settings


@dataclass
class CrawledPage:
    url: str
    status_code: int = 0
    title: str = ""
    depth: int = 0
    response_time_ms: float = 0.0
    word_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    error: Optional[str] = None


@dataclass
class CrawlResult:
    base_url: str
    pages: List[CrawledPage] = field(default_factory=list)
    total_pages: int = 0
    total_errors: int = 0
    avg_response_time: float = 0.0
    crawl_duration_sec: float = 0.0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "total_pages": self.total_pages,
            "total_errors": self.total_errors,
            "avg_response_time": self.avg_response_time,
            "crawl_duration_sec": self.crawl_duration_sec,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "pages": [
                {
                    "url": p.url, "status_code": p.status_code,
                    "title": p.title, "depth": p.depth,
                    "response_time_ms": p.response_time_ms,
                    "word_count": p.word_count,
                    "internal_links": p.internal_links,
                    "external_links": p.external_links,
                    "error": p.error,
                } for p in self.pages
            ],
        }



class SiteCrawler:
    """Crawls entire website following internal links."""

    def __init__(
        self,
        max_pages: int = 100,
        max_depth: int = 3,
        delay: Optional[float] = None,
        on_page_crawled: Optional[Callable] = None,
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay or settings.crawl_delay
        self.on_page_crawled = on_page_crawled
        self._visited: Set[str] = set()
        self._queue: asyncio.Queue = asyncio.Queue()

    async def crawl(self, start_url: str) -> CrawlResult:
        """Start crawling from the given URL."""
        import time

        result = CrawlResult(base_url=start_url)
        result.started_at = datetime.now().isoformat()
        start_time = time.time()

        parsed = urlparse(start_url)
        self._base_domain = parsed.netloc

        await self._queue.put((start_url, 0))

        async with HttpClient() as client:
            while not self._queue.empty() and len(self._visited) < self.max_pages:
                url, depth = await self._queue.get()

                if url in self._visited or depth > self.max_depth:
                    continue

                self._visited.add(url)
                page = await self._crawl_page(client, url, depth)
                result.pages.append(page)

                if page.error:
                    result.total_errors += 1

                if self.on_page_crawled:
                    self.on_page_crawled(page)

                logger.info(f"Crawled [{len(self._visited)}/{self.max_pages}]: {url}")

                if self.delay > 0:
                    await asyncio.sleep(self.delay)

        elapsed = time.time() - start_time
        result.total_pages = len(result.pages)
        result.crawl_duration_sec = round(elapsed, 2)
        result.finished_at = datetime.now().isoformat()

        times = [p.response_time_ms for p in result.pages if p.response_time_ms > 0]
        result.avg_response_time = round(sum(times) / len(times), 2) if times else 0

        return result


    async def _crawl_page(self, client: HttpClient, url: str, depth: int) -> CrawledPage:
        """Crawl a single page and extract links."""
        import time

        page = CrawledPage(url=url, depth=depth)
        start = time.time()

        try:
            response = await client.get(url)
            page.status_code = response.status_code
            page.response_time_ms = round((time.time() - start) * 1000, 2)

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return page

            html = response.text
            parser = HtmlParser(html, url)

            page.title = parser.title or ""
            page.word_count = parser.get_word_count()

            # Extract and queue internal links
            links = parser.get_links()
            internal = [link for link in links if link["is_internal"]]
            external = [link for link in links if not link["is_internal"]]

            page.internal_links = len(internal)
            page.external_links = len(external)

            # Queue new internal links
            if depth < self.max_depth:
                for link in internal:
                    link_url = link["absolute_url"].split("#")[0].split("?")[0]
                    if (
                        link_url not in self._visited
                        and self._is_same_domain(link_url)
                        and self._is_crawlable(link_url)
                    ):
                        await self._queue.put((link_url, depth + 1))

        except Exception as e:
            page.error = str(e)
            page.response_time_ms = round((time.time() - start) * 1000, 2)

        return page

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        parsed = urlparse(url)
        return parsed.netloc == self._base_domain

    def _is_crawlable(self, url: str) -> bool:
        """Check if URL should be crawled (skip assets, etc.)."""
        skip_extensions = {
            ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
            ".css", ".js", ".ico", ".woff", ".woff2", ".ttf", ".eot",
            ".mp3", ".mp4", ".avi", ".zip", ".tar", ".gz",
        }
        parsed = urlparse(url)
        path = parsed.path.lower()
        return not any(path.endswith(ext) for ext in skip_extensions)
