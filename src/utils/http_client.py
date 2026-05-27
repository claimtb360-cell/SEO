"""Async HTTP client wrapper with retry, rate limiting, and error handling."""

import asyncio
from typing import Optional, Dict, Any

import httpx

from .config import settings
from .logger import logger


class HttpClient:
    """Reusable async HTTP client with built-in rate limiting and retries."""

    def __init__(
        self,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.timeout = timeout or settings.request_timeout
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            **(headers or {}),
        }
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Create async client on context entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self.headers,
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=settings.max_concurrent_requests,
                max_keepalive_connections=5,
            ),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async client on context exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Perform GET request with retry and rate limiting."""
        return await self._request("GET", url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Perform POST request with retry and rate limiting."""
        return await self._request("POST", url, data=data, json=json, headers=headers)

    async def head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Perform HEAD request with retry and rate limiting."""
        return await self._request("HEAD", url, headers=headers)

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Execute request with semaphore-based rate limiting and retries."""
        async with self._semaphore:
            last_exception = None
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await self._client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 503):
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Rate limited on {url}, retrying in {wait_time}s (attempt {attempt})"
                        )
                        await asyncio.sleep(wait_time)
                        last_exception = e
                    else:
                        raise
                except (httpx.ConnectError, httpx.ReadTimeout) as e:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Connection error on {url}: {e}, retrying in {wait_time}s (attempt {attempt})"
                    )
                    await asyncio.sleep(wait_time)
                    last_exception = e

            raise last_exception

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page and return HTML content, or None on failure."""
        try:
            response = await self.get(url)
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    async def check_url(self, url: str) -> Dict[str, Any]:
        """Check URL status without downloading full content."""
        try:
            response = await self.head(url)
            return {
                "url": url,
                "status_code": response.status_code,
                "is_redirect": response.has_redirect_location,
                "redirect_url": str(response.headers.get("location", "")),
                "content_type": response.headers.get("content-type", ""),
                "is_alive": True,
            }
        except httpx.HTTPStatusError as e:
            return {
                "url": url,
                "status_code": e.response.status_code,
                "is_redirect": False,
                "redirect_url": "",
                "content_type": "",
                "is_alive": e.response.status_code < 400,
            }
        except Exception as e:
            return {
                "url": url,
                "status_code": 0,
                "is_redirect": False,
                "redirect_url": "",
                "content_type": "",
                "is_alive": False,
                "error": str(e),
            }
