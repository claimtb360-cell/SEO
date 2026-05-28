"""Comprehensive SEO & GEO Analyzer - 80 factors across 10 categories."""

import re
import math
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class FactorResult:
    """Result of a single factor check."""

    def __init__(self, name: str, passed: bool, score: float,
                 message: str, recommendation: str = "", priority: str = "medium"):
        self.name = name
        self.passed = passed
        self.score = score  # 0-100
        self.message = message
        self.recommendation = recommendation
        self.priority = priority  # high, medium, low

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "message": self.message,
            "recommendation": self.recommendation,
            "priority": self.priority,
        }



class CategoryResult:
    """Result for a category of factors."""

    def __init__(self, name: str, factors: List[FactorResult]):
        self.name = name
        self.factors = factors
        self.score = self._calculate_score()

    def _calculate_score(self) -> float:
        if not self.factors:
            return 0.0
        return round(sum(f.score for f in self.factors) / len(self.factors), 1)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "factors": [f.to_dict() for f in self.factors],
            "passed_count": sum(1 for f in self.factors if f.passed),
            "total_count": len(self.factors),
        }



class SEOGEOAnalysisResult:
    """Complete analysis result with all categories."""

    def __init__(self, url: str, categories: Dict[str, CategoryResult]):
        self.url = url
        self.categories = categories
        self.overall_score = self._calculate_overall()
        self.recommendations = self._prioritized_recommendations()

    def _calculate_overall(self) -> float:
        if not self.categories:
            return 0.0
        return round(
            sum(c.score for c in self.categories.values()) / len(self.categories), 1
        )

    def _prioritized_recommendations(self) -> List[dict]:
        recs = []
        priority_order = {"high": 0, "medium": 1, "low": 2}
        for cat_name, cat in self.categories.items():
            for factor in cat.factors:
                if not factor.passed and factor.recommendation:
                    recs.append({
                        "category": cat_name,
                        "factor": factor.name,
                        "recommendation": factor.recommendation,
                        "priority": factor.priority,
                    })
        recs.sort(key=lambda x: priority_order.get(x["priority"], 1))
        return recs

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "overall_score": self.overall_score,
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "recommendations": self.recommendations,
            "total_factors": sum(len(c.factors) for c in self.categories.values()),
            "passed_factors": sum(
                sum(1 for f in c.factors if f.passed)
                for c in self.categories.values()
            ),
        }



class SEOGEOAnalyzer:
    """Comprehensive 80-factor SEO & GEO Analyzer."""

    def __init__(self):
        self.target_keyword: Optional[str] = None

    def analyze(self, html: str, url: str, target_keyword: Optional[str] = None) -> SEOGEOAnalysisResult:
        """Run all 80 factor checks and return comprehensive results."""
        self.target_keyword = target_keyword or ""
        self.soup = BeautifulSoup(html, "html.parser")
        self.html = html
        self.url = url
        self.parsed_url = urlparse(url)
        self.text_content = self.soup.get_text(separator=" ", strip=True)

        categories = {
            "meta_tags": self._check_meta_tags(),
            "open_graph_social": self._check_open_graph(),
            "technical_seo": self._check_technical_seo(),
            "headings_structure": self._check_headings_structure(),
            "content_keywords": self._check_content_keywords(),
            "images_media": self._check_images_media(),
            "links": self._check_links(),
            "schema_structured_data": self._check_schema(),
            "core_web_vitals": self._check_core_web_vitals(),
            "geo_optimization": self._check_geo(),
            "cro_conversion": self._check_cro(),
        }

        return SEOGEOAnalysisResult(url=url, categories=categories)


    # ─── Category 1: Meta Tags (10 factors) ───────────────────────────────

    def _check_meta_tags(self) -> CategoryResult:
        factors = []
        title_tag = self.soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""

        # 1. Title length
        title_len = len(title_text)
        passed = 30 <= title_len <= 60
        score = 100 if passed else (70 if title_len > 0 else 0)
        factors.append(FactorResult(
            "Title Length", passed, score,
            f"Title is {title_len} characters",
            "Keep title between 30-60 characters for optimal display in SERPs.",
            "high"
        ))

        # 2. Title keyword
        has_kw = self.target_keyword.lower() in title_text.lower() if self.target_keyword else True
        factors.append(FactorResult(
            "Title Keyword", has_kw, 100 if has_kw else 30,
            "Target keyword found in title" if has_kw else "Target keyword missing from title",
            "Include your primary keyword near the beginning of the title tag.",
            "high"
        ))

        # 3. Meta description length
        meta_desc = self.soup.find("meta", attrs={"name": "description"})
        desc_text = meta_desc.get("content", "") if meta_desc else ""
        desc_len = len(desc_text)
        passed = 120 <= desc_len <= 160
        score = 100 if passed else (60 if desc_len > 0 else 0)
        factors.append(FactorResult(
            "Meta Description Length", passed, score,
            f"Meta description is {desc_len} characters",
            "Keep meta description between 120-160 characters.",
            "high"
        ))

        # 4. Meta description keyword
        has_kw = self.target_keyword.lower() in desc_text.lower() if self.target_keyword else True
        factors.append(FactorResult(
            "Meta Description Keyword", has_kw, 100 if has_kw else 40,
            "Keyword in meta description" if has_kw else "Keyword missing from description",
            "Include the target keyword naturally in the meta description.",
            "medium"
        ))


        # 5. Canonical URL
        canonical = self.soup.find("link", rel="canonical")
        has_canonical = canonical is not None
        factors.append(FactorResult(
            "Canonical URL", has_canonical, 100 if has_canonical else 20,
            "Canonical URL defined" if has_canonical else "No canonical URL found",
            "Add a canonical link tag to prevent duplicate content issues.",
            "high"
        ))

        # 6. Robots meta
        robots = self.soup.find("meta", attrs={"name": "robots"})
        robots_ok = robots is None or "noindex" not in (robots.get("content", ""))
        factors.append(FactorResult(
            "Robots Meta", robots_ok, 100 if robots_ok else 0,
            "Page is indexable" if robots_ok else "Page is set to noindex",
            "Remove noindex if you want this page indexed by search engines.",
            "high"
        ))

        # 7. Viewport meta
        viewport = self.soup.find("meta", attrs={"name": "viewport"})
        has_viewport = viewport is not None
        factors.append(FactorResult(
            "Viewport Meta", has_viewport, 100 if has_viewport else 0,
            "Viewport meta tag present" if has_viewport else "Missing viewport meta tag",
            "Add <meta name='viewport' content='width=device-width, initial-scale=1'>.",
            "high"
        ))

        # 8. Charset declaration
        charset = self.soup.find("meta", charset=True) or self.soup.find("meta", attrs={"http-equiv": "Content-Type"})
        has_charset = charset is not None
        factors.append(FactorResult(
            "Charset Declaration", has_charset, 100 if has_charset else 30,
            "Charset declared" if has_charset else "No charset declaration found",
            "Add <meta charset='UTF-8'> in the <head>.",
            "medium"
        ))

        # 9. Hreflang tags
        hreflangs = self.soup.find_all("link", rel="alternate", hreflang=True)
        has_hreflang = len(hreflangs) > 0
        factors.append(FactorResult(
            "Hreflang Tags", has_hreflang, 100 if has_hreflang else 50,
            f"{len(hreflangs)} hreflang tags found" if has_hreflang else "No hreflang tags",
            "Add hreflang tags if you have multi-language content.",
            "low"
        ))

        # 10. Language declaration
        html_tag = self.soup.find("html")
        has_lang = html_tag and html_tag.get("lang")
        factors.append(FactorResult(
            "Language Declaration", bool(has_lang), 100 if has_lang else 20,
            f"Language set: {html_tag.get('lang')}" if has_lang else "No lang attribute on <html>",
            "Add lang attribute to the <html> tag (e.g., lang='en').",
            "medium"
        ))

        return CategoryResult("Meta Tags", factors)


    # ─── Category 2: Open Graph & Social (8 factors) ─────────────────────

    def _check_open_graph(self) -> CategoryResult:
        factors = []

        og_tags = {
            "og:title": ("OG Title", "high"),
            "og:description": ("OG Description", "high"),
            "og:image": ("OG Image", "high"),
            "og:url": ("OG URL", "medium"),
            "og:type": ("OG Type", "medium"),
        }

        for prop, (name, priority) in og_tags.items():
            tag = self.soup.find("meta", property=prop)
            has_tag = tag is not None and tag.get("content", "").strip() != ""
            factors.append(FactorResult(
                name, has_tag, 100 if has_tag else 0,
                f"{prop} is set" if has_tag else f"Missing {prop}",
                f"Add {prop} meta tag for better social sharing.",
                priority
            ))

        # Twitter Card tags
        twitter_tags = {
            "twitter:card": ("Twitter Card", "medium"),
            "twitter:title": ("Twitter Title", "low"),
            "twitter:image": ("Twitter Image", "medium"),
        }

        for name_attr, (name, priority) in twitter_tags.items():
            tag = self.soup.find("meta", attrs={"name": name_attr}) or \
                  self.soup.find("meta", property=name_attr)
            has_tag = tag is not None and tag.get("content", "").strip() != ""
            factors.append(FactorResult(
                name, has_tag, 100 if has_tag else 0,
                f"{name_attr} is set" if has_tag else f"Missing {name_attr}",
                f"Add {name_attr} meta tag for Twitter/X sharing.",
                priority
            ))

        return CategoryResult("Open Graph & Social", factors)


    # ─── Category 3: Technical SEO (12 factors) ──────────────────────────

    def _check_technical_seo(self) -> CategoryResult:
        factors = []

        # 1. HTTPS
        is_https = self.parsed_url.scheme == "https"
        factors.append(FactorResult(
            "HTTPS", is_https, 100 if is_https else 0,
            "Site uses HTTPS" if is_https else "Site not using HTTPS",
            "Migrate to HTTPS for security and SEO ranking benefit.",
            "high"
        ))

        # 2. Mixed content
        mixed = bool(re.search(r'(src|href)=["\']http://', self.html)) if is_https else False
        factors.append(FactorResult(
            "No Mixed Content", not mixed, 100 if not mixed else 20,
            "No mixed content detected" if not mixed else "Mixed HTTP/HTTPS content found",
            "Update all resource URLs to use HTTPS.",
            "high"
        ))

        # 3. Redirects (check URL structure)
        clean_url = not self.parsed_url.path.endswith("/index.html")
        factors.append(FactorResult(
            "Clean URL Structure", clean_url, 100 if clean_url else 60,
            "URL structure is clean" if clean_url else "URL has unnecessary index.html",
            "Use clean URL paths without file extensions.",
            "medium"
        ))

        # 4. Robots.txt accessible (signal from meta)
        robots_meta = self.soup.find("meta", attrs={"name": "robots"})
        indexable = robots_meta is None or "noindex" not in robots_meta.get("content", "")
        factors.append(FactorResult(
            "Robots Indexable", indexable, 100 if indexable else 0,
            "Page allows indexing" if indexable else "Page blocks indexing via meta robots",
            "Ensure robots meta allows indexing for public pages.",
            "high"
        ))

        # 5. XML Sitemap reference
        sitemap_link = bool(re.search(r'sitemap', self.html, re.IGNORECASE))
        factors.append(FactorResult(
            "Sitemap Reference", sitemap_link, 100 if sitemap_link else 40,
            "Sitemap reference found" if sitemap_link else "No sitemap reference detected",
            "Reference your XML sitemap in robots.txt and internal links.",
            "medium"
        ))

        # 6. Page speed signal (inline CSS/JS size)
        scripts = self.soup.find_all("script")
        inline_js = sum(len(s.string or "") for s in scripts if not s.get("src"))
        speed_ok = inline_js < 50000
        factors.append(FactorResult(
            "Page Speed Signal", speed_ok, 100 if speed_ok else 40,
            f"Inline JS: {inline_js} chars" if speed_ok else f"Large inline JS: {inline_js} chars",
            "Minimize inline JavaScript and defer non-critical scripts.",
            "high"
        ))


        # 7. Mobile-friendly (viewport presence)
        viewport = self.soup.find("meta", attrs={"name": "viewport"})
        mobile_ok = viewport is not None
        factors.append(FactorResult(
            "Mobile-Friendly", mobile_ok, 100 if mobile_ok else 0,
            "Mobile viewport configured" if mobile_ok else "No mobile viewport",
            "Add viewport meta tag for mobile responsiveness.",
            "high"
        ))

        # 8. Canonical consistency
        canonical = self.soup.find("link", rel="canonical")
        canonical_url = canonical.get("href", "") if canonical else ""
        canon_consistent = canonical_url == self.url or not canonical_url
        factors.append(FactorResult(
            "Canonical Consistency", canon_consistent, 100 if canon_consistent else 50,
            "Canonical matches current URL" if canon_consistent else "Canonical differs from URL",
            "Ensure canonical URL matches the actual page URL.",
            "medium"
        ))

        # 9. URL structure (no special chars)
        url_clean = not bool(re.search(r'[^\w\-/.:?=&%]', self.parsed_url.path))
        factors.append(FactorResult(
            "URL Structure", url_clean, 100 if url_clean else 50,
            "URL uses clean characters" if url_clean else "URL contains special characters",
            "Use only lowercase letters, numbers, and hyphens in URLs.",
            "medium"
        ))

        # 10. 404 handling signal (no broken internal links in page)
        internal_links = [a.get("href", "") for a in self.soup.find_all("a", href=True)
                         if a.get("href", "").startswith("/")]
        no_hash_only = all(l != "#" for l in internal_links)
        factors.append(FactorResult(
            "Internal Link Quality", no_hash_only, 100 if no_hash_only else 60,
            "No placeholder links" if no_hash_only else "Found # placeholder links",
            "Replace placeholder # links with real internal URLs.",
            "medium"
        ))

        # 11. Server response (HTML size as proxy)
        html_size = len(self.html.encode("utf-8", errors="ignore"))
        size_ok = html_size < 500000  # 500KB
        factors.append(FactorResult(
            "Response Size", size_ok, 100 if size_ok else 40,
            f"HTML size: {html_size // 1024}KB",
            "Keep HTML document under 500KB for fast loading.",
            "medium"
        ))

        # 12. Compression signal (check for preload/prefetch hints)
        has_preload = bool(self.soup.find("link", rel="preload"))
        factors.append(FactorResult(
            "Resource Hints", has_preload, 100 if has_preload else 50,
            "Resource preload hints found" if has_preload else "No resource preload hints",
            "Add preload hints for critical CSS/fonts to improve load time.",
            "low"
        ))

        return CategoryResult("Technical SEO", factors)


    # ─── Category 4: Headings & Structure (8 factors) ────────────────────

    def _check_headings_structure(self) -> CategoryResult:
        factors = []
        h1s = self.soup.find_all("h1")
        h2s = self.soup.find_all("h2")
        h3s = self.soup.find_all("h3")
        h4s = self.soup.find_all("h4")
        h5s = self.soup.find_all("h5")
        h6s = self.soup.find_all("h6")

        # 1. H1 presence
        has_h1 = len(h1s) >= 1
        factors.append(FactorResult(
            "H1 Presence", has_h1, 100 if has_h1 else 0,
            f"{len(h1s)} H1 tag(s) found" if has_h1 else "No H1 tag found",
            "Every page should have exactly one H1 tag.",
            "high"
        ))

        # 2. H1 count (exactly one)
        single_h1 = len(h1s) == 1
        factors.append(FactorResult(
            "Single H1", single_h1, 100 if single_h1 else 50,
            "Exactly one H1" if single_h1 else f"{len(h1s)} H1 tags (should be 1)",
            "Use only one H1 tag per page for clear hierarchy.",
            "medium"
        ))

        # 3. Heading hierarchy (H2 follows H1, etc.)
        all_headings = self.soup.find_all(re.compile(r'^h[1-6]$'))
        hierarchy_ok = True
        prev_level = 0
        for h in all_headings:
            level = int(h.name[1])
            if level > prev_level + 1 and prev_level > 0:
                hierarchy_ok = False
                break
            prev_level = level
        factors.append(FactorResult(
            "Heading Hierarchy", hierarchy_ok, 100 if hierarchy_ok else 40,
            "Heading levels follow proper hierarchy" if hierarchy_ok else "Heading levels skip (e.g., H1 to H3)",
            "Maintain sequential heading order: H1 > H2 > H3.",
            "medium"
        ))

        # 4. Heading keyword usage
        h1_text = " ".join(h.get_text(strip=True) for h in h1s).lower()
        kw_in_h1 = self.target_keyword.lower() in h1_text if self.target_keyword else True
        factors.append(FactorResult(
            "Keyword in Headings", kw_in_h1, 100 if kw_in_h1 else 30,
            "Keyword in H1" if kw_in_h1 else "Keyword not in H1",
            "Include your target keyword in the H1 heading.",
            "high"
        ))


        # 5. Heading length
        heading_lengths_ok = all(
            len(h.get_text(strip=True)) <= 70 for h in all_headings
        ) if all_headings else True
        factors.append(FactorResult(
            "Heading Length", heading_lengths_ok, 100 if heading_lengths_ok else 60,
            "All headings within optimal length" if heading_lengths_ok else "Some headings too long (>70 chars)",
            "Keep headings concise - under 70 characters.",
            "low"
        ))

        # 6. Content structure depth (has H2 and H3)
        deep_structure = len(h2s) >= 2 and len(h3s) >= 1
        factors.append(FactorResult(
            "Content Depth", deep_structure, 100 if deep_structure else 40,
            "Good heading depth (H2+H3)" if deep_structure else "Shallow content structure",
            "Use H2 and H3 subheadings to organize content into sections.",
            "medium"
        ))

        # 7. Table of contents presence
        has_toc = bool(self.soup.find(id=re.compile(r'toc|table.of.contents', re.I))) or \
                  bool(self.soup.find(class_=re.compile(r'toc|table.of.contents', re.I)))
        factors.append(FactorResult(
            "Table of Contents", has_toc, 100 if has_toc else 50,
            "TOC detected" if has_toc else "No table of contents found",
            "Add a table of contents for long-form content (>1500 words).",
            "low"
        ))

        # 8. Breadcrumbs
        has_breadcrumb = bool(self.soup.find(class_=re.compile(r'breadcrumb', re.I))) or \
                         bool(self.soup.find(attrs={"aria-label": re.compile(r'breadcrumb', re.I)}))
        factors.append(FactorResult(
            "Breadcrumbs", has_breadcrumb, 100 if has_breadcrumb else 40,
            "Breadcrumb navigation found" if has_breadcrumb else "No breadcrumbs detected",
            "Add breadcrumb navigation for better UX and structured data.",
            "medium"
        ))

        return CategoryResult("Headings & Structure", factors)


    # ─── Category 5: Content & Keywords (10 factors) ─────────────────────

    def _check_content_keywords(self) -> CategoryResult:
        factors = []
        words = self.text_content.split()
        word_count = len(words)

        # 1. Word count
        good_wc = word_count >= 300
        factors.append(FactorResult(
            "Word Count", good_wc, 100 if word_count >= 1000 else (70 if good_wc else 20),
            f"{word_count} words",
            "Aim for at least 1000 words for comprehensive content.",
            "high"
        ))

        # 2. Keyword density
        if self.target_keyword and word_count > 0:
            kw_count = self.text_content.lower().count(self.target_keyword.lower())
            density = (kw_count / word_count) * 100
            good_density = 0.5 <= density <= 3.0
            factors.append(FactorResult(
                "Keyword Density", good_density,
                100 if good_density else (50 if density > 0 else 0),
                f"Keyword density: {density:.1f}%",
                "Maintain keyword density between 0.5-3%.",
                "medium"
            ))
        else:
            factors.append(FactorResult(
                "Keyword Density", True, 70,
                "No target keyword specified",
                "Specify a target keyword for density analysis.",
                "medium"
            ))

        # 3. Keyword in first 100 words
        first_100 = " ".join(words[:100]).lower()
        kw_early = self.target_keyword.lower() in first_100 if self.target_keyword else True
        factors.append(FactorResult(
            "Keyword in First 100 Words", kw_early, 100 if kw_early else 30,
            "Keyword appears early" if kw_early else "Keyword not in first 100 words",
            "Include target keyword in the first 100 words of content.",
            "high"
        ))

        # 4. Keyword in last paragraph
        paragraphs = self.soup.find_all("p")
        last_p = paragraphs[-1].get_text(strip=True).lower() if paragraphs else ""
        kw_end = self.target_keyword.lower() in last_p if self.target_keyword else True
        factors.append(FactorResult(
            "Keyword in Last Paragraph", kw_end, 100 if kw_end else 50,
            "Keyword in conclusion" if kw_end else "Keyword missing from last paragraph",
            "Reinforce the keyword in the concluding paragraph.",
            "low"
        ))


        # 5. LSI keywords (related terms presence)
        has_variety = len(set(w.lower() for w in words if len(w) > 4)) > 50
        factors.append(FactorResult(
            "LSI Keywords / Variety", has_variety, 100 if has_variety else 40,
            "Good vocabulary diversity" if has_variety else "Limited vocabulary diversity",
            "Use semantically related terms and synonyms throughout content.",
            "medium"
        ))

        # 6. Readability score (simple Flesch approximation)
        sentences = re.split(r'[.!?]+', self.text_content)
        sentence_count = max(len([s for s in sentences if s.strip()]), 1)
        avg_sentence_len = word_count / sentence_count
        syllable_count = sum(self._count_syllables(w) for w in words)
        avg_syllables = syllable_count / max(word_count, 1)
        flesch = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables)
        flesch = max(0, min(100, flesch))
        readable = flesch >= 50
        factors.append(FactorResult(
            "Readability Score", readable, min(100, max(0, flesch)),
            f"Flesch score: {flesch:.0f} ({'easy' if flesch >= 70 else 'moderate' if flesch >= 50 else 'difficult'})",
            "Aim for Flesch reading ease score of 60+ for general audiences.",
            "medium"
        ))

        # 7. Content uniqueness signals (no duplicate paragraphs)
        p_texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
        unique_ratio = len(set(p_texts)) / max(len(p_texts), 1)
        unique_ok = unique_ratio >= 0.9
        factors.append(FactorResult(
            "Content Uniqueness", unique_ok, 100 if unique_ok else 40,
            f"Content uniqueness: {unique_ratio*100:.0f}%",
            "Ensure all content paragraphs are unique.",
            "high"
        ))

        # 8. Thin content check
        not_thin = word_count >= 300
        factors.append(FactorResult(
            "Not Thin Content", not_thin, 100 if not_thin else 0,
            "Sufficient content depth" if not_thin else "Thin content (<300 words)",
            "Add more substantive content - minimum 300 words per page.",
            "high"
        ))

        # 9. Content freshness signal (date present)
        has_date = bool(re.search(
            r'\d{4}[-/]\d{2}[-/]\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}',
            self.text_content
        ))
        factors.append(FactorResult(
            "Content Freshness Signal", has_date, 100 if has_date else 40,
            "Publication/update date found" if has_date else "No date signal detected",
            "Include publication or last-updated date on content pages.",
            "low"
        ))

        # 10. Internal topic coverage (multiple sections with H2)
        h2_count = len(self.soup.find_all("h2"))
        good_coverage = h2_count >= 3
        factors.append(FactorResult(
            "Topic Coverage", good_coverage, 100 if good_coverage else (60 if h2_count >= 1 else 20),
            f"{h2_count} topic sections (H2 headings)",
            "Cover the topic comprehensively with 3+ subtopic sections.",
            "medium"
        ))

        return CategoryResult("Content & Keywords", factors)

    @staticmethod
    def _count_syllables(word: str) -> int:
        word = word.lower().strip(".,!?;:'\"")
        if not word:
            return 1
        count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e'):
            count -= 1
        return max(count, 1)


    # ─── Category 6: Images & Media (8 factors) ──────────────────────────

    def _check_images_media(self) -> CategoryResult:
        factors = []
        images = self.soup.find_all("img")
        img_count = len(images)

        # 1. Alt text presence
        imgs_with_alt = [img for img in images if img.get("alt", "").strip()]
        alt_ratio = len(imgs_with_alt) / max(img_count, 1)
        alt_ok = alt_ratio >= 0.9
        factors.append(FactorResult(
            "Alt Text Presence", alt_ok, round(alt_ratio * 100),
            f"{len(imgs_with_alt)}/{img_count} images have alt text",
            "Add descriptive alt text to all informative images.",
            "high"
        ))

        # 2. Image file names
        good_names = sum(1 for img in images if img.get("src") and
                        not re.search(r'IMG_\d+|DSC\d+|image\d+|untitled', img.get("src", ""), re.I))
        name_ratio = good_names / max(img_count, 1)
        factors.append(FactorResult(
            "Descriptive File Names", name_ratio >= 0.8, round(name_ratio * 100),
            f"{good_names}/{img_count} images have descriptive names",
            "Use descriptive, keyword-rich file names for images.",
            "medium"
        ))

        # 3. Image size optimization (check for width/height > 2000 in src name)
        oversized = sum(1 for img in images if img.get("src") and
                       re.search(r'(\d{4,})x(\d{4,})', img.get("src", "")))
        size_ok = oversized == 0
        factors.append(FactorResult(
            "Image Size Optimization", size_ok, 100 if size_ok else 40,
            "No obviously oversized images" if size_ok else f"{oversized} potentially oversized images",
            "Optimize image dimensions and file sizes for web.",
            "high"
        ))

        # 4. Lazy loading
        lazy_imgs = [img for img in images if img.get("loading") == "lazy"]
        lazy_ratio = len(lazy_imgs) / max(img_count, 1) if img_count > 3 else 1.0
        factors.append(FactorResult(
            "Lazy Loading", lazy_ratio >= 0.5, round(lazy_ratio * 100),
            f"{len(lazy_imgs)}/{img_count} images use lazy loading",
            "Add loading='lazy' to below-fold images.",
            "medium"
        ))


        # 5. Modern format (WebP/AVIF)
        modern_imgs = sum(1 for img in images if img.get("src") and
                         re.search(r'\.(webp|avif)', img.get("src", ""), re.I))
        picture_tags = len(self.soup.find_all("picture"))
        modern_ok = modern_imgs > 0 or picture_tags > 0 or img_count == 0
        factors.append(FactorResult(
            "Modern Image Format", modern_ok, 100 if modern_ok else 30,
            "Modern formats (WebP/AVIF) used" if modern_ok else "No modern image formats detected",
            "Convert images to WebP or AVIF for smaller file sizes.",
            "medium"
        ))

        # 6. Image dimensions specified
        dims_specified = sum(1 for img in images if img.get("width") and img.get("height"))
        dims_ratio = dims_specified / max(img_count, 1)
        factors.append(FactorResult(
            "Dimensions Specified", dims_ratio >= 0.8, round(dims_ratio * 100),
            f"{dims_specified}/{img_count} images have explicit dimensions",
            "Specify width and height attributes to prevent layout shift.",
            "medium"
        ))

        # 7. Decorative vs informative
        decorative_ok = all(
            img.get("alt") != "" or img.get("role") == "presentation" or img.get("aria-hidden") == "true"
            for img in images
        )
        factors.append(FactorResult(
            "Decorative Handling", decorative_ok, 100 if decorative_ok else 60,
            "Decorative images properly marked" if decorative_ok else "Some images missing alt or aria markup",
            "Mark decorative images with alt='' and role='presentation'.",
            "low"
        ))

        # 8. Image count ratio
        words = len(self.text_content.split())
        good_ratio = img_count >= 1 and (words / max(img_count, 1)) <= 500
        factors.append(FactorResult(
            "Image to Text Ratio", good_ratio or img_count == 0, 100 if good_ratio else 50,
            f"{img_count} images for {words} words",
            "Use at least 1 image per 300-500 words for engagement.",
            "low"
        ))

        return CategoryResult("Images & Media", factors)


    # ─── Category 7: Links (8 factors) ───────────────────────────────────

    def _check_links(self) -> CategoryResult:
        factors = []
        all_links = self.soup.find_all("a", href=True)
        hrefs = [a.get("href", "") for a in all_links]

        internal = [h for h in hrefs if h.startswith("/") or self.parsed_url.netloc in h]
        external = [h for h in hrefs if h.startswith("http") and self.parsed_url.netloc not in h]

        # 1. Internal link count
        good_internal = len(internal) >= 3
        factors.append(FactorResult(
            "Internal Links", good_internal, 100 if good_internal else 30,
            f"{len(internal)} internal links found",
            "Include at least 3-5 internal links per page.",
            "high"
        ))

        # 2. External link count
        has_external = len(external) >= 1
        factors.append(FactorResult(
            "External Links", has_external, 100 if has_external else 40,
            f"{len(external)} external links found",
            "Link to authoritative external sources to build trust.",
            "medium"
        ))

        # 3. Broken link signals (empty or javascript: links)
        broken_signals = [h for h in hrefs if h in ("", "#", "javascript:void(0)", "javascript:;")]
        no_broken = len(broken_signals) == 0
        factors.append(FactorResult(
            "No Broken Links", no_broken, 100 if no_broken else 40,
            "No broken link patterns" if no_broken else f"{len(broken_signals)} potential broken links",
            "Replace placeholder links with valid URLs.",
            "high"
        ))

        # 4. Nofollow usage
        nofollow_links = [a for a in all_links if "nofollow" in a.get("rel", [])]
        nofollow_ok = len(nofollow_links) <= len(all_links) * 0.5
        factors.append(FactorResult(
            "Nofollow Balance", nofollow_ok, 100 if nofollow_ok else 50,
            f"{len(nofollow_links)} nofollow links",
            "Use nofollow sparingly - only for untrusted or sponsored links.",
            "low"
        ))

        # 5. Anchor text diversity
        anchor_texts = [a.get_text(strip=True).lower() for a in all_links if a.get_text(strip=True)]
        unique_anchors = len(set(anchor_texts))
        diversity = unique_anchors / max(len(anchor_texts), 1)
        factors.append(FactorResult(
            "Anchor Text Diversity", diversity >= 0.5, round(diversity * 100),
            f"{unique_anchors} unique anchor texts from {len(anchor_texts)} links",
            "Vary anchor text - avoid repeating the same link text.",
            "medium"
        ))

        # 6. Deep linking
        deep_links = [h for h in internal if h.count("/") >= 2]
        has_deep = len(deep_links) >= 1
        factors.append(FactorResult(
            "Deep Linking", has_deep, 100 if has_deep else 40,
            f"{len(deep_links)} deep internal links" if has_deep else "No deep internal links",
            "Link to deeper pages, not just the homepage.",
            "medium"
        ))

        # 7. Orphan page signal (has incoming context)
        nav_links = self.soup.find("nav")
        has_nav = nav_links is not None
        factors.append(FactorResult(
            "Navigation Context", has_nav, 100 if has_nav else 30,
            "Navigation element present" if has_nav else "No <nav> element found",
            "Include navigation to prevent orphan pages.",
            "medium"
        ))

        # 8. Link juice distribution
        link_count = len(all_links)
        good_distribution = 5 <= link_count <= 150
        factors.append(FactorResult(
            "Link Distribution", good_distribution, 100 if good_distribution else 50,
            f"{link_count} total links on page",
            "Keep total links between 5-150 per page for optimal link equity.",
            "low"
        ))

        return CategoryResult("Links", factors)


    # ─── Category 8: Schema & Structured Data (6 factors) ────────────────

    def _check_schema(self) -> CategoryResult:
        factors = []

        # Find JSON-LD scripts
        json_ld_scripts = self.soup.find_all("script", type="application/ld+json")

        # 1. JSON-LD presence
        has_jsonld = len(json_ld_scripts) > 0
        factors.append(FactorResult(
            "JSON-LD Presence", has_jsonld, 100 if has_jsonld else 0,
            f"{len(json_ld_scripts)} JSON-LD blocks found" if has_jsonld else "No structured data",
            "Add JSON-LD structured data for rich search results.",
            "high"
        ))

        # 2. Schema type appropriateness
        schema_types = []
        for script in json_ld_scripts:
            content = script.string or ""
            types = re.findall(r'"@type"\s*:\s*"([^"]+)"', content)
            schema_types.extend(types)
        has_type = len(schema_types) > 0
        factors.append(FactorResult(
            "Schema Types", has_type, 100 if has_type else 0,
            f"Types: {', '.join(schema_types[:5])}" if has_type else "No schema types found",
            "Use appropriate schema types (Article, Product, FAQPage, etc.).",
            "high"
        ))

        # 3. Required fields filled
        has_name_or_title = any(
            re.search(r'"(name|headline)"\s*:', s.string or "") for s in json_ld_scripts
        ) if json_ld_scripts else False
        factors.append(FactorResult(
            "Required Fields", has_name_or_title, 100 if has_name_or_title else 0,
            "Required fields present" if has_name_or_title else "Missing required schema fields",
            "Include name/headline, description, and image in schema.",
            "high"
        ))

        # 4. Nested schema
        has_nested = any(
            re.search(r'"@type"\s*:.*"@type"\s*:', s.string or "", re.DOTALL)
            for s in json_ld_scripts
        ) if json_ld_scripts else False
        factors.append(FactorResult(
            "Nested Schema", has_nested, 100 if has_nested else 50,
            "Nested schema objects found" if has_nested else "No nested schema",
            "Use nested schemas (e.g., author within Article) for richer data.",
            "low"
        ))

        # 5. Breadcrumb schema
        has_breadcrumb_schema = any(
            "BreadcrumbList" in (s.string or "") for s in json_ld_scripts
        )
        factors.append(FactorResult(
            "Breadcrumb Schema", has_breadcrumb_schema, 100 if has_breadcrumb_schema else 40,
            "BreadcrumbList schema present" if has_breadcrumb_schema else "No breadcrumb schema",
            "Add BreadcrumbList schema for breadcrumb rich results.",
            "medium"
        ))

        # 6. FAQ/HowTo schema
        has_faq = any(
            re.search(r'FAQ|HowTo', s.string or "") for s in json_ld_scripts
        )
        factors.append(FactorResult(
            "FAQ/HowTo Schema", has_faq, 100 if has_faq else 40,
            "FAQ or HowTo schema found" if has_faq else "No FAQ/HowTo schema",
            "Add FAQPage or HowTo schema for enhanced SERP display.",
            "medium"
        ))

        return CategoryResult("Schema & Structured Data", factors)


    # ─── Category 9: Core Web Vitals (6 factors) ─────────────────────────

    def _check_core_web_vitals(self) -> CategoryResult:
        factors = []

        # Estimate LCP (Largest Contentful Paint) from content
        images = self.soup.find_all("img")
        hero_img = any(img for img in images if img.get("src") and
                      ("hero" in img.get("class", []) or "hero" in img.get("src", "")))
        large_text = len(self.soup.find_all(re.compile(r'^h[12]$'))) > 0
        lcp_score = 80 if (not hero_img or large_text) else 60
        factors.append(FactorResult(
            "LCP Estimate", lcp_score >= 70, lcp_score,
            f"LCP estimate: {'Good' if lcp_score >= 70 else 'Needs improvement'}",
            "Optimize largest element load - preload hero images, use CDN.",
            "high"
        ))

        # INP (Interaction to Next Paint) - check JS load
        scripts = self.soup.find_all("script", src=True)
        async_scripts = sum(1 for s in scripts if s.get("async") or s.get("defer"))
        script_ratio = async_scripts / max(len(scripts), 1)
        inp_score = round(60 + script_ratio * 40)
        factors.append(FactorResult(
            "INP Estimate", inp_score >= 70, inp_score,
            f"INP estimate: {inp_score}/100 ({async_scripts}/{len(scripts)} async/defer)",
            "Use async/defer for scripts to improve interactivity.",
            "high"
        ))

        # CLS (Cumulative Layout Shift) - images without dimensions
        imgs_no_dims = sum(1 for img in images if not (img.get("width") and img.get("height")))
        cls_score = max(0, 100 - imgs_no_dims * 15)
        factors.append(FactorResult(
            "CLS Estimate", cls_score >= 70, cls_score,
            f"CLS risk: {imgs_no_dims} images without dimensions",
            "Add width/height to all images and use aspect-ratio CSS.",
            "high"
        ))

        # FCP (First Contentful Paint) - inline critical CSS
        style_tags = self.soup.find_all("style")
        has_inline_css = len(style_tags) > 0
        preload_css = bool(self.soup.find("link", rel="preload", attrs={"as": "style"}))
        fcp_score = 85 if has_inline_css else (70 if preload_css else 50)
        factors.append(FactorResult(
            "FCP Estimate", fcp_score >= 70, fcp_score,
            f"FCP signals: {'inline CSS found' if has_inline_css else 'no inline critical CSS'}",
            "Inline critical CSS and preload key stylesheets.",
            "medium"
        ))

        # TTFB (Time to First Byte) - HTML size proxy
        html_kb = len(self.html.encode("utf-8", errors="ignore")) / 1024
        ttfb_score = 90 if html_kb < 100 else (70 if html_kb < 300 else 40)
        factors.append(FactorResult(
            "TTFB Estimate", ttfb_score >= 70, ttfb_score,
            f"HTML size: {html_kb:.0f}KB (affects TTFB)",
            "Keep HTML small, use server-side caching for fast TTFB.",
            "medium"
        ))

        # Total Blocking Time - render-blocking resources
        blocking_css = self.soup.find_all("link", rel="stylesheet")
        blocking_js = [s for s in self.soup.find_all("script", src=True)
                      if not s.get("async") and not s.get("defer")]
        blocking_count = len(blocking_css) + len(blocking_js)
        tbt_score = max(0, 100 - blocking_count * 10)
        factors.append(FactorResult(
            "TBT Estimate", tbt_score >= 60, tbt_score,
            f"{blocking_count} render-blocking resources",
            "Defer non-critical CSS/JS to reduce total blocking time.",
            "high"
        ))

        return CategoryResult("Core Web Vitals", factors)


    # ─── Category 10: GEO - Generative Engine Optimization (8 factors) ───

    def _check_geo(self) -> CategoryResult:
        factors = []
        paragraphs = self.soup.find_all("p")
        p_texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]

        # 1. Citability score
        quotable = [p for p in p_texts if 20 <= len(p.split()) <= 50 and not p.endswith("?")]
        cite_ratio = len(quotable) / max(len(p_texts), 1)
        cite_score = min(100, round(cite_ratio * 150))
        factors.append(FactorResult(
            "Citability Score", cite_score >= 60, cite_score,
            f"{len(quotable)} quotable statements found",
            "Write clear, self-contained statements that AI can cite directly.",
            "high"
        ))

        # 2. Direct answer presence
        has_direct = any(
            re.search(r'^([\w\s]+)\s+(is|are|was|were|means|refers to|defined as)', p)
            for p in p_texts[:10]
        )
        factors.append(FactorResult(
            "Direct Answer Presence", has_direct, 100 if has_direct else 20,
            "Direct definition/answer found" if has_direct else "No clear direct answers detected",
            "Start key sections with direct answers: 'X is...' or 'X refers to...'.",
            "high"
        ))

        # 3. Structured data richness for AI
        json_ld = self.soup.find_all("script", type="application/ld+json")
        lists = self.soup.find_all(["ul", "ol"])
        tables = self.soup.find_all("table")
        richness = len(json_ld) * 30 + len(lists) * 10 + len(tables) * 20
        rich_score = min(100, richness)
        factors.append(FactorResult(
            "Structured Data Richness", rich_score >= 50, rich_score,
            f"Schema: {len(json_ld)}, Lists: {len(lists)}, Tables: {len(tables)}",
            "Add JSON-LD schema, organized lists, and data tables for AI parsing.",
            "high"
        ))

        # 4. Entity clarity
        defined_entities = len(re.findall(
            r'<(strong|b|dfn|abbr)[^>]*>([^<]+)</', self.html
        ))
        entity_score = min(100, defined_entities * 15)
        factors.append(FactorResult(
            "Entity Clarity", entity_score >= 40, entity_score,
            f"{defined_entities} clearly defined entities",
            "Use <strong>, <dfn>, or <abbr> to highlight key entities.",
            "medium"
        ))


        # 5. Source authority signals
        has_author = bool(self.soup.find(class_=re.compile(r'author', re.I))) or \
                     bool(re.search(r'"author"', self.html))
        has_date = bool(self.soup.find("time")) or bool(self.soup.find(class_=re.compile(r'date|published', re.I)))
        has_citations = bool(self.soup.find("cite")) or bool(self.soup.find("blockquote"))
        auth_score = (has_author * 40) + (has_date * 30) + (has_citations * 30)
        factors.append(FactorResult(
            "Source Authority Signals", auth_score >= 60, auth_score,
            f"Author: {'✓' if has_author else '✗'}, Date: {'✓' if has_date else '✗'}, Citations: {'✓' if has_citations else '✗'}",
            "Add author byline, publication date, and source citations.",
            "high"
        ))

        # 6. Factual claims with evidence
        stat_patterns = re.findall(r'\d+%|\d+\s*(million|billion|thousand|percent)', self.text_content, re.I)
        has_sources = bool(re.search(r'(according to|source:|study|research|data from)', self.text_content, re.I))
        fact_score = min(100, len(stat_patterns) * 15 + (30 if has_sources else 0))
        factors.append(FactorResult(
            "Factual Claims + Evidence", fact_score >= 40, fact_score,
            f"{len(stat_patterns)} statistics found, sources: {'yes' if has_sources else 'no'}",
            "Include verifiable statistics with source attributions.",
            "medium"
        ))

        # 7. Concise summary availability
        has_summary = bool(self.soup.find(class_=re.compile(r'summary|tldr|key.?takeaway|excerpt', re.I))) or \
                      bool(self.soup.find("meta", attrs={"name": "description"}))
        factors.append(FactorResult(
            "Concise Summary", has_summary, 100 if has_summary else 20,
            "Summary/TLDR element found" if has_summary else "No concise summary detected",
            "Add a TL;DR or key takeaways section for AI to extract.",
            "medium"
        ))

        # 8. Multi-format content
        has_text = len(p_texts) >= 3
        has_lists = len(lists) >= 1
        has_tables_local = len(tables) >= 1
        has_headings = len(self.soup.find_all(re.compile(r'^h[2-4]$'))) >= 2
        format_count = sum([has_text, has_lists, has_tables_local, has_headings])
        multi_score = round(format_count / 4 * 100)
        factors.append(FactorResult(
            "Multi-Format Content", format_count >= 3, multi_score,
            f"Formats: text={'✓' if has_text else '✗'}, lists={'✓' if has_lists else '✗'}, tables={'✓' if has_tables_local else '✗'}, headings={'✓' if has_headings else '✗'}",
            "Include paragraphs, lists, tables, and clear headings.",
            "medium"
        ))

        return CategoryResult("GEO - Generative Engine Optimization", factors)


    # ─── Category 11: CRO - Conversion (6 factors) ──────────────────────

    def _check_cro(self) -> CategoryResult:
        factors = []

        # 1. CTA presence
        cta_patterns = re.compile(
            r'(sign.?up|get.?started|buy.?now|subscribe|download|try.?free|learn.?more|contact|request)',
            re.I
        )
        buttons = self.soup.find_all(["button", "a"], class_=re.compile(r'btn|button|cta', re.I))
        cta_text_matches = [el for el in self.soup.find_all(["a", "button"])
                           if cta_patterns.search(el.get_text())]
        has_cta = len(buttons) > 0 or len(cta_text_matches) > 0
        factors.append(FactorResult(
            "CTA Presence", has_cta, 100 if has_cta else 0,
            f"{len(buttons) + len(cta_text_matches)} CTA elements found",
            "Add clear call-to-action buttons with action-oriented text.",
            "high"
        ))

        # 2. Above-fold content (check first elements)
        first_heading = self.soup.find(re.compile(r'^h[12]$'))
        first_p = self.soup.find("p")
        has_above_fold = first_heading is not None and first_p is not None
        factors.append(FactorResult(
            "Above-Fold Content", has_above_fold, 100 if has_above_fold else 30,
            "Heading and content in upper section" if has_above_fold else "Missing above-fold content",
            "Ensure key message is visible without scrolling.",
            "high"
        ))

        # 3. Form accessibility
        forms = self.soup.find_all("form")
        labels = self.soup.find_all("label")
        form_ok = len(forms) == 0 or len(labels) >= len(forms)
        factors.append(FactorResult(
            "Form Accessibility", form_ok, 100 if form_ok else 40,
            f"{len(forms)} forms, {len(labels)} labels",
            "Add proper labels to all form inputs for accessibility.",
            "medium"
        ))

        # 4. Trust signals
        trust_patterns = re.compile(r'(secure|guarantee|certified|verified|trusted|ssl|privacy)', re.I)
        trust_elements = len(trust_patterns.findall(self.text_content))
        has_trust = trust_elements >= 2
        factors.append(FactorResult(
            "Trust Signals", has_trust, 100 if has_trust else 30,
            f"{trust_elements} trust signals found",
            "Add trust badges, security mentions, and guarantees.",
            "medium"
        ))

        # 5. Social proof
        social_patterns = re.compile(r'(testimonial|review|rating|customer|client|star|★)', re.I)
        social_elements = len(social_patterns.findall(self.html))
        has_social = social_elements >= 2
        factors.append(FactorResult(
            "Social Proof", has_social, 100 if has_social else 20,
            f"{social_elements} social proof elements",
            "Add testimonials, reviews, ratings, or client logos.",
            "medium"
        ))

        # 6. Value proposition
        h1 = self.soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""
        has_value_prop = len(h1_text) > 10 and len(h1_text) < 100
        factors.append(FactorResult(
            "Clear Value Proposition", has_value_prop, 100 if has_value_prop else 30,
            f"H1: '{h1_text[:50]}...'" if h1_text else "No H1 value proposition",
            "Craft a compelling H1 that communicates your unique value.",
            "high"
        ))

        return CategoryResult("CRO - Conversion", factors)
