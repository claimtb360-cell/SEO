"""Content analyzer - keyword density, readability, word count."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import Counter
import re

from src.utils.html_parser import HtmlParser


@dataclass
class ContentIssue:
    severity: str
    message: str
    suggestion: str = ""


@dataclass
class ContentAnalysisResult:
    url: str
    word_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    avg_sentence_length: float = 0.0
    readability_score: float = 0.0
    readability_grade: str = ""
    keyword_density: Dict[str, float] = field(default_factory=dict)
    top_keywords: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[ContentIssue] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "paragraph_count": self.paragraph_count,
            "avg_sentence_length": self.avg_sentence_length,
            "readability_score": self.readability_score,
            "readability_grade": self.readability_grade,
            "keyword_density": self.keyword_density,
            "top_keywords": self.top_keywords,
            "issues": [
                {"severity": i.severity, "message": i.message, "suggestion": i.suggestion}
                for i in self.issues
            ],
            "score": self.score,
        }



class ContentAnalyzer:
    """Analyzes page content quality for SEO."""

    MIN_WORD_COUNT = 300
    MAX_KEYWORD_DENSITY = 3.0
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "because", "but", "and", "or", "if",
        "while", "about", "up", "it", "its", "this", "that", "these",
        "those", "i", "me", "my", "we", "our", "you", "your", "he", "him",
        "his", "she", "her", "they", "them", "their", "what", "which", "who",
    }

    def analyze(self, html: str, url: str, target_keyword: Optional[str] = None) -> ContentAnalysisResult:
        """Perform content quality analysis."""
        parser = HtmlParser(html, url)
        text = parser.get_text_content()

        result = ContentAnalysisResult(url=url)
        words = text.split()
        result.word_count = len(words)
        result.sentence_count = self._count_sentences(text)
        result.paragraph_count = len(parser.soup.find_all("p"))
        result.avg_sentence_length = (
            result.word_count / result.sentence_count
            if result.sentence_count > 0 else 0
        )

        # Readability
        result.readability_score = self._calculate_readability(text)
        result.readability_grade = self._get_readability_grade(result.readability_score)

        # Keyword analysis
        result.top_keywords = self._extract_keywords(words)
        if target_keyword:
            density = self._calculate_keyword_density(text, target_keyword)
            result.keyword_density = {target_keyword: density}

        # Run checks
        self._check_word_count(result)
        self._check_readability(result)
        self._check_keyword_density(result, target_keyword)
        self._check_sentence_length(result)

        result.score = self._calculate_score(result)
        return result


    def _count_sentences(self, text: str) -> int:
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    def _calculate_readability(self, text: str) -> float:
        """Simplified Flesch Reading Ease score."""
        words = text.split()
        sentences = self._count_sentences(text)
        if not words or not sentences:
            return 0.0
        syllables = sum(self._count_syllables(w) for w in words)
        asl = len(words) / sentences
        asw = syllables / len(words)
        score = 206.835 - (1.015 * asl) - (84.6 * asw)
        return max(0.0, min(100.0, score))

    def _count_syllables(self, word: str) -> int:
        word = word.lower().strip(".,!?;:")
        if len(word) <= 3:
            return 1
        vowels = "aeiou"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith("e"):
            count -= 1
        return max(1, count)

    def _get_readability_grade(self, score: float) -> str:
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        return "Very Difficult"

    def _extract_keywords(self, words: List[str], top_n: int = 20) -> List[Dict[str, Any]]:
        cleaned = [
            w.lower().strip(".,!?;:\"'()[]{}") for w in words
            if len(w) > 2 and w.lower().strip(".,!?;:\"'()[]{}") not in self.STOP_WORDS
        ]
        counter = Counter(cleaned)
        total = len(cleaned) if cleaned else 1
        return [
            {"keyword": kw, "count": count, "density": round((count / total) * 100, 2)}
            for kw, count in counter.most_common(top_n)
        ]

    def _calculate_keyword_density(self, text: str, keyword: str) -> float:
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        words = text_lower.split()
        count = text_lower.count(keyword_lower)
        total_words = len(words) if words else 1
        keyword_words = len(keyword_lower.split())
        return round((count / (total_words / keyword_words)) * 100, 2)


    def _check_word_count(self, result: ContentAnalysisResult):
        if result.word_count < self.MIN_WORD_COUNT:
            result.issues.append(ContentIssue(
                severity="warning",
                message=f"Low word count ({result.word_count}, recommended > {self.MIN_WORD_COUNT})",
                suggestion="Add more quality content. Longer content tends to rank better.",
            ))
        elif result.word_count > 5000:
            result.issues.append(ContentIssue(
                severity="info",
                message=f"Very long content ({result.word_count} words)",
                suggestion="Consider breaking into multiple pages or adding a table of contents.",
            ))

    def _check_readability(self, result: ContentAnalysisResult):
        if result.readability_score < 30:
            result.issues.append(ContentIssue(
                severity="warning",
                message=f"Content is very difficult to read (score: {result.readability_score:.0f})",
                suggestion="Simplify sentences, use shorter words, and break up paragraphs.",
            ))
        elif result.readability_score < 50:
            result.issues.append(ContentIssue(
                severity="info",
                message=f"Content readability could be improved (score: {result.readability_score:.0f})",
                suggestion="Try to write at a 6th-8th grade reading level for broader audience.",
            ))

    def _check_keyword_density(self, result: ContentAnalysisResult, target_keyword: Optional[str]):
        if target_keyword and target_keyword in result.keyword_density:
            density = result.keyword_density[target_keyword]
            if density > self.MAX_KEYWORD_DENSITY:
                result.issues.append(ContentIssue(
                    severity="warning",
                    message=f"Keyword density too high ({density:.1f}%, max {self.MAX_KEYWORD_DENSITY}%)",
                    suggestion="Reduce keyword usage to avoid over-optimization penalty.",
                ))
            elif density < 0.5:
                result.issues.append(ContentIssue(
                    severity="info",
                    message=f"Keyword density very low ({density:.1f}%)",
                    suggestion="Naturally incorporate the target keyword more in your content.",
                ))

    def _check_sentence_length(self, result: ContentAnalysisResult):
        if result.avg_sentence_length > 25:
            result.issues.append(ContentIssue(
                severity="info",
                message=f"Average sentence length is long ({result.avg_sentence_length:.0f} words)",
                suggestion="Use shorter sentences for better readability and engagement.",
            ))

    def _calculate_score(self, result: ContentAnalysisResult) -> float:
        score = 100.0
        for issue in result.issues:
            if issue.severity == "error":
                score -= 20
            elif issue.severity == "warning":
                score -= 12
            elif issue.severity == "info":
                score -= 5
        return max(0.0, min(100.0, score))
