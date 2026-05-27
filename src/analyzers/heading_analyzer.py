"""Heading structure analyzer - validates H1-H6 hierarchy."""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from src.utils.html_parser import HtmlParser


@dataclass
class HeadingIssue:
    severity: str
    message: str
    suggestion: str = ""


@dataclass
class HeadingAnalysisResult:
    url: str
    headings: Dict[str, List[str]] = field(default_factory=dict)
    h1_count: int = 0
    total_headings: int = 0
    hierarchy_valid: bool = True
    issues: List[HeadingIssue] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "headings": self.headings,
            "h1_count": self.h1_count,
            "total_headings": self.total_headings,
            "hierarchy_valid": self.hierarchy_valid,
            "issues": [{"severity": i.severity, "message": i.message, "suggestion": i.suggestion} for i in self.issues],
            "score": self.score,
        }


class HeadingAnalyzer:
    """Analyzes heading structure for SEO best practices."""

    def analyze(self, html: str, url: str) -> HeadingAnalysisResult:
        """Perform heading structure analysis."""
        parser = HtmlParser(html, url)
        headings = parser.get_headings()

        result = HeadingAnalysisResult(url=url, headings=headings)
        result.h1_count = len(headings.get("h1", []))
        result.total_headings = sum(len(v) for v in headings.values())

        self._check_h1(result)
        self._check_hierarchy(result, headings)
        self._check_length(result, headings)
        self._check_duplicate(result, headings)
        self._check_empty(result, headings)

        result.score = self._calculate_score(result)
        return result

    def _check_h1(self, result: HeadingAnalysisResult):
        """Check H1 tag presence and count."""
        if result.h1_count == 0:
            result.issues.append(HeadingIssue(
                severity="error",
                message="Missing H1 tag",
                suggestion="Add exactly one H1 tag that describes the main topic of the page.",
            ))
        elif result.h1_count > 1:
            result.issues.append(HeadingIssue(
                severity="warning",
                message=f"Multiple H1 tags found ({result.h1_count})",
                suggestion="Use only one H1 tag per page for clear content hierarchy.",
            ))

    def _check_hierarchy(self, result: HeadingAnalysisResult, headings: Dict[str, List[str]]):
        """Check heading hierarchy (no level skipping)."""
        levels_used = []
        for level in range(1, 7):
            if headings.get(f"h{level}"):
                levels_used.append(level)

        for i in range(1, len(levels_used)):
            if levels_used[i] - levels_used[i - 1] > 1:
                result.hierarchy_valid = False
                result.issues.append(HeadingIssue(
                    severity="warning",
                    message=f"Heading level skipped: H{levels_used[i-1]} to H{levels_used[i]}",
                    suggestion=f"Add H{levels_used[i-1]+1} between H{levels_used[i-1]} and H{levels_used[i]} for proper hierarchy.",
                ))

    def _check_length(self, result: HeadingAnalysisResult, headings: Dict[str, List[str]]):
        """Check heading lengths."""
        for level, texts in headings.items():
            for text in texts:
                if len(text) > 70:
                    result.issues.append(HeadingIssue(
                        severity="info",
                        message=f"{level.upper()} too long ({len(text)} chars): '{text[:50]}...'",
                        suggestion="Keep headings concise (under 70 characters) for better readability.",
                    ))

    def _check_duplicate(self, result: HeadingAnalysisResult, headings: Dict[str, List[str]]):
        """Check for duplicate headings."""
        all_headings = []
        for texts in headings.values():
            all_headings.extend(texts)

        seen = set()
        for heading in all_headings:
            lower = heading.lower().strip()
            if lower in seen:
                result.issues.append(HeadingIssue(
                    severity="info",
                    message=f"Duplicate heading: '{heading}'",
                    suggestion="Use unique headings to better describe each section.",
                ))
            seen.add(lower)

    def _check_empty(self, result: HeadingAnalysisResult, headings: Dict[str, List[str]]):
        """Check for empty headings."""
        for level, texts in headings.items():
            for text in texts:
                if not text.strip():
                    result.issues.append(HeadingIssue(
                        severity="error",
                        message=f"Empty {level.upper()} tag found",
                        suggestion="Remove empty heading tags or add meaningful content.",
                    ))

    def _calculate_score(self, result: HeadingAnalysisResult) -> float:
        """Calculate heading structure SEO score."""
        score = 100.0
        for issue in result.issues:
            if issue.severity == "error":
                score -= 20
            elif issue.severity == "warning":
                score -= 10
            elif issue.severity == "info":
                score -= 3
        return max(0.0, min(100.0, score))
