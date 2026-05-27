"""Image analyzer - checks alt text, optimization, lazy loading."""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from src.utils.html_parser import HtmlParser


@dataclass
class ImageIssue:
    severity: str
    message: str
    image_src: str = ""
    suggestion: str = ""


@dataclass
class ImageAnalysisResult:
    url: str
    total_images: int = 0
    images_without_alt: int = 0
    images_with_empty_alt: int = 0
    images_with_lazy_loading: int = 0
    images_without_dimensions: int = 0
    images: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[ImageIssue] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "total_images": self.total_images,
            "images_without_alt": self.images_without_alt,
            "images_with_empty_alt": self.images_with_empty_alt,
            "images_with_lazy_loading": self.images_with_lazy_loading,
            "images_without_dimensions": self.images_without_dimensions,
            "issues": [{"severity": i.severity, "message": i.message, "image_src": i.image_src, "suggestion": i.suggestion} for i in self.issues],
            "score": self.score,
        }


class ImageAnalyzer:
    """Analyzes images for SEO and performance best practices."""

    def analyze(self, html: str, url: str) -> ImageAnalysisResult:
        """Perform complete image analysis."""
        parser = HtmlParser(html, url)
        images = parser.get_images()

        result = ImageAnalysisResult(url=url)
        result.images = images
        result.total_images = len(images)

        for img in images:
            if not img["has_alt"]:
                result.images_without_alt += 1
            elif img["alt"].strip() == "":
                result.images_with_empty_alt += 1

            if img["is_lazy"]:
                result.images_with_lazy_loading += 1

            if not img["width"] and not img["height"]:
                result.images_without_dimensions += 1

        # Run checks
        self._check_alt_text(result, images)
        self._check_lazy_loading(result, images)
        self._check_dimensions(result, images)
        self._check_file_names(result, images)

        result.score = self._calculate_score(result)
        return result

    def _check_alt_text(self, result: ImageAnalysisResult, images: List[Dict]):
        """Check alt text presence and quality."""
        if result.images_without_alt > 0:
            result.issues.append(ImageIssue(
                severity="error",
                message=f"{result.images_without_alt} images missing alt attribute",
                suggestion="Add descriptive alt text to all images for accessibility and SEO.",
            ))

        # Check for overly long alt text
        for img in images:
            if img["has_alt"] and len(img["alt"]) > 125:
                result.issues.append(ImageIssue(
                    severity="info",
                    message=f"Alt text too long ({len(img['alt'])} chars)",
                    image_src=img["src"],
                    suggestion="Keep alt text concise (under 125 characters).",
                ))

        # Check for keyword-stuffed alt text
        for img in images:
            if img["has_alt"] and img["alt"].count(",") > 3:
                result.issues.append(ImageIssue(
                    severity="warning",
                    message="Alt text appears keyword-stuffed",
                    image_src=img["src"],
                    suggestion="Write natural, descriptive alt text instead of keyword lists.",
                ))

    def _check_lazy_loading(self, result: ImageAnalysisResult, images: List[Dict]):
        """Check lazy loading implementation."""
        non_lazy = result.total_images - result.images_with_lazy_loading
        if result.total_images > 5 and non_lazy > 3:
            result.issues.append(ImageIssue(
                severity="info",
                message=f"{non_lazy} images without lazy loading",
                suggestion="Add loading='lazy' to below-the-fold images to improve page speed.",
            ))

    def _check_dimensions(self, result: ImageAnalysisResult, images: List[Dict]):
        """Check image dimension attributes."""
        if result.images_without_dimensions > 0:
            result.issues.append(ImageIssue(
                severity="warning",
                message=f"{result.images_without_dimensions} images without width/height attributes",
                suggestion="Specify width and height to prevent layout shifts (CLS).",
            ))

    def _check_file_names(self, result: ImageAnalysisResult, images: List[Dict]):
        """Check image file naming conventions."""
        bad_names = 0
        for img in images:
            src = img["src"].split("/")[-1].split("?")[0] if img["src"] else ""
            if src and any(pattern in src.lower() for pattern in ["img_", "image", "dsc", "screenshot", "untitled"]):
                bad_names += 1

        if bad_names > 0:
            result.issues.append(ImageIssue(
                severity="info",
                message=f"{bad_names} images with non-descriptive file names",
                suggestion="Use descriptive, keyword-rich file names (e.g., 'blue-widget.jpg' instead of 'IMG_001.jpg').",
            ))

    def _calculate_score(self, result: ImageAnalysisResult) -> float:
        """Calculate image SEO score."""
        score = 100.0
        for issue in result.issues:
            if issue.severity == "error":
                score -= 20
            elif issue.severity == "warning":
                score -= 10
            elif issue.severity == "info":
                score -= 3
        return max(0.0, min(100.0, score))
