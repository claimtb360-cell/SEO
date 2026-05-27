"""Basic tests for SEO analyzers."""

import pytest
from src.analyzers.meta_analyzer import MetaAnalyzer
from src.analyzers.heading_analyzer import HeadingAnalyzer
from src.analyzers.content_analyzer import ContentAnalyzer
from src.analyzers.link_analyzer import LinkAnalyzer
from src.analyzers.image_analyzer import ImageAnalyzer


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Page - SEO Tool Testing</title>
    <meta name="description" content="This is a test page for SEO tool analysis. It contains various SEO elements for validation purposes.">
    <link rel="canonical" href="https://example.com/test">
    <meta property="og:title" content="Test Page">
    <meta property="og:description" content="Test description">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:url" content="https://example.com/test">
    <meta property="og:type" content="website">
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a paragraph with enough content to test word count and readability analysis features.</p>
    <h2>Sub Heading One</h2>
    <p>Another paragraph with some more text content for analysis.</p>
    <h2>Sub Heading Two</h2>
    <p>Yet another paragraph to increase the word count.</p>
    <a href="/internal-link">Internal Link</a>
    <a href="https://external.com">External Link</a>
    <img src="/image.jpg" alt="Test image" width="800" height="600">
    <img src="/no-alt.jpg">
</body>
</html>"""


class TestMetaAnalyzer:
    def test_title_detection(self):
        analyzer = MetaAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.title == "Test Page - SEO Tool Testing"
        assert result.title_length > 0

    def test_description_detection(self):
        analyzer = MetaAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.description is not None
        assert "test page" in result.description.lower()

    def test_canonical_detection(self):
        analyzer = MetaAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.canonical == "https://example.com/test"

    def test_og_tags_detection(self):
        analyzer = MetaAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert len(result.og_tags) >= 4

    def test_score_is_valid(self):
        analyzer = MetaAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert 0 <= result.score <= 100


class TestHeadingAnalyzer:
    def test_h1_detection(self):
        analyzer = HeadingAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.h1_count == 1

    def test_heading_hierarchy(self):
        analyzer = HeadingAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.hierarchy_valid is True

    def test_total_headings(self):
        analyzer = HeadingAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.total_headings == 3  # 1 h1 + 2 h2

    def test_missing_h1(self):
        html_no_h1 = "<html><body><h2>Only H2</h2></body></html>"
        analyzer = HeadingAnalyzer()
        result = analyzer.analyze(html_no_h1, "https://example.com")
        assert result.h1_count == 0
        assert any(i.severity == "error" for i in result.issues)


class TestContentAnalyzer:
    def test_word_count(self):
        analyzer = ContentAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.word_count > 0

    def test_readability_score(self):
        analyzer = ContentAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert 0 <= result.readability_score <= 100

    def test_keyword_extraction(self):
        analyzer = ContentAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert len(result.top_keywords) > 0

    def test_keyword_density(self):
        analyzer = ContentAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test", "test")
        assert "test" in result.keyword_density


class TestLinkAnalyzer:
    def test_link_count(self):
        analyzer = LinkAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.total_links == 2

    def test_internal_external_split(self):
        analyzer = LinkAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.internal_links >= 1
        assert result.external_links >= 1


class TestImageAnalyzer:
    def test_image_count(self):
        analyzer = ImageAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.total_images == 2

    def test_missing_alt(self):
        analyzer = ImageAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert result.images_without_alt >= 1

    def test_score(self):
        analyzer = ImageAnalyzer()
        result = analyzer.analyze(SAMPLE_HTML, "https://example.com/test")
        assert 0 <= result.score <= 100
