"""Sitemap parser - parse and validate sitemap.xml files."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from src.utils.http_client import HttpClient
from src.utils.logger import logger


@dataclass
class SitemapUrl:
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None


@dataclass
class SitemapResult:
    url: str
    urls: List[SitemapUrl] = field(default_factory=list)
    total_urls: int = 0
    sub_sitemaps: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    is_index: bool = False
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "total_urls": self.total_urls,
            "is_index": self.is_index,
            "sub_sitemaps": self.sub_sitemaps,
            "urls": [
                {"loc": u.loc, "lastmod": u.lastmod,
                 "changefreq": u.changefreq, "priority": u.priority}
                for u in self.urls
            ],
            "errors": self.errors,
            "success": self.success,
        }



class SitemapParser:
    """Parses sitemap.xml and sitemap index files."""

    NAMESPACES = {
        "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    }

    async def parse(self, url: str) -> SitemapResult:
        """Parse a sitemap URL (handles both index and regular sitemaps)."""
        result = SitemapResult(url=url)

        async with HttpClient() as client:
            html = await client.fetch_page(url)

        if not html:
            result.errors.append(f"Failed to fetch sitemap: {url}")
            return result

        try:
            root = ET.fromstring(html)
        except ET.ParseError as e:
            result.errors.append(f"XML parse error: {e}")
            return result

        # Detect namespace
        tag = root.tag
        ns = ""
        if "{" in tag:
            ns = tag.split("}")[0] + "}"

        # Check if sitemap index
        if "sitemapindex" in tag.lower():
            result.is_index = True
            for sitemap in root.findall(f"{ns}sitemap"):
                loc = sitemap.find(f"{ns}loc")
                if loc is not None and loc.text:
                    result.sub_sitemaps.append(loc.text.strip())
        else:
            # Regular sitemap
            for url_elem in root.findall(f"{ns}url"):
                loc = url_elem.find(f"{ns}loc")
                if loc is None or not loc.text:
                    continue

                lastmod = url_elem.find(f"{ns}lastmod")
                changefreq = url_elem.find(f"{ns}changefreq")
                priority = url_elem.find(f"{ns}priority")

                sitemap_url = SitemapUrl(
                    loc=loc.text.strip(),
                    lastmod=lastmod.text.strip() if lastmod is not None and lastmod.text else None,
                    changefreq=changefreq.text.strip() if changefreq is not None and changefreq.text else None,
                    priority=float(priority.text.strip()) if priority is not None and priority.text else None,
                )
                result.urls.append(sitemap_url)

        result.total_urls = len(result.urls)
        result.success = True
        return result

    async def parse_recursive(self, url: str) -> SitemapResult:
        """Parse sitemap and follow sitemap index entries."""
        result = await self.parse(url)

        if result.is_index and result.sub_sitemaps:
            all_urls = []
            for sub_url in result.sub_sitemaps:
                sub_result = await self.parse(sub_url)
                all_urls.extend(sub_result.urls)
                result.errors.extend(sub_result.errors)

            result.urls = all_urls
            result.total_urls = len(all_urls)

        return result

    @staticmethod
    def get_sitemap_url(base_url: str) -> str:
        """Construct default sitemap URL from base URL."""
        return urljoin(base_url, "/sitemap.xml")
