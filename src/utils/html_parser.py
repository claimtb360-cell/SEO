"""HTML parsing utilities using BeautifulSoup."""

from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


class HtmlParser:
    """HTML parsing utility for SEO analysis."""

    def __init__(self, html: str, base_url: str = ""):
        self.html = html
        self.base_url = base_url
        self.soup = BeautifulSoup(html, "lxml")

    @property
    def title(self) -> Optional[str]:
        """Get page title."""
        tag = self.soup.find("title")
        return tag.get_text(strip=True) if tag else None

    @property
    def meta_description(self) -> Optional[str]:
        """Get meta description."""
        tag = self.soup.find("meta", attrs={"name": "description"})
        return tag.get("content", "").strip() if tag else None

    @property
    def meta_keywords(self) -> Optional[str]:
        """Get meta keywords."""
        tag = self.soup.find("meta", attrs={"name": "keywords"})
        return tag.get("content", "").strip() if tag else None

    @property
    def canonical_url(self) -> Optional[str]:
        """Get canonical URL."""
        tag = self.soup.find("link", attrs={"rel": "canonical"})
        return tag.get("href", "").strip() if tag else None

    @property
    def robots_meta(self) -> Optional[str]:
        """Get robots meta tag content."""
        tag = self.soup.find("meta", attrs={"name": "robots"})
        return tag.get("content", "").strip() if tag else None

    def get_meta_tags(self) -> Dict[str, Any]:
        """Get all relevant meta tags."""
        og_tags = {}
        twitter_tags = {}

        for tag in self.soup.find_all("meta"):
            prop = tag.get("property", "")
            name = tag.get("name", "")
            content = tag.get("content", "")

            if prop.startswith("og:"):
                og_tags[prop] = content
            elif name.startswith("twitter:"):
                twitter_tags[name] = content

        return {
            "title": self.title,
            "description": self.meta_description,
            "keywords": self.meta_keywords,
            "canonical": self.canonical_url,
            "robots": self.robots_meta,
            "og": og_tags,
            "twitter": twitter_tags,
            "viewport": self._get_meta_content("viewport"),
            "charset": self._get_charset(),
        }

    def get_headings(self) -> Dict[str, List[str]]:
        """Get all headings organized by level."""
        headings = {}
        for level in range(1, 7):
            tag_name = f"h{level}"
            tags = self.soup.find_all(tag_name)
            headings[tag_name] = [tag.get_text(strip=True) for tag in tags]
        return headings

    def get_links(self) -> List[Dict[str, Any]]:
        """Get all links with metadata."""
        links = []
        for tag in self.soup.find_all("a", href=True):
            href = tag["href"].strip()
            absolute_url = urljoin(self.base_url, href) if self.base_url else href
            parsed = urlparse(absolute_url)
            base_parsed = urlparse(self.base_url) if self.base_url else None

            is_internal = (
                base_parsed and parsed.netloc == base_parsed.netloc
            ) if base_parsed else href.startswith("/")

            links.append({
                "href": href,
                "absolute_url": absolute_url,
                "text": tag.get_text(strip=True),
                "is_internal": is_internal,
                "is_nofollow": "nofollow" in tag.get("rel", []),
                "target": tag.get("target", ""),
                "title": tag.get("title", ""),
            })
        return links

    def get_images(self) -> List[Dict[str, Any]]:
        """Get all images with metadata."""
        images = []
        for tag in self.soup.find_all("img"):
            src = tag.get("src", "")
            images.append({
                "src": urljoin(self.base_url, src) if self.base_url and src else src,
                "alt": tag.get("alt", ""),
                "title": tag.get("title", ""),
                "width": tag.get("width", ""),
                "height": tag.get("height", ""),
                "loading": tag.get("loading", ""),
                "has_alt": bool(tag.get("alt")),
                "is_lazy": tag.get("loading") == "lazy",
            })
        return images

    def get_text_content(self) -> str:
        """Get cleaned text content of the page."""
        # Remove script and style elements
        for element in self.soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = self.soup.get_text(separator=" ", strip=True)
        # Clean multiple spaces
        return " ".join(text.split())

    def get_word_count(self) -> int:
        """Get word count of main content."""
        return len(self.get_text_content().split())

    def get_structured_data(self) -> List[Dict[str, Any]]:
        """Extract JSON-LD structured data."""
        import json
        structured = []
        for script in self.soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                structured.append(data)
            except (json.JSONDecodeError, TypeError):
                pass
        return structured

    def get_scripts(self) -> List[Dict[str, str]]:
        """Get all script tags."""
        scripts = []
        for tag in self.soup.find_all("script"):
            scripts.append({
                "src": tag.get("src", ""),
                "type": tag.get("type", ""),
                "async": tag.has_attr("async"),
                "defer": tag.has_attr("defer"),
            })
        return scripts

    def get_stylesheets(self) -> List[str]:
        """Get all stylesheet URLs."""
        return [
            link.get("href", "")
            for link in self.soup.find_all("link", rel="stylesheet")
        ]

    def has_viewport_meta(self) -> bool:
        """Check if page has viewport meta tag (mobile-friendly indicator)."""
        return self.soup.find("meta", attrs={"name": "viewport"}) is not None

    def _get_meta_content(self, name: str) -> Optional[str]:
        """Get content of a meta tag by name."""
        tag = self.soup.find("meta", attrs={"name": name})
        return tag.get("content", "").strip() if tag else None

    def _get_charset(self) -> Optional[str]:
        """Get document charset."""
        tag = self.soup.find("meta", charset=True)
        if tag:
            return tag.get("charset", "")
        tag = self.soup.find("meta", attrs={"http-equiv": "Content-Type"})
        if tag:
            content = tag.get("content", "")
            if "charset=" in content:
                return content.split("charset=")[-1].strip()
        return None
