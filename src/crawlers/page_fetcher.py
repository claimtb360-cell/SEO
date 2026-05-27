"""Page fetcher - fetches individual pages with metadata."""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from src.utils.http_client import HttpClient
from src.utils.logger import logger


@dataclass
class FetchResult:
    """Result of fetching a single page."""
    url: str
    status_code: int = 0
    html: str = ""
    content_type: str = ""
    response_time_ms: float = 0.0
    final_url: str = ""
    is_redirect: bool = False
    headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "response_time_ms": self.response_time_ms,
            "final_url": self.final_url,
            "is_redirect": self.is_redirect,
            "error": self.error,
            "success": self.success,
        }



class PageFetcher:
    """Fetches individual pages with timing and metadata."""

    def __init__(self):
        self._client: Optional[HttpClient] = None

    async def __aenter__(self):
        self._client = HttpClient()
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def fetch(self, url: str) -> FetchResult:
        """Fetch a single page and return detailed result."""
        result = FetchResult(url=url)
        start_time = time.time()

        try:
            response = await self._client.get(url)
            elapsed = (time.time() - start_time) * 1000

            result.status_code = response.status_code
            result.html = response.text
            result.content_type = response.headers.get("content-type", "")
            result.response_time_ms = round(elapsed, 2)
            result.final_url = str(response.url)
            result.is_redirect = str(response.url) != url
            result.headers = dict(response.headers)
            result.success = True

        except Exception as e:
            result.error = str(e)
            result.response_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Fetch error for {url}: {e}")

        return result

    async def fetch_multiple(self, urls: list) -> list:
        """Fetch multiple pages concurrently."""
        import asyncio
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)
