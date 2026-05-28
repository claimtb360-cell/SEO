"""Advanced SERP Checker - Top 100 results, AI Overview detection, Featured Snippets."""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class SearchEngine(str, Enum):
    GOOGLE = "google"
    BING = "bing"


class SnippetType(str, Enum):
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    VIDEO = "video"


@dataclass
class SERPResult:
    """A single organic search result."""
    position: int
    url: str
    title: str
    snippet: str
    domain: str
    is_featured: bool = False
    snippet_type: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)



@dataclass
class AIOverview:
    """AI-generated overview detected at top of SERP."""
    detected: bool = False
    summary_text: str = ""
    cited_sources: List[Dict[str, str]] = field(default_factory=list)
    cited_domains: List[str] = field(default_factory=list)
    position: str = "top"  # top, inline

    def to_dict(self) -> dict:
        return {
            "detected": self.detected,
            "summary_text": self.summary_text,
            "cited_sources": self.cited_sources,
            "cited_domains": self.cited_domains,
            "position": self.position,
        }


@dataclass
class FeaturedSnippet:
    """Featured snippet detection."""
    detected: bool = False
    type: Optional[str] = None  # paragraph, list, table, video
    content: str = ""
    source_url: str = ""
    source_domain: str = ""

    def to_dict(self) -> dict:
        return {
            "detected": self.detected,
            "type": self.type,
            "content": self.content,
            "source_url": self.source_url,
            "source_domain": self.source_domain,
        }


@dataclass
class SERPFeatures:
    """All SERP features detected."""
    ai_overview: AIOverview = field(default_factory=AIOverview)
    featured_snippet: FeaturedSnippet = field(default_factory=FeaturedSnippet)
    people_also_ask: List[str] = field(default_factory=list)
    knowledge_panel: bool = False
    local_pack: bool = False
    video_carousel: bool = False
    image_pack: bool = False
    shopping_results: bool = False

    def to_dict(self) -> dict:
        return {
            "ai_overview": self.ai_overview.to_dict(),
            "featured_snippet": self.featured_snippet.to_dict(),
            "people_also_ask": self.people_also_ask,
            "knowledge_panel": self.knowledge_panel,
            "local_pack": self.local_pack,
            "video_carousel": self.video_carousel,
            "image_pack": self.image_pack,
            "shopping_results": self.shopping_results,
        }



@dataclass
class SERPAnalysis:
    """Complete SERP analysis result."""
    keyword: str
    engine: str
    total_results: int
    organic_results: List[SERPResult] = field(default_factory=list)
    features: SERPFeatures = field(default_factory=SERPFeatures)
    domain_positions: Dict[str, List[int]] = field(default_factory=dict)
    brand_mentions: int = 0

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "engine": self.engine,
            "total_results": self.total_results,
            "organic_results": [r.to_dict() for r in self.organic_results],
            "features": self.features.to_dict(),
            "domain_positions": self.domain_positions,
            "brand_mentions": self.brand_mentions,
            "top_10_domains": [r.domain for r in self.organic_results[:10]],
        }


class SERPChecker:
    """Advanced SERP Checker with AI Overview and Featured Snippet detection."""

    def __init__(self):
        self.user_agents = {
            SearchEngine.GOOGLE: (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            SearchEngine.BING: (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }


    async def check_serp(
        self,
        keyword: str,
        engine: SearchEngine = SearchEngine.GOOGLE,
        num_results: int = 100,
        track_domain: Optional[str] = None,
    ) -> SERPAnalysis:
        """
        Check top organic results for a keyword.

        Args:
            keyword: Search keyword to check.
            engine: Search engine to query (google, bing).
            num_results: Number of results to fetch (up to 100).
            track_domain: Optional domain to track positions for.

        Returns:
            SERPAnalysis with results, features, and domain positions.
        """
        from src.utils.http_client import HttpClient

        num_results = min(num_results, 100)
        search_url = self._build_search_url(keyword, engine, num_results)

        async with HttpClient() as client:
            html = await client.fetch_page(search_url)

        if not html:
            return SERPAnalysis(
                keyword=keyword,
                engine=engine.value,
                total_results=0,
            )

        return self._parse_serp(html, keyword, engine, track_domain)

    def _build_search_url(self, keyword: str, engine: SearchEngine, num: int) -> str:
        """Build search engine URL."""
        encoded_kw = keyword.replace(" ", "+")
        if engine == SearchEngine.GOOGLE:
            return f"https://www.google.com/search?q={encoded_kw}&num={num}"
        elif engine == SearchEngine.BING:
            return f"https://www.bing.com/search?q={encoded_kw}&count={num}"
        return f"https://www.google.com/search?q={encoded_kw}&num={num}"


    def _parse_serp(
        self, html: str, keyword: str, engine: SearchEngine,
        track_domain: Optional[str] = None,
    ) -> SERPAnalysis:
        """Parse SERP HTML and extract results + features."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        analysis = SERPAnalysis(
            keyword=keyword,
            engine=engine.value,
            total_results=0,
        )

        # Parse organic results
        analysis.organic_results = self._extract_organic_results(soup, engine)
        analysis.total_results = len(analysis.organic_results)

        # Detect SERP features
        analysis.features = self._detect_features(soup, engine)

        # Track domain positions
        if track_domain:
            positions = []
            for result in analysis.organic_results:
                if track_domain.lower() in result.domain.lower():
                    positions.append(result.position)
            analysis.domain_positions = {track_domain: positions}

            # Count brand mentions
            analysis.brand_mentions = sum(
                1 for r in analysis.organic_results
                if track_domain.lower() in r.title.lower() or
                   track_domain.lower() in r.snippet.lower()
            )

        return analysis

    def _extract_organic_results(self, soup, engine: SearchEngine) -> List[SERPResult]:
        """Extract organic search results from SERP HTML."""
        results = []

        if engine == SearchEngine.GOOGLE:
            # Google result containers
            containers = soup.find_all("div", class_="g")
            if not containers:
                # Fallback: find links with h3
                containers = soup.find_all("div", attrs={"data-sokoban-container": True})

            for i, container in enumerate(containers[:100], 1):
                link = container.find("a", href=True)
                title_el = container.find("h3")
                snippet_el = container.find("div", class_="VwiC3b") or \
                            container.find("span", class_="aCOpRe") or \
                            container.find("div", class_=re.compile(r'style-scope'))

                if link and title_el:
                    url = link.get("href", "")
                    if url.startswith("/url?q="):
                        url = url.split("/url?q=")[1].split("&")[0]

                    domain = self._extract_domain(url)
                    results.append(SERPResult(
                        position=i,
                        url=url,
                        title=title_el.get_text(strip=True),
                        snippet=snippet_el.get_text(strip=True) if snippet_el else "",
                        domain=domain,
                    ))
        else:
            # Bing result containers
            containers = soup.find_all("li", class_="b_algo")
            for i, container in enumerate(containers[:100], 1):
                link = container.find("a", href=True)
                title_el = container.find("h2")
                snippet_el = container.find("p")

                if link and title_el:
                    url = link.get("href", "")
                    domain = self._extract_domain(url)
                    results.append(SERPResult(
                        position=i,
                        url=url,
                        title=title_el.get_text(strip=True),
                        snippet=snippet_el.get_text(strip=True) if snippet_el else "",
                        domain=domain,
                    ))

        return results


    def _detect_features(self, soup, engine: SearchEngine) -> SERPFeatures:
        """Detect various SERP features including AI Overview."""
        features = SERPFeatures()

        # AI Overview detection (Google SGE / AI Overview)
        ai_container = soup.find("div", attrs={"data-attrid": re.compile(r'ai|overview', re.I)}) or \
                       soup.find("div", class_=re.compile(r'ai-overview|sge|bard', re.I)) or \
                       soup.find("div", id=re.compile(r'ai-overview', re.I))

        if ai_container:
            features.ai_overview = AIOverview(
                detected=True,
                summary_text=ai_container.get_text(strip=True)[:500],
                cited_sources=[
                    {"url": a.get("href", ""), "title": a.get_text(strip=True)}
                    for a in ai_container.find_all("a", href=True)[:5]
                ],
                cited_domains=[
                    self._extract_domain(a.get("href", ""))
                    for a in ai_container.find_all("a", href=True)[:5]
                ],
            )

        # Featured Snippet detection
        featured = soup.find("div", class_=re.compile(r'featured|kp-blk|xpdopen', re.I)) or \
                   soup.find("div", attrs={"data-tts": True})
        if featured:
            snippet_type = SnippetType.PARAGRAPH
            if featured.find("ol") or featured.find("ul"):
                snippet_type = SnippetType.LIST
            elif featured.find("table"):
                snippet_type = SnippetType.TABLE

            source_link = featured.find("a", href=True)
            features.featured_snippet = FeaturedSnippet(
                detected=True,
                type=snippet_type.value,
                content=featured.get_text(strip=True)[:300],
                source_url=source_link.get("href", "") if source_link else "",
                source_domain=self._extract_domain(source_link.get("href", "")) if source_link else "",
            )

        # People Also Ask
        paa = soup.find_all(class_=re.compile(r'related-question|paa', re.I))
        if not paa:
            paa = soup.find_all(attrs={"data-q": True})
        features.people_also_ask = [
            el.get_text(strip=True) for el in paa[:8]
        ]

        # Other features
        features.knowledge_panel = bool(
            soup.find("div", class_=re.compile(r'knowledge|kp-wholepage', re.I))
        )
        features.local_pack = bool(
            soup.find("div", class_=re.compile(r'local-pack|map', re.I))
        )
        features.video_carousel = bool(
            soup.find("div", class_=re.compile(r'video|carousel', re.I))
        )
        features.image_pack = bool(
            soup.find("div", class_=re.compile(r'image-pack|immersive', re.I))
        )

        return features

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url
