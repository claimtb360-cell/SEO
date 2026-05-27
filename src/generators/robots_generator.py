"""Robots.txt generator."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.utils.logger import logger


@dataclass
class RobotsRule:
    user_agent: str = "*"
    allow: List[str] = field(default_factory=list)
    disallow: List[str] = field(default_factory=list)


@dataclass
class RobotsGeneratorResult:
    content: str = ""
    file_path: Optional[str] = None
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "file_path": self.file_path,
            "success": self.success,
        }


class RobotsGenerator:
    """Generates robots.txt files."""

    def generate(
        self,
        rules: Optional[List[RobotsRule]] = None,
        sitemap_url: Optional[str] = None,
        crawl_delay: Optional[int] = None,
        additional_sitemaps: Optional[List[str]] = None,
        output_path: Optional[str] = None,
    ) -> RobotsGeneratorResult:
        """Generate robots.txt content."""
        result = RobotsGeneratorResult()
        lines = []

        # Use default rules if none provided
        if not rules:
            rules = [RobotsRule(
                user_agent="*",
                allow=["/"],
                disallow=[
                    "/admin/",
                    "/private/",
                    "/api/",
                    "/*.json$",
                    "/wp-admin/",
                    "/search/",
                ],
            )]

        for rule in rules:
            lines.append(f"User-agent: {rule.user_agent}")

            if crawl_delay:
                lines.append(f"Crawl-delay: {crawl_delay}")

            for path in rule.disallow:
                lines.append(f"Disallow: {path}")

            for path in rule.allow:
                lines.append(f"Allow: {path}")

            lines.append("")  # Empty line between rules

        # Add sitemap references
        if sitemap_url:
            lines.append(f"Sitemap: {sitemap_url}")

        if additional_sitemaps:
            for sm in additional_sitemaps:
                lines.append(f"Sitemap: {sm}")

        result.content = "\n".join(lines).strip() + "\n"
        result.success = True

        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result.content)
                result.file_path = output_path
                logger.info(f"robots.txt saved to {output_path}")
            except IOError as e:
                logger.error(f"Failed to save robots.txt: {e}")
                result.success = False

        return result

    def generate_permissive(
        self,
        sitemap_url: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> RobotsGeneratorResult:
        """Generate a permissive robots.txt (allow all)."""
        rules = [RobotsRule(user_agent="*", allow=["/"])]
        return self.generate(rules, sitemap_url, output_path=output_path)

    def generate_restrictive(
        self,
        sitemap_url: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> RobotsGeneratorResult:
        """Generate a restrictive robots.txt (block all)."""
        rules = [RobotsRule(user_agent="*", disallow=["/"])]
        return self.generate(rules, sitemap_url, output_path=output_path)
