"""Broken link checker - detects dead links on a page or site."""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.http_client import HttpClient
from src.utils.html_parser import HtmlParser
from src.utils.logger import logger


@dataclass
class BrokenLink:
    url: str
    source_page: str
    anchor_text: str = ""
    status_code: int = 0
    error: str = ""
    is_internal: bool = False


@dataclass
class BrokenLinkResult:
    source_url: str
    total_links_checked: int = 0
    broken_links: List[BrokenLink] = field(default_factory=list)
    healthy_links: int = 0
    timeout_links: int = 0
    check_duration_sec: float = 0.0

    @property
    def broken_count(self) -> int:
        return len(self.broken_links)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_url": self.source_url,
            "total_links_checked": self.total_links_checked,
            "broken_count": self.broken_count,
            "healthy_links": self.healthy_links,
            "timeout_links": self.timeout_links,
            "check_duration_sec": self.check_duration_sec,
            "broken_links": [
                {
                    "url": bl.url,
                    "source_page": bl.source_page,
                    "anchor_text": bl.anchor_text,
                    "status_code": bl.status_code,
                    "error": bl.error,
                    "is_internal": bl.is_internal,
                }
                for bl in self.broken_links
            ],
        }



class BrokenLinkChecker:
    """Checks pages for broken links (404, 5xx, timeouts)."""

    def __init__(self, concurrency: int = 20):
        self.concurrency = concurrency

    async def check_page(self, url: str, html: Optional[str] = None) -> BrokenLinkResult:
        """Check all links on a single page."""
        import time
        start = time.time()
        result = BrokenLinkResult(source_url=url)

        if html is None:
            async with HttpClient() as client:
                html = await client.fetch_page(url)
            if not html:
                return result

        parser = HtmlParser(html, url)
        links = parser.get_links()

        # Deduplicate URLs
        unique_links = {}
        for link in links:
            abs_url = link["absolute_url"]
            if abs_url and abs_url.startswith("http"):
                if abs_url not in unique_links:
                    unique_links[abs_url] = link

        result.total_links_checked = len(unique_links)

        # Check all links concurrently
        semaphore = asyncio.Semaphore(self.concurrency)

        async def check_single(link_url: str, link_data: dict):
            async with semaphore:
                async with HttpClient(max_retries=1) as client:
                    check = await client.check_url(link_url)
                    return link_url, link_data, check

        tasks = [
            check_single(link_url, link_data)
            for link_url, link_data in unique_links.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for item in results:
            if isinstance(item, Exception):
                continue
            link_url, link_data, check = item

            if not check["is_alive"]:
                broken = BrokenLink(
                    url=link_url,
                    source_page=url,
                    anchor_text=link_data.get("text", ""),
                    status_code=check.get("status_code", 0),
                    error=check.get("error", ""),
                    is_internal=link_data.get("is_internal", False),
                )
                result.broken_links.append(broken)
            else:
                result.healthy_links += 1

        result.timeout_links = result.total_links_checked - result.healthy_links - result.broken_count
        result.check_duration_sec = round(time.time() - start, 2)
        return result

    async def check_pages(self, urls: List[str]) -> List[BrokenLinkResult]:
        """Check broken links across multiple pages."""
        results = []
        for url in urls:
            res = await self.check_page(url)
            results.append(res)
            logger.info(f"Checked {url}: {res.broken_count} broken links found")
        return results
