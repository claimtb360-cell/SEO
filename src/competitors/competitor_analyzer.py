"""Competitor analyzer - side-by-side SEO comparison."""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.http_client import HttpClient
from src.utils.html_parser import HtmlParser
from src.analyzers.meta_analyzer import MetaAnalyzer
from src.analyzers.heading_analyzer import HeadingAnalyzer
from src.analyzers.content_analyzer import ContentAnalyzer
from src.analyzers.link_analyzer import LinkAnalyzer
from src.analyzers.performance_analyzer import PerformanceAnalyzer


@dataclass
class CompetitorProfile:
    url: str
    title: str = ""
    description: str = ""
    word_count: int = 0
    heading_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    images_count: int = 0
    page_size_kb: float = 0.0
    load_time_ms: float = 0.0
    meta_score: float = 0.0
    content_score: float = 0.0
    performance_score: float = 0.0
    overall_score: float = 0.0
    top_keywords: List[Dict[str, Any]] = field(default_factory=list)
    has_structured_data: bool = False
    has_og_tags: bool = False
    has_twitter_cards: bool = False
    has_canonical: bool = False
    has_sitemap: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "word_count": self.word_count,
            "heading_count": self.heading_count,
            "internal_links": self.internal_links,
            "external_links": self.external_links,
            "images_count": self.images_count,
            "page_size_kb": self.page_size_kb,
            "load_time_ms": self.load_time_ms,
            "meta_score": self.meta_score,
            "content_score": self.content_score,
            "performance_score": self.performance_score,
            "overall_score": self.overall_score,
            "top_keywords": self.top_keywords,
            "has_structured_data": self.has_structured_data,
            "has_og_tags": self.has_og_tags,
            "has_twitter_cards": self.has_twitter_cards,
            "has_canonical": self.has_canonical,
            "has_sitemap": self.has_sitemap,
            "error": self.error,
        }



@dataclass
class CompetitorComparisonResult:
    my_site: Optional[CompetitorProfile] = None
    competitors: List[CompetitorProfile] = field(default_factory=list)
    advantages: List[str] = field(default_factory=list)
    disadvantages: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    keyword_gaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "my_site": self.my_site.to_dict() if self.my_site else None,
            "competitors": [c.to_dict() for c in self.competitors],
            "advantages": self.advantages,
            "disadvantages": self.disadvantages,
            "recommendations": self.recommendations,
            "keyword_gaps": self.keyword_gaps,
        }


class CompetitorAnalyzer:
    """Compares SEO metrics between your site and competitors."""

    def __init__(self):
        self.meta_analyzer = MetaAnalyzer()
        self.heading_analyzer = HeadingAnalyzer()
        self.content_analyzer = ContentAnalyzer()
        self.link_analyzer = LinkAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()

    async def analyze_site(self, url: str) -> CompetitorProfile:
        """Analyze a single site for competitor comparison."""
        import time
        profile = CompetitorProfile(url=url)
        start = time.time()

        async with HttpClient() as client:
            html = await client.fetch_page(url)

        if not html:
            profile.error = "Failed to fetch page"
            return profile

        profile.load_time_ms = round((time.time() - start) * 1000, 2)
        profile.page_size_kb = round(len(html.encode()) / 1024, 2)

        parser = HtmlParser(html, url)
        profile.title = parser.title or ""
        profile.description = parser.meta_description or ""
        profile.has_canonical = parser.canonical_url is not None
        profile.images_count = len(parser.get_images())

        # Meta analysis
        meta_result = self.meta_analyzer.analyze(html, url)
        profile.meta_score = meta_result.score
        profile.has_structured_data = len(meta_result.structured_data) > 0
        profile.has_og_tags = len(meta_result.og_tags) >= 3
        profile.has_twitter_cards = len(meta_result.twitter_tags) >= 2

        # Content analysis
        content_result = self.content_analyzer.analyze(html, url)
        profile.content_score = content_result.score
        profile.word_count = content_result.word_count
        profile.top_keywords = content_result.top_keywords[:10]

        # Heading analysis
        heading_result = self.heading_analyzer.analyze(html, url)
        profile.heading_count = heading_result.total_headings

        # Link analysis
        link_result = self.link_analyzer.analyze(html, url)
        profile.internal_links = link_result.internal_links
        profile.external_links = link_result.external_links

        # Performance analysis
        perf_result = self.performance_analyzer.analyze(html, url)
        profile.performance_score = perf_result.score

        # Overall score
        scores = [profile.meta_score, profile.content_score, profile.performance_score]
        profile.overall_score = round(sum(scores) / len(scores), 1)

        # Check sitemap
        profile.has_sitemap = await self._check_sitemap(url)

        return profile


    async def compare(
        self,
        my_url: str,
        competitor_urls: List[str],
    ) -> CompetitorComparisonResult:
        """Compare your site against competitors."""
        result = CompetitorComparisonResult()

        # Analyze all sites concurrently
        all_urls = [my_url] + competitor_urls
        tasks = [self.analyze_site(url) for url in all_urls]
        profiles = await asyncio.gather(*tasks)

        result.my_site = profiles[0]
        result.competitors = list(profiles[1:])

        # Generate insights
        self._find_advantages(result)
        self._find_disadvantages(result)
        self._find_keyword_gaps(result)
        self._generate_recommendations(result)

        return result

    def _find_advantages(self, result: CompetitorComparisonResult):
        """Find areas where your site outperforms competitors."""
        my = result.my_site
        if not my:
            return

        avg_score = self._avg([c.overall_score for c in result.competitors])
        if my.overall_score > avg_score:
            result.advantages.append(
                f"Overall SEO score ({my.overall_score:.0f}) is above competitor average ({avg_score:.0f})"
            )

        avg_words = self._avg([c.word_count for c in result.competitors])
        if my.word_count > avg_words * 1.2:
            result.advantages.append(
                f"Content length ({my.word_count} words) exceeds competitor average ({avg_words:.0f})"
            )

        avg_speed = self._avg([c.load_time_ms for c in result.competitors])
        if my.load_time_ms < avg_speed * 0.8:
            result.advantages.append(
                f"Page loads faster ({my.load_time_ms:.0f}ms vs avg {avg_speed:.0f}ms)"
            )

        if my.has_structured_data and not all(c.has_structured_data for c in result.competitors):
            result.advantages.append("Has structured data (JSON-LD) while some competitors don't")

    def _find_disadvantages(self, result: CompetitorComparisonResult):
        """Find areas where competitors outperform your site."""
        my = result.my_site
        if not my:
            return

        avg_score = self._avg([c.overall_score for c in result.competitors])
        if my.overall_score < avg_score:
            result.disadvantages.append(
                f"Overall SEO score ({my.overall_score:.0f}) is below competitor average ({avg_score:.0f})"
            )

        avg_words = self._avg([c.word_count for c in result.competitors])
        if my.word_count < avg_words * 0.7:
            result.disadvantages.append(
                f"Content is shorter ({my.word_count} words) than competitor average ({avg_words:.0f})"
            )

        if not my.has_structured_data and any(c.has_structured_data for c in result.competitors):
            result.disadvantages.append("Missing structured data that competitors have")

        if not my.has_og_tags and any(c.has_og_tags for c in result.competitors):
            result.disadvantages.append("Missing Open Graph tags for social sharing")

    def _find_keyword_gaps(self, result: CompetitorComparisonResult):
        """Find keywords competitors use that you don't."""
        my = result.my_site
        if not my:
            return

        my_keywords = {kw["keyword"] for kw in my.top_keywords}

        for competitor in result.competitors:
            for kw_data in competitor.top_keywords:
                kw = kw_data["keyword"]
                if kw not in my_keywords and kw_data.get("count", 0) >= 3:
                    result.keyword_gaps.append(
                        f"'{kw}' used by {competitor.url} ({kw_data['count']}x)"
                    )

        # Deduplicate and limit
        result.keyword_gaps = list(dict.fromkeys(result.keyword_gaps))[:20]

    def _generate_recommendations(self, result: CompetitorComparisonResult):
        """Generate actionable recommendations based on comparison."""
        my = result.my_site
        if not my:
            return

        best = max(result.competitors, key=lambda c: c.overall_score, default=None)
        if not best:
            return

        if my.word_count < best.word_count:
            diff = best.word_count - my.word_count
            result.recommendations.append(
                f"Increase content by ~{diff} words to match top competitor"
            )

        if my.internal_links < best.internal_links:
            result.recommendations.append(
                f"Add more internal links (you: {my.internal_links}, top: {best.internal_links})"
            )

        if not my.has_structured_data and best.has_structured_data:
            result.recommendations.append("Add JSON-LD structured data to match competitors")

        if not my.has_sitemap:
            result.recommendations.append("Create and submit a sitemap.xml")

        if my.load_time_ms > best.load_time_ms * 1.5:
            result.recommendations.append(
                f"Improve page speed (you: {my.load_time_ms:.0f}ms, best: {best.load_time_ms:.0f}ms)"
            )

        if result.keyword_gaps:
            result.recommendations.append(
                f"Consider targeting {len(result.keyword_gaps)} keywords used by competitors"
            )

    async def _check_sitemap(self, url: str) -> bool:
        """Check if site has a sitemap.xml."""
        from urllib.parse import urljoin
        sitemap_url = urljoin(url, "/sitemap.xml")
        async with HttpClient() as client:
            check = await client.check_url(sitemap_url)
            return check.get("is_alive", False)

    @staticmethod
    def _avg(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0
