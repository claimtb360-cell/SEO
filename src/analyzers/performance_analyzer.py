"""Performance analyzer - Core Web Vitals, page speed metrics."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.html_parser import HtmlParser
from src.utils.config import settings
from src.utils.logger import logger


@dataclass
class PerformanceIssue:
    severity: str
    message: str
    suggestion: str = ""


@dataclass
class PerformanceResult:
    url: str
    page_size_bytes: int = 0
    total_scripts: int = 0
    total_stylesheets: int = 0
    render_blocking_scripts: int = 0
    inline_styles: int = 0
    issues: List[PerformanceIssue] = field(default_factory=list)
    core_web_vitals: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "page_size_bytes": self.page_size_bytes,
            "page_size_kb": round(self.page_size_bytes / 1024, 2),
            "total_scripts": self.total_scripts,
            "total_stylesheets": self.total_stylesheets,
            "render_blocking_scripts": self.render_blocking_scripts,
            "inline_styles": self.inline_styles,
            "core_web_vitals": self.core_web_vitals,
            "issues": [
                {"severity": i.severity, "message": i.message, "suggestion": i.suggestion}
                for i in self.issues
            ],
            "score": self.score,
        }



class PerformanceAnalyzer:
    """Analyzes page performance for SEO (page size, scripts, CWV)."""

    MAX_PAGE_SIZE_KB = 500
    MAX_SCRIPTS = 20
    MAX_STYLESHEETS = 10

    def analyze(self, html: str, url: str) -> PerformanceResult:
        """Perform page performance analysis from HTML content."""
        parser = HtmlParser(html, url)
        result = PerformanceResult(url=url)

        result.page_size_bytes = len(html.encode("utf-8"))
        scripts = parser.get_scripts()
        stylesheets = parser.get_stylesheets()

        result.total_scripts = len(scripts)
        result.total_stylesheets = len(stylesheets)
        result.render_blocking_scripts = sum(
            1 for s in scripts if s["src"] and not s["async"] and not s["defer"]
        )
        result.inline_styles = len(parser.soup.find_all("style"))

        self._check_page_size(result)
        self._check_scripts(result)
        self._check_stylesheets(result)
        self._check_render_blocking(result)

        result.score = self._calculate_score(result)
        return result

    async def analyze_with_api(self, url: str) -> PerformanceResult:
        """Analyze using Google PageSpeed Insights API."""
        from src.utils.http_client import HttpClient

        result = PerformanceResult(url=url)

        if not settings.pagespeed_api_key:
            logger.warning("PageSpeed API key not configured")
            return result

        api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeedTests"
        params = {
            "url": url,
            "key": settings.pagespeed_api_key,
            "strategy": "mobile",
            "category": ["performance", "seo"],
        }

        try:
            async with HttpClient() as client:
                response = await client.get(api_url, params=params)
                data = response.json()

            metrics = data.get("lighthouseResult", {}).get("audits", {})
            result.core_web_vitals = {
                "LCP": metrics.get("largest-contentful-paint", {}).get("numericValue"),
                "FID": metrics.get("max-potential-fid", {}).get("numericValue"),
                "CLS": metrics.get("cumulative-layout-shift", {}).get("numericValue"),
                "FCP": metrics.get("first-contentful-paint", {}).get("numericValue"),
                "TTFB": metrics.get("server-response-time", {}).get("numericValue"),
            }

            perf_score = (
                data.get("lighthouseResult", {})
                .get("categories", {})
                .get("performance", {})
                .get("score", 0)
            )
            result.score = perf_score * 100

        except Exception as e:
            logger.error(f"PageSpeed API error: {e}")

        return result


    def _check_page_size(self, result: PerformanceResult):
        size_kb = result.page_size_bytes / 1024
        if size_kb > self.MAX_PAGE_SIZE_KB:
            result.issues.append(PerformanceIssue(
                severity="warning",
                message=f"Page size is large ({size_kb:.0f}KB, recommended < {self.MAX_PAGE_SIZE_KB}KB)",
                suggestion="Minimize HTML, remove unused code, and compress resources.",
            ))

    def _check_scripts(self, result: PerformanceResult):
        if result.total_scripts > self.MAX_SCRIPTS:
            result.issues.append(PerformanceIssue(
                severity="warning",
                message=f"Too many scripts ({result.total_scripts}, recommended < {self.MAX_SCRIPTS})",
                suggestion="Combine and minify JavaScript files to reduce HTTP requests.",
            ))

    def _check_stylesheets(self, result: PerformanceResult):
        if result.total_stylesheets > self.MAX_STYLESHEETS:
            result.issues.append(PerformanceIssue(
                severity="info",
                message=f"Many stylesheets ({result.total_stylesheets})",
                suggestion="Combine CSS files to reduce HTTP requests.",
            ))

    def _check_render_blocking(self, result: PerformanceResult):
        if result.render_blocking_scripts > 3:
            result.issues.append(PerformanceIssue(
                severity="warning",
                message=f"{result.render_blocking_scripts} render-blocking scripts",
                suggestion="Add 'async' or 'defer' attributes to non-critical scripts.",
            ))

    def _calculate_score(self, result: PerformanceResult) -> float:
        score = 100.0
        for issue in result.issues:
            if issue.severity == "error":
                score -= 20
            elif issue.severity == "warning":
                score -= 12
            elif issue.severity == "info":
                score -= 5
        return max(0.0, min(100.0, score))
