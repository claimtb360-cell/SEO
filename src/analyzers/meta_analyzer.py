"""Meta tag analyzer - checks title, description, OG tags, Twitter cards."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.html_parser import HtmlParser


@dataclass
class MetaIssue:
    """Represents an SEO issue found in meta tags."""
    severity: str  # "error", "warning", "info"
    message: str
    tag: str
    suggestion: str = ""


@dataclass
class MetaAnalysisResult:
    """Result of meta tag analysis."""
    url: str
    title: Optional[str] = None
    title_length: int = 0
    description: Optional[str] = None
    description_length: int = 0
    keywords: Optional[str] = None
    canonical: Optional[str] = None
    robots: Optional[str] = None
    viewport: Optional[str] = None
    charset: Optional[str] = None
    og_tags: Dict[str, str] = field(default_factory=dict)
    twitter_tags: Dict[str, str] = field(default_factory=dict)
    structured_data: List[Dict] = field(default_factory=list)
    issues: List[MetaIssue] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "title_length": self.title_length,
            "description": self.description,
            "description_length": self.description_length,
            "keywords": self.keywords,
            "canonical": self.canonical,
            "robots": self.robots,
            "viewport": self.viewport,
            "charset": self.charset,
            "og_tags": self.og_tags,
            "twitter_tags": self.twitter_tags,
            "structured_data": self.structured_data,
            "issues": [{"severity": i.severity, "message": i.message, "tag": i.tag, "suggestion": i.suggestion} for i in self.issues],
            "score": self.score,
        }


class MetaAnalyzer:
    """Analyzes meta tags for SEO best practices."""

    # Optimal lengths
    TITLE_MIN_LENGTH = 30
    TITLE_MAX_LENGTH = 60
    DESC_MIN_LENGTH = 120
    DESC_MAX_LENGTH = 160

    # Required OG tags
    REQUIRED_OG_TAGS = ["og:title", "og:description", "og:image", "og:url", "og:type"]
    REQUIRED_TWITTER_TAGS = ["twitter:card", "twitter:title", "twitter:description"]

    def analyze(self, html: str, url: str) -> MetaAnalysisResult:
        """Perform complete meta tag analysis."""
        parser = HtmlParser(html, url)
        meta = parser.get_meta_tags()

        result = MetaAnalysisResult(url=url)
        result.title = meta.get("title")
        result.title_length = len(result.title) if result.title else 0
        result.description = meta.get("description")
        result.description_length = len(result.description) if result.description else 0
        result.keywords = meta.get("keywords")
        result.canonical = meta.get("canonical")
        result.robots = meta.get("robots")
        result.viewport = meta.get("viewport")
        result.charset = meta.get("charset")
        result.og_tags = meta.get("og", {})
        result.twitter_tags = meta.get("twitter", {})
        result.structured_data = parser.get_structured_data()

        # Run checks
        self._check_title(result)
        self._check_description(result)
        self._check_canonical(result)
        self._check_robots(result)
        self._check_viewport(result)
        self._check_charset(result)
        self._check_og_tags(result)
        self._check_twitter_tags(result)
        self._check_structured_data(result)

        # Calculate score
        result.score = self._calculate_score(result)

        return result

    def _check_title(self, result: MetaAnalysisResult):
        """Check title tag for SEO issues."""
        if not result.title:
            result.issues.append(MetaIssue(
                severity="error",
                message="Missing title tag",
                tag="title",
                suggestion="Add a unique, descriptive title tag between 30-60 characters.",
            ))
        elif result.title_length < self.TITLE_MIN_LENGTH:
            result.issues.append(MetaIssue(
                severity="warning",
                message=f"Title too short ({result.title_length} chars, min {self.TITLE_MIN_LENGTH})",
                tag="title",
                suggestion="Expand your title to include more relevant keywords.",
            ))
        elif result.title_length > self.TITLE_MAX_LENGTH:
            result.issues.append(MetaIssue(
                severity="warning",
                message=f"Title too long ({result.title_length} chars, max {self.TITLE_MAX_LENGTH})",
                tag="title",
                suggestion="Shorten your title to avoid truncation in search results.",
            ))

    def _check_description(self, result: MetaAnalysisResult):
        """Check meta description for SEO issues."""
        if not result.description:
            result.issues.append(MetaIssue(
                severity="error",
                message="Missing meta description",
                tag="description",
                suggestion="Add a compelling meta description between 120-160 characters.",
            ))
        elif result.description_length < self.DESC_MIN_LENGTH:
            result.issues.append(MetaIssue(
                severity="warning",
                message=f"Description too short ({result.description_length} chars, min {self.DESC_MIN_LENGTH})",
                tag="description",
                suggestion="Expand your description to better summarize the page content.",
            ))
        elif result.description_length > self.DESC_MAX_LENGTH:
            result.issues.append(MetaIssue(
                severity="warning",
                message=f"Description too long ({result.description_length} chars, max {self.DESC_MAX_LENGTH})",
                tag="description",
                suggestion="Shorten your description to avoid truncation in search results.",
            ))

    def _check_canonical(self, result: MetaAnalysisResult):
        """Check canonical URL."""
        if not result.canonical:
            result.issues.append(MetaIssue(
                severity="warning",
                message="Missing canonical URL",
                tag="canonical",
                suggestion="Add a canonical URL to prevent duplicate content issues.",
            ))

    def _check_robots(self, result: MetaAnalysisResult):
        """Check robots meta tag."""
        if result.robots and "noindex" in result.robots.lower():
            result.issues.append(MetaIssue(
                severity="info",
                message="Page is set to noindex",
                tag="robots",
                suggestion="This page will not be indexed by search engines.",
            ))

    def _check_viewport(self, result: MetaAnalysisResult):
        """Check viewport meta tag."""
        if not result.viewport:
            result.issues.append(MetaIssue(
                severity="error",
                message="Missing viewport meta tag",
                tag="viewport",
                suggestion="Add viewport meta tag for mobile responsiveness.",
            ))

    def _check_charset(self, result: MetaAnalysisResult):
        """Check charset declaration."""
        if not result.charset:
            result.issues.append(MetaIssue(
                severity="warning",
                message="Missing charset declaration",
                tag="charset",
                suggestion="Add <meta charset='UTF-8'> for proper character encoding.",
            ))

    def _check_og_tags(self, result: MetaAnalysisResult):
        """Check Open Graph tags."""
        missing = [tag for tag in self.REQUIRED_OG_TAGS if tag not in result.og_tags]
        if missing:
            result.issues.append(MetaIssue(
                severity="warning",
                message=f"Missing Open Graph tags: {', '.join(missing)}",
                tag="og",
                suggestion="Add Open Graph tags for better social media sharing.",
            ))

    def _check_twitter_tags(self, result: MetaAnalysisResult):
        """Check Twitter Card tags."""
        missing = [tag for tag in self.REQUIRED_TWITTER_TAGS if tag not in result.twitter_tags]
        if missing:
            result.issues.append(MetaIssue(
                severity="info",
                message=f"Missing Twitter Card tags: {', '.join(missing)}",
                tag="twitter",
                suggestion="Add Twitter Card tags for better appearance when shared on Twitter.",
            ))

    def _check_structured_data(self, result: MetaAnalysisResult):
        """Check structured data presence."""
        if not result.structured_data:
            result.issues.append(MetaIssue(
                severity="info",
                message="No structured data (JSON-LD) found",
                tag="structured_data",
                suggestion="Add JSON-LD structured data to enable rich snippets in search results.",
            ))

    def _calculate_score(self, result: MetaAnalysisResult) -> float:
        """Calculate meta tag SEO score (0-100)."""
        score = 100.0
        for issue in result.issues:
            if issue.severity == "error":
                score -= 15
            elif issue.severity == "warning":
                score -= 8
            elif issue.severity == "info":
                score -= 3
        return max(0.0, min(100.0, score))
