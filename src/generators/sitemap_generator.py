"""Sitemap.xml generator from crawled URLs."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

from src.utils.logger import logger


@dataclass
class SitemapEntry:
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None


@dataclass
class SitemapGeneratorResult:
    xml_content: str = ""
    total_urls: int = 0
    file_path: Optional[str] = None
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_urls": self.total_urls,
            "file_path": self.file_path,
            "success": self.success,
            "xml_preview": self.xml_content[:500] if self.xml_content else "",
        }


class SitemapGenerator:
    """Generates sitemap.xml files."""

    VALID_CHANGEFREQ = [
        "always", "hourly", "daily", "weekly", "monthly", "yearly", "never"
    ]

    def generate(
        self,
        urls: List[SitemapEntry],
        output_path: Optional[str] = None,
    ) -> SitemapGeneratorResult:
        """Generate sitemap.xml from list of URLs."""
        result = SitemapGeneratorResult()

        urlset = ET.Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        for entry in urls:
            url_elem = ET.SubElement(urlset, "url")
            loc = ET.SubElement(url_elem, "loc")
            loc.text = entry.loc

            if entry.lastmod:
                lastmod = ET.SubElement(url_elem, "lastmod")
                lastmod.text = entry.lastmod

            if entry.changefreq and entry.changefreq in self.VALID_CHANGEFREQ:
                changefreq = ET.SubElement(url_elem, "changefreq")
                changefreq.text = entry.changefreq

            if entry.priority is not None:
                priority = ET.SubElement(url_elem, "priority")
                priority.text = f"{entry.priority:.1f}"

        # Pretty print XML
        rough_string = ET.tostring(urlset, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        xml_content = reparsed.toprettyxml(indent="  ", encoding=None)
        # Remove extra XML declaration if present
        lines = xml_content.split("\n")
        if lines[0].startswith("<?xml"):
            xml_content = "\n".join(lines)
        else:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content

        result.xml_content = xml_content
        result.total_urls = len(urls)
        result.success = True

        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
                result.file_path = output_path
                logger.info(f"Sitemap saved to {output_path} ({len(urls)} URLs)")
            except IOError as e:
                logger.error(f"Failed to save sitemap: {e}")
                result.success = False

        return result

    def generate_from_crawl(
        self,
        crawl_pages: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        default_changefreq: str = "weekly",
        default_priority: float = 0.5,
    ) -> SitemapGeneratorResult:
        """Generate sitemap from crawl results."""
        entries = []
        today = datetime.now().strftime("%Y-%m-%d")

        for page in crawl_pages:
            if page.get("status_code") == 200 and not page.get("error"):
                entry = SitemapEntry(
                    loc=page["url"],
                    lastmod=today,
                    changefreq=default_changefreq,
                    priority=default_priority,
                )
                entries.append(entry)

        return self.generate(entries, output_path)
