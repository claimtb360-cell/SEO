"""Mobile-friendly checker - validates mobile responsiveness signals."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.http_client import HttpClient
from src.utils.html_parser import HtmlParser
from src.utils.logger import logger


@dataclass
class MobileIssue:
    severity: str
    message: str
    suggestion: str = ""


@dataclass
class MobileFriendlyResult:
    url: str
    is_mobile_friendly: bool = True
    has_viewport: bool = False
    has_responsive_images: bool = False
    has_media_queries: bool = False
    font_size_ok: bool = True
    tap_targets_ok: bool = True
    issues: List[MobileIssue] = field(default_factory=list)
    score: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "is_mobile_friendly": self.is_mobile_friendly,
            "has_viewport": self.has_viewport,
            "has_responsive_images": self.has_responsive_images,
            "has_media_queries": self.has_media_queries,
            "score": self.score,
            "issues": [
                {"severity": i.severity, "message": i.message, "suggestion": i.suggestion}
                for i in self.issues
            ],
        }


class MobileFriendlyChecker:
    """Checks pages for mobile-friendliness indicators."""

    async def check(self, url: str, html: Optional[str] = None) -> MobileFriendlyResult:
        """Check a page for mobile-friendliness."""
        result = MobileFriendlyResult(url=url)

        if html is None:
            async with HttpClient() as client:
                html = await client.fetch_page(url)
            if not html:
                result.is_mobile_friendly = False
                result.issues.append(MobileIssue(
                    severity="error", message="Could not fetch page",
                ))
                return result

        parser = HtmlParser(html, url)

        self._check_viewport(result, parser)
        self._check_responsive_images(result, parser)
        self._check_media_queries(result, html)
        self._check_font_sizes(result, html)
        self._check_touch_elements(result, parser)
        self._check_horizontal_scroll(result, html)

        # Calculate final score and mobile-friendly status
        result.score = self._calculate_score(result)
        result.is_mobile_friendly = result.score >= 70

        return result

    def _check_viewport(self, result: MobileFriendlyResult, parser: HtmlParser):
        """Check viewport meta tag."""
        result.has_viewport = parser.has_viewport_meta()
        if not result.has_viewport:
            result.issues.append(MobileIssue(
                severity="error",
                message="Missing viewport meta tag",
                suggestion="Add <meta name='viewport' content='width=device-width, initial-scale=1'>",
            ))

    def _check_responsive_images(self, result: MobileFriendlyResult, parser: HtmlParser):
        """Check if images are responsive."""
        images = parser.get_images()
        fixed_width_images = 0
        for img in images:
            width = img.get("width", "")
            if width and width.isdigit() and int(width) > 600:
                fixed_width_images += 1

        if fixed_width_images > 0:
            result.issues.append(MobileIssue(
                severity="warning",
                message=f"{fixed_width_images} images with fixed width > 600px",
                suggestion="Use max-width: 100% or responsive image techniques.",
            ))
        else:
            result.has_responsive_images = True

    def _check_media_queries(self, result: MobileFriendlyResult, html: str):
        """Check for CSS media queries (responsiveness indicator)."""
        if "@media" in html or "media=" in html:
            result.has_media_queries = True
        else:
            result.issues.append(MobileIssue(
                severity="info",
                message="No CSS media queries detected in inline styles",
                suggestion="Use media queries or a responsive framework for mobile layout.",
            ))

    def _check_font_sizes(self, result: MobileFriendlyResult, html: str):
        """Check for tiny font sizes."""
        import re
        tiny_fonts = re.findall(r'font-size:\s*(\d+)px', html)
        tiny_count = sum(1 for f in tiny_fonts if int(f) < 12)
        if tiny_count > 3:
            result.font_size_ok = False
            result.issues.append(MobileIssue(
                severity="warning",
                message=f"{tiny_count} elements with font-size < 12px",
                suggestion="Use minimum 16px font size for mobile readability.",
            ))

    def _check_touch_elements(self, result: MobileFriendlyResult, parser: HtmlParser):
        """Check for properly sized touch targets."""
        links = parser.get_links()
        small_targets = sum(1 for l in links if len(l.get("text", "")) < 2)
        if small_targets > 5:
            result.tap_targets_ok = False
            result.issues.append(MobileIssue(
                severity="warning",
                message=f"{small_targets} potentially small tap targets",
                suggestion="Ensure touch targets are at least 48x48px with adequate spacing.",
            ))

    def _check_horizontal_scroll(self, result: MobileFriendlyResult, html: str):
        """Check for elements that might cause horizontal scrolling."""
        import re
        fixed_widths = re.findall(r'width:\s*(\d+)px', html)
        wide_elements = sum(1 for w in fixed_widths if int(w) > 500)
        if wide_elements > 2:
            result.issues.append(MobileIssue(
                severity="warning",
                message=f"{wide_elements} elements with fixed width > 500px",
                suggestion="Avoid fixed widths. Use percentage or max-width for responsive layout.",
            ))

    def _calculate_score(self, result: MobileFriendlyResult) -> float:
        score = 100.0
        for issue in result.issues:
            if issue.severity == "error":
                score -= 25
            elif issue.severity == "warning":
                score -= 12
            elif issue.severity == "info":
                score -= 5
        return max(0.0, min(100.0, score))
