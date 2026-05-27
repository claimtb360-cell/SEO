"""Canonical URL checker - validates canonical tag implementation."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin

from src.utils.http_client import HttpClient
from src.utils.html_parser import HtmlParser
from src.utils.logger import logger


@dataclass
class CanonicalIssue:
    url: str
    issue_type: str
    message: str
    canonical_url: Optional[str] = None


@dataclass
class CanonicalCheckResult:
    urls_checked: int = 0
    issues: List[CanonicalIssue] = field(default_factory=list)
    pages_without_canonical: int = 0
    self_referencing: int = 0
    cross_domain_canonicals: int = 0

    @property
    def issues_count(self) -> int:
        return len(self.issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "urls_checked": self.urls_checked,
            "issues_count": self.issues_count,
            "pages_without_canonical": self.pages_without_canonical,
            "self_referencing": self.self_referencing,
            "cross_domain_canonicals": self.cross_domain_canonicals,
            "issues": [
                {
                    "url": i.url,
                    "issue_type": i.issue_type,
                    "message": i.message,
                    "canonical_url": i.canonical_url,
                }
                for i in self.issues
            ],
        }


class CanonicalChecker:
    """Validates canonical URL implementation across pages."""

    async def check_page(self, url: str, html: Optional[str] = None) -> List[CanonicalIssue]:
        """Check canonical tag for a single page."""
        issues = []

        if html is None:
            async with HttpClient() as client:
                html = await client.fetch_page(url)
            if not html:
                issues.append(CanonicalIssue(
                    url=url, issue_type="fetch_error",
                    message="Could not fetch page to check canonical",
                ))
                return issues

        parser = HtmlParser(html, url)
        canonical = parser.canonical_url

        if not canonical:
            issues.append(CanonicalIssue(
                url=url, issue_type="missing",
                message="No canonical tag found",
            ))
            return issues

        # Resolve relative canonical
        canonical_absolute = urljoin(url, canonical)
        parsed_url = urlparse(url)
        parsed_canonical = urlparse(canonical_absolute)

        # Check cross-domain
        if parsed_url.netloc != parsed_canonical.netloc:
            issues.append(CanonicalIssue(
                url=url, issue_type="cross_domain",
                message=f"Canonical points to different domain: {parsed_canonical.netloc}",
                canonical_url=canonical_absolute,
            ))

        # Check if canonical is accessible
        async with HttpClient() as client:
            check = await client.check_url(canonical_absolute)
            if not check["is_alive"]:
                issues.append(CanonicalIssue(
                    url=url, issue_type="broken_canonical",
                    message=f"Canonical URL returns {check['status_code']}",
                    canonical_url=canonical_absolute,
                ))

        return issues

    async def check_pages(self, urls: List[str]) -> CanonicalCheckResult:
        """Check canonical tags across multiple pages."""
        import asyncio

        result = CanonicalCheckResult()
        result.urls_checked = len(urls)

        for url in urls:
            page_issues = await self.check_page(url)
            result.issues.extend(page_issues)

            for issue in page_issues:
                if issue.issue_type == "missing":
                    result.pages_without_canonical += 1
                elif issue.issue_type == "cross_domain":
                    result.cross_domain_canonicals += 1

        result.self_referencing = result.urls_checked - result.pages_without_canonical - result.cross_domain_canonicals

        return result
