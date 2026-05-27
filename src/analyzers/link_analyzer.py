"""Link analyzer - checks internal/external links, anchor text distribution."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from collections import Counter

from src.utils.html_parser import HtmlParser


@dataclass
class LinkIssue:
    severity: str
    message: str
    suggestion: str = ""


@dataclass
class LinkAnalysisResult:
    url: str
    total_links: int = 0
    internal_links: int = 0
    external_links: int = 0
    nofollow_links: int = 0
    links_with_empty_anchor: int = 0
    links_with_generic_anchor: int = 0
    unique_internal_urls: int = 0
    unique_external_urls: int = 0
    anchor_text_distribution: Dict[str, int] = field(default_factory=dict)
    links: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[LinkIssue] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "total_links": self.total_links,
            "internal_links": self.internal_links,
            "external_links": self.external_links,
            "nofollow_links": self.nofollow_links,
            "links_with_empty_anchor": self.links_with_empty_anchor,
            "links_with_generic_anchor": self.links_with_generic_anchor,
            "unique_internal_urls": self.unique_internal_urls,
            "unique_external_urls": self.unique_external_urls,
            "anchor_text_distribution": self.anchor_text_distribution,
            "issues": [{"severity": i.severity, "message": i.message, "suggestion": i.suggestion} for i in self.issues],
            "score": self.score,
        }


class LinkAnalyzer:
    """Analyzes links for SEO best practices."""

    GENERIC_ANCHORS = [
        "click here", "read more", "learn more", "here", "this",
        "more", "link", "continue", "go", "see more",
    ]

    def analyze(self, html: str, url: str) -> LinkAnalysisResult:
        """Perform complete link analysis."""
        parser = HtmlParser(html, url)
        links = parser.get_links()

        result = LinkAnalysisResult(url=url)
        result.links = links
        result.total_links = len(links)

        internal_urls = set()
        external_urls = set()
        anchor_texts = []

        for link in links:
            if link["is_internal"]:
                result.internal_links += 1
                internal_urls.add(link["absolute_url"])
            else:
                result.external_links += 1
                external_urls.add(link["absolute_url"])

            if link["is_nofollow"]:
                result.nofollow_links += 1

            anchor = link["text"].strip()
            if not anchor:
                result.links_with_empty_anchor += 1
            elif anchor.lower() in self.GENERIC_ANCHORS:
                result.links_with_generic_anchor += 1

            if anchor:
                anchor_texts.append(anchor.lower())

        result.unique_internal_urls = len(internal_urls)
        result.unique_external_urls = len(external_urls)
        result.anchor_text_distribution = dict(Counter(anchor_texts).most_common(20))

        # Run checks
        self._check_link_count(result)
        self._check_empty_anchors(result)
        self._check_generic_anchors(result)
        self._check_external_ratio(result)
        self._check_nofollow_usage(result)

        result.score = self._calculate_score(result)
        return result

    def _check_link_count(self, result: LinkAnalysisResult):
        """Check total link count."""
        if result.total_links == 0:
            result.issues.append(LinkIssue(
                severity="warning",
                message="No links found on the page",
                suggestion="Add internal links to improve site navigation and SEO.",
            ))
        elif result.internal_links == 0:
            result.issues.append(LinkIssue(
                severity="warning",
                message="No internal links found",
                suggestion="Add internal links to distribute page authority and improve crawlability.",
            ))

    def _check_empty_anchors(self, result: LinkAnalysisResult):
        """Check for links with empty anchor text."""
        if result.links_with_empty_anchor > 0:
            result.issues.append(LinkIssue(
                severity="warning",
                message=f"{result.links_with_empty_anchor} links with empty anchor text",
                suggestion="Add descriptive anchor text to all links for accessibility and SEO.",
            ))

    def _check_generic_anchors(self, result: LinkAnalysisResult):
        """Check for links with generic anchor text."""
        if result.links_with_generic_anchor > 3:
            result.issues.append(LinkIssue(
                severity="info",
                message=f"{result.links_with_generic_anchor} links with generic anchor text (e.g., 'click here')",
                suggestion="Use descriptive, keyword-rich anchor text instead of generic phrases.",
            ))

    def _check_external_ratio(self, result: LinkAnalysisResult):
        """Check external links ratio."""
        if result.total_links > 0:
            ratio = result.external_links / result.total_links
            if ratio > 0.7:
                result.issues.append(LinkIssue(
                    severity="warning",
                    message=f"High external link ratio ({ratio:.0%})",
                    suggestion="Balance internal and external links. Too many external links may leak page authority.",
                ))

    def _check_nofollow_usage(self, result: LinkAnalysisResult):
        """Check nofollow link usage."""
        if result.nofollow_links > 0 and result.internal_links > 0:
            internal_nofollow = sum(
                1 for link in result.links
                if link["is_internal"] and link["is_nofollow"]
            )
            if internal_nofollow > 0:
                result.issues.append(LinkIssue(
                    severity="info",
                    message=f"{internal_nofollow} internal links have nofollow attribute",
                    suggestion="Avoid using nofollow on internal links as it wastes crawl budget.",
                ))

    def _calculate_score(self, result: LinkAnalysisResult) -> float:
        """Calculate link SEO score."""
        score = 100.0
        for issue in result.issues:
            if issue.severity == "error":
                score -= 15
            elif issue.severity == "warning":
                score -= 10
            elif issue.severity == "info":
                score -= 3
        return max(0.0, min(100.0, score))
