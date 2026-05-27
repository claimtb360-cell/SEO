"""Content Testing Module - SEO scoring, plagiarism check, readability, keyword audit, SERP preview."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re

from src.utils.logger import logger
from .providers import get_provider


PLAGIARISM_CHECK_PROMPT = """Analyze this content for originality and potential plagiarism risk:

**Content:**
{content}

Evaluate and return JSON:
{{
    "originality_score": <0-100>,
    "risk_level": "<low/medium/high>",
    "common_phrases_detected": [
        {{"phrase": "<generic/overused phrase>", "suggestion": "<more original alternative>"}}
    ],
    "ai_detection_risk": "<low/medium/high>",
    "humanization_tips": ["<tip to make content sound more natural>"],
    "unique_value_assessment": "<what makes this content unique or not>"
}}"""



SERP_PREVIEW_PROMPT = """Generate a Google SERP preview for this content:

**Title:** {title}
**Meta Description:** {meta_description}
**URL:** {url}
**Content Summary:** {content_summary}

Return JSON:
{{
    "serp_preview": {{
        "title_display": "<how title appears in Google, truncated if needed>",
        "title_length": <int>,
        "title_truncated": <bool>,
        "url_display": "<breadcrumb URL display>",
        "description_display": "<how description appears>",
        "description_length": <int>,
        "description_truncated": <bool>
    }},
    "title_analysis": {{
        "has_keyword": <bool>,
        "has_power_word": <bool>,
        "has_number": <bool>,
        "emotional_appeal": "<low/medium/high>",
        "click_probability": "<low/medium/high>",
        "improvements": ["<suggestion>"]
    }},
    "description_analysis": {{
        "has_keyword": <bool>,
        "has_cta": <bool>,
        "is_compelling": <bool>,
        "improvements": ["<suggestion>"]
    }},
    "featured_snippet_potential": {{
        "eligible": <bool>,
        "type": "<paragraph/list/table/none>",
        "optimization_tip": "<how to optimize for featured snippet>"
    }},
    "rich_results_potential": {{
        "faq_eligible": <bool>,
        "howto_eligible": <bool>,
        "review_eligible": <bool>,
        "structured_data_suggestions": ["<schema type to add>"]
    }}
}}"""


@dataclass
class KeywordPlacement:
    """Analysis of where a keyword appears in content."""
    keyword: str
    total_count: int = 0
    density_percent: float = 0.0
    in_title: bool = False
    in_first_paragraph: bool = False
    in_headings: bool = False
    in_last_paragraph: bool = False
    in_meta_description: bool = False
    in_url_slug: bool = False
    positions: List[str] = field(default_factory=list)
    score: float = 0.0
    suggestions: List[str] = field(default_factory=list)



@dataclass
class ReadabilityReport:
    """Detailed readability analysis."""
    flesch_score: float = 0.0
    grade_level: str = ""
    avg_sentence_length: float = 0.0
    avg_word_length: float = 0.0
    long_sentences: int = 0
    passive_voice_estimate: int = 0
    paragraph_count: int = 0
    short_paragraphs: int = 0
    long_paragraphs: int = 0
    has_bullet_lists: bool = False
    has_numbered_lists: bool = False
    transition_words_count: int = 0
    score: float = 0.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class SEOScoreReport:
    """Comprehensive SEO scoring."""
    overall_score: float = 0.0
    keyword_score: float = 0.0
    readability_score: float = 0.0
    structure_score: float = 0.0
    meta_score: float = 0.0
    engagement_score: float = 0.0
    technical_score: float = 0.0
    breakdown: Dict[str, Any] = field(default_factory=dict)
    pass_fail_checks: List[Dict[str, Any]] = field(default_factory=list)
    priority_fixes: List[str] = field(default_factory=list)


@dataclass
class ContentTestResult:
    """Complete content testing result."""
    # Scores
    seo_score: Optional[SEOScoreReport] = None
    readability: Optional[ReadabilityReport] = None
    keyword_audit: List[KeywordPlacement] = field(default_factory=list)

    # Checks
    plagiarism_check: Dict[str, Any] = field(default_factory=dict)
    serp_preview: Dict[str, Any] = field(default_factory=dict)

    # Summary
    overall_grade: str = ""  # A, B, C, D, F
    publish_ready: bool = False
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)

    # Meta
    model_used: str = ""
    provider_used: str = ""
    generation_time_sec: float = 0.0
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seo_score": {
                "overall": self.seo_score.overall_score,
                "keyword": self.seo_score.keyword_score,
                "readability": self.seo_score.readability_score,
                "structure": self.seo_score.structure_score,
                "meta": self.seo_score.meta_score,
                "engagement": self.seo_score.engagement_score,
                "technical": self.seo_score.technical_score,
                "pass_fail_checks": self.seo_score.pass_fail_checks,
                "priority_fixes": self.seo_score.priority_fixes,
            } if self.seo_score else {},
            "readability": {
                "flesch_score": self.readability.flesch_score,
                "grade_level": self.readability.grade_level,
                "avg_sentence_length": self.readability.avg_sentence_length,
                "long_sentences": self.readability.long_sentences,
                "score": self.readability.score,
                "suggestions": self.readability.suggestions,
            } if self.readability else {},
            "keyword_audit": [
                {
                    "keyword": kp.keyword,
                    "count": kp.total_count,
                    "density": kp.density_percent,
                    "in_title": kp.in_title,
                    "in_first_paragraph": kp.in_first_paragraph,
                    "in_headings": kp.in_headings,
                    "score": kp.score,
                    "suggestions": kp.suggestions,
                } for kp in self.keyword_audit
            ],
            "plagiarism_check": self.plagiarism_check,
            "serp_preview": self.serp_preview,
            "overall_grade": self.overall_grade,
            "publish_ready": self.publish_ready,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "passed_checks": self.passed_checks,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "generation_time_sec": self.generation_time_sec,
            "success": self.success,
            "error": self.error,
        }



class ContentTester:
    """Comprehensive content testing and quality assurance."""

    TRANSITION_WORDS = [
        "however", "therefore", "furthermore", "moreover", "additionally",
        "consequently", "meanwhile", "nevertheless", "in addition",
        "for example", "in contrast", "on the other hand", "as a result",
        "in conclusion", "specifically", "similarly", "likewise",
    ]

    def __init__(self, provider: str = "openai", model_id: str = "gpt-4o-mini"):
        self.provider_name = provider
        self.model_id = model_id

    async def full_test(
        self,
        content: str,
        keyword: str,
        secondary_keywords: str = "",
        meta_title: str = "",
        meta_description: str = "",
        url: str = "",
    ) -> ContentTestResult:
        """Run all content tests."""
        import time
        start = time.time()

        result = ContentTestResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            # 1. SEO Score
            result.seo_score = self._calculate_seo_score(
                content, keyword, secondary_keywords, meta_title, meta_description
            )

            # 2. Readability
            result.readability = self._analyze_readability(content)

            # 3. Keyword Audit
            all_keywords = [keyword]
            if secondary_keywords:
                all_keywords.extend(
                    kw.strip() for kw in secondary_keywords.split(",") if kw.strip()
                )
            for kw in all_keywords:
                placement = self._audit_keyword(content, kw, meta_title, meta_description, url)
                result.keyword_audit.append(placement)

            # 4. Plagiarism Check (AI-based)
            result.plagiarism_check = await self._check_plagiarism(content)

            # 5. SERP Preview
            if meta_title or url:
                result.serp_preview = await self._generate_serp_preview(
                    title=meta_title or self._extract_title(content),
                    meta_description=meta_description or content[:160],
                    url=url or "https://example.com/article",
                    content_summary=content[:500],
                )

            # Calculate overall grade
            self._calculate_overall_grade(result)
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Content test failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    def test_seo_only(
        self,
        content: str,
        keyword: str,
        secondary_keywords: str = "",
        meta_title: str = "",
        meta_description: str = "",
    ) -> ContentTestResult:
        """Run SEO scoring only (no AI calls, instant)."""
        result = ContentTestResult(success=True)
        result.seo_score = self._calculate_seo_score(
            content, keyword, secondary_keywords, meta_title, meta_description
        )
        result.readability = self._analyze_readability(content)

        all_keywords = [keyword]
        if secondary_keywords:
            all_keywords.extend(kw.strip() for kw in secondary_keywords.split(",") if kw.strip())
        for kw in all_keywords:
            result.keyword_audit.append(
                self._audit_keyword(content, kw, meta_title, meta_description, "")
            )

        self._calculate_overall_grade(result)
        return result


    def _calculate_seo_score(
        self, content: str, keyword: str, secondary_keywords: str,
        meta_title: str, meta_description: str,
    ) -> SEOScoreReport:
        """Calculate comprehensive SEO score."""
        report = SEOScoreReport()
        checks = []
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        words = content.split()
        word_count = len(words)

        # --- Keyword Score (25 points) ---
        kw_score = 0.0
        kw_count = content_lower.count(keyword_lower)
        density = (kw_count / word_count * 100) if word_count else 0

        # Keyword in first 100 words
        first_100 = " ".join(words[:100]).lower()
        in_first = keyword_lower in first_100
        if in_first:
            kw_score += 5
            checks.append({"check": "Keyword in first 100 words", "passed": True})
        else:
            checks.append({"check": "Keyword in first 100 words", "passed": False})

        # Keyword in headings
        headings = [l for l in content.split("\n") if l.startswith("## ")]
        in_headings = any(keyword_lower in h.lower() for h in headings)
        if in_headings:
            kw_score += 5
            checks.append({"check": "Keyword in H2 heading", "passed": True})
        else:
            checks.append({"check": "Keyword in H2 heading", "passed": False})

        # Keyword density
        if 1.0 <= density <= 2.5:
            kw_score += 10
            checks.append({"check": f"Keyword density optimal ({density:.1f}%)", "passed": True})
        elif 0.5 <= density < 1.0 or 2.5 < density <= 3.0:
            kw_score += 5
            checks.append({"check": f"Keyword density acceptable ({density:.1f}%)", "passed": True})
        else:
            checks.append({"check": f"Keyword density ({density:.1f}%)", "passed": False})

        # Keyword in meta
        if meta_title and keyword_lower in meta_title.lower():
            kw_score += 5
            checks.append({"check": "Keyword in meta title", "passed": True})
        elif meta_title:
            checks.append({"check": "Keyword in meta title", "passed": False})

        report.keyword_score = min(25.0, kw_score)

        # --- Structure Score (20 points) ---
        struct_score = 0.0
        if headings:
            struct_score += 5
            checks.append({"check": f"Has H2 headings ({len(headings)})", "passed": True})
        else:
            checks.append({"check": "Has H2 headings", "passed": False})

        h3_count = content.count("### ")
        if h3_count > 0:
            struct_score += 3
            checks.append({"check": "Has H3 subheadings", "passed": True})

        if "- " in content or "* " in content:
            struct_score += 4
            checks.append({"check": "Has bullet lists", "passed": True})
        else:
            checks.append({"check": "Has bullet lists", "passed": False})

        if "1. " in content or "1) " in content:
            struct_score += 3

        if word_count >= 1000:
            struct_score += 5
            checks.append({"check": f"Word count sufficient ({word_count})", "passed": True})
        elif word_count >= 500:
            struct_score += 3
            checks.append({"check": f"Word count acceptable ({word_count})", "passed": True})
        else:
            checks.append({"check": f"Word count low ({word_count})", "passed": False})

        report.structure_score = min(20.0, struct_score)

        # --- Meta Score (20 points) ---
        meta_score = 0.0
        if meta_title:
            title_len = len(meta_title)
            if 30 <= title_len <= 60:
                meta_score += 7
                checks.append({"check": f"Meta title length OK ({title_len})", "passed": True})
            else:
                meta_score += 3
                checks.append({"check": f"Meta title length ({title_len}, ideal 30-60)", "passed": False})
        else:
            checks.append({"check": "Has meta title", "passed": False})

        if meta_description:
            desc_len = len(meta_description)
            if 120 <= desc_len <= 160:
                meta_score += 7
                checks.append({"check": f"Meta description length OK ({desc_len})", "passed": True})
            else:
                meta_score += 3
                checks.append({"check": f"Meta description length ({desc_len}, ideal 120-160)", "passed": False})
        else:
            checks.append({"check": "Has meta description", "passed": False})

        if meta_title and keyword_lower in meta_title.lower():
            meta_score += 6

        report.meta_score = min(20.0, meta_score)

        # --- Readability Score (15 points) ---
        sentences = [s for s in re.split(r'[.!?]+', content) if s.strip()]
        avg_sent_len = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        read_score = 0.0
        if avg_sent_len <= 20:
            read_score += 8
        elif avg_sent_len <= 25:
            read_score += 5
        else:
            read_score += 2

        # Transition words
        transitions = sum(1 for tw in self.TRANSITION_WORDS if tw in content_lower)
        if transitions >= 5:
            read_score += 4
        elif transitions >= 2:
            read_score += 2

        # Paragraphs not too long
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        long_paras = sum(1 for p in paragraphs if len(p.split()) > 100)
        if long_paras == 0:
            read_score += 3
        checks.append({"check": f"Avg sentence length ({avg_sent_len:.0f} words)", "passed": avg_sent_len <= 20})

        report.readability_score = min(15.0, read_score)

        # --- Engagement Score (10 points) ---
        eng_score = 0.0
        if "?" in content:
            eng_score += 2  # Questions engage readers
        if "faq" in content_lower or "frequently asked" in content_lower:
            eng_score += 3
            checks.append({"check": "Has FAQ section", "passed": True})
        if any(w in content_lower for w in ["example", "case study", "for instance"]):
            eng_score += 3
        if any(w in content_lower for w in ["you", "your"]):
            eng_score += 2  # Direct address

        report.engagement_score = min(10.0, eng_score)

        # --- Technical Score (10 points) ---
        tech_score = 0.0
        if "](http" in content or "](/" in content:
            tech_score += 4  # Has links
            checks.append({"check": "Has links", "passed": True})
        if "![" in content or "image" in content_lower:
            tech_score += 3  # References images
        if content.startswith("# ") or "# " in content[:200]:
            tech_score += 3  # Has H1
            checks.append({"check": "Has H1 title", "passed": True})

        report.technical_score = min(10.0, tech_score)

        # Overall
        report.overall_score = round(
            report.keyword_score + report.structure_score + report.meta_score +
            report.readability_score + report.engagement_score + report.technical_score, 1
        )
        report.pass_fail_checks = checks

        # Priority fixes
        for check in checks:
            if not check["passed"]:
                report.priority_fixes.append(f"Fix: {check['check']}")

        return report


    def _analyze_readability(self, content: str) -> ReadabilityReport:
        """Analyze content readability in detail."""
        report = ReadabilityReport()

        # Clean content (remove markdown)
        clean = re.sub(r'[#*\[\]()_`>]', '', content)
        sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if s.strip()]
        words = clean.split()
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        report.paragraph_count = len(paragraphs)
        report.short_paragraphs = sum(1 for p in paragraphs if len(p.split()) < 30)
        report.long_paragraphs = sum(1 for p in paragraphs if len(p.split()) > 100)

        if sentences:
            sent_lengths = [len(s.split()) for s in sentences]
            report.avg_sentence_length = round(sum(sent_lengths) / len(sent_lengths), 1)
            report.long_sentences = sum(1 for sl in sent_lengths if sl > 20)

        if words:
            report.avg_word_length = round(sum(len(w) for w in words) / len(words), 1)

        # Flesch Reading Ease approximation
        syllable_count = sum(self._count_syllables(w) for w in words)
        if sentences and words:
            asl = len(words) / len(sentences)
            asw = syllable_count / len(words)
            report.flesch_score = round(206.835 - (1.015 * asl) - (84.6 * asw), 1)
            report.flesch_score = max(0, min(100, report.flesch_score))

        # Grade level
        if report.flesch_score >= 90:
            report.grade_level = "5th grade (Very Easy)"
        elif report.flesch_score >= 80:
            report.grade_level = "6th grade (Easy)"
        elif report.flesch_score >= 70:
            report.grade_level = "7th grade (Fairly Easy)"
        elif report.flesch_score >= 60:
            report.grade_level = "8th-9th grade (Standard)"
        elif report.flesch_score >= 50:
            report.grade_level = "10th-12th grade (Fairly Hard)"
        elif report.flesch_score >= 30:
            report.grade_level = "College (Hard)"
        else:
            report.grade_level = "Professional (Very Hard)"

        # Lists
        report.has_bullet_lists = "- " in content or "* " in content
        report.has_numbered_lists = bool(re.search(r'\d+\. ', content))

        # Transition words
        content_lower = content.lower()
        report.transition_words_count = sum(
            1 for tw in self.TRANSITION_WORDS if tw in content_lower
        )

        # Passive voice estimate (simple heuristic)
        passive_patterns = [" is ", " was ", " were ", " been ", " being ", " are "]
        report.passive_voice_estimate = sum(
            content_lower.count(p + "used")
            + content_lower.count(p + "made")
            + content_lower.count(p + "done")
            + content_lower.count(p + "found")
            for p in passive_patterns
        )

        # Score (0-100)
        score = 50.0
        if report.flesch_score >= 60:
            score += 20
        elif report.flesch_score >= 50:
            score += 10
        if report.avg_sentence_length <= 18:
            score += 10
        if report.long_sentences <= 3:
            score += 10
        if report.has_bullet_lists or report.has_numbered_lists:
            score += 5
        if report.transition_words_count >= 5:
            score += 5
        report.score = min(100.0, score)

        # Suggestions
        if report.avg_sentence_length > 20:
            report.suggestions.append(f"Shorten sentences (avg {report.avg_sentence_length} words, target < 20)")
        if report.long_sentences > 5:
            report.suggestions.append(f"Break up {report.long_sentences} long sentences (> 20 words)")
        if report.long_paragraphs > 2:
            report.suggestions.append(f"Split {report.long_paragraphs} long paragraphs (> 100 words)")
        if not report.has_bullet_lists:
            report.suggestions.append("Add bullet points for better scannability")
        if report.transition_words_count < 3:
            report.suggestions.append("Add more transition words for better flow")

        return report

    def _audit_keyword(
        self, content: str, keyword: str,
        meta_title: str, meta_description: str, url: str,
    ) -> KeywordPlacement:
        """Audit keyword placement throughout content."""
        kp = KeywordPlacement(keyword=keyword)
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        words = content.split()

        # Count
        kp.total_count = content_lower.count(keyword_lower)
        kp.density_percent = round(
            (kp.total_count / len(words) * 100) if words else 0, 2
        )

        # Placement checks
        first_para = content.split("\n\n")[0] if "\n\n" in content else content[:300]
        kp.in_first_paragraph = keyword_lower in first_para.lower()

        last_para = content.split("\n\n")[-1] if "\n\n" in content else content[-300:]
        kp.in_last_paragraph = keyword_lower in last_para.lower()

        headings = [l for l in content.split("\n") if l.startswith("#")]
        kp.in_headings = any(keyword_lower in h.lower() for h in headings)

        if meta_title:
            kp.in_title = keyword_lower in meta_title.lower()
        else:
            title_line = next((l for l in content.split("\n") if l.startswith("# ")), "")
            kp.in_title = keyword_lower in title_line.lower()

        if meta_description:
            kp.in_meta_description = keyword_lower in meta_description.lower()

        if url:
            kp.in_url_slug = keyword_lower.replace(" ", "-") in url.lower()

        # Positions
        if kp.in_title:
            kp.positions.append("title")
        if kp.in_first_paragraph:
            kp.positions.append("first_paragraph")
        if kp.in_headings:
            kp.positions.append("headings")
        if kp.in_last_paragraph:
            kp.positions.append("conclusion")
        if kp.in_meta_description:
            kp.positions.append("meta_description")
        if kp.in_url_slug:
            kp.positions.append("url")

        # Score
        kp.score = len(kp.positions) * 15.0
        if 1.0 <= kp.density_percent <= 2.5:
            kp.score += 10
        kp.score = min(100.0, kp.score)

        # Suggestions
        if not kp.in_first_paragraph:
            kp.suggestions.append("Add keyword to the first paragraph")
        if not kp.in_headings:
            kp.suggestions.append("Include keyword in at least one H2 heading")
        if not kp.in_title:
            kp.suggestions.append("Add keyword to the title/H1")
        if kp.density_percent < 0.5:
            kp.suggestions.append(f"Increase keyword usage (current: {kp.density_percent}%)")
        elif kp.density_percent > 3.0:
            kp.suggestions.append(f"Reduce keyword usage (current: {kp.density_percent}%, risk of stuffing)")

        return kp


    async def _check_plagiarism(self, content: str) -> Dict[str, Any]:
        """AI-based originality/plagiarism risk check."""
        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = PLAGIARISM_CHECK_PROMPT.format(content=content[:5000])

            response = await provider.generate(
                prompt=prompt,
                system_prompt="You are a plagiarism detection expert. Analyze content originality.",
                max_tokens=2048,
                temperature=0.2,
            )

            data = self._parse_json(response)
            return data if data else {"originality_score": 0, "error": "Could not parse response"}

        except Exception as e:
            logger.error(f"Plagiarism check failed: {e}")
            return {"originality_score": 0, "error": str(e)}

    async def _generate_serp_preview(
        self, title: str, meta_description: str, url: str, content_summary: str,
    ) -> Dict[str, Any]:
        """Generate SERP preview analysis."""
        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = SERP_PREVIEW_PROMPT.format(
                title=title,
                meta_description=meta_description,
                url=url,
                content_summary=content_summary,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt="You are a Google SERP optimization expert.",
                max_tokens=2048,
                temperature=0.3,
            )

            data = self._parse_json(response)
            return data if data else {}

        except Exception as e:
            logger.error(f"SERP preview failed: {e}")
            return {"error": str(e)}

    def _calculate_overall_grade(self, result: ContentTestResult):
        """Calculate overall grade and publish readiness."""
        scores = []
        if result.seo_score:
            scores.append(result.seo_score.overall_score)
        if result.readability:
            scores.append(result.readability.score)
        if result.keyword_audit:
            scores.append(result.keyword_audit[0].score)

        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score >= 85:
            result.overall_grade = "A"
            result.publish_ready = True
        elif avg_score >= 70:
            result.overall_grade = "B"
            result.publish_ready = True
        elif avg_score >= 55:
            result.overall_grade = "C"
            result.publish_ready = False
        elif avg_score >= 40:
            result.overall_grade = "D"
            result.publish_ready = False
        else:
            result.overall_grade = "F"
            result.publish_ready = False

        # Compile issues
        if result.seo_score:
            for fix in result.seo_score.priority_fixes[:5]:
                result.critical_issues.append(fix)

        if result.readability and result.readability.suggestions:
            for sug in result.readability.suggestions[:3]:
                result.warnings.append(sug)

        if result.keyword_audit:
            for kp in result.keyword_audit:
                if kp.score >= 70:
                    result.passed_checks.append(f"Keyword '{kp.keyword}' well-placed ({kp.score:.0f}/100)")
                else:
                    for sug in kp.suggestions:
                        result.warnings.append(sug)

    def _extract_title(self, content: str) -> str:
        """Extract title from content."""
        for line in content.split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
        return content[:60]

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word."""
        word = word.lower().strip(".,!?;:'\"")
        if len(word) <= 3:
            return 1
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in "aeiou"
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith("e"):
            count -= 1
        return max(1, count)

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from AI response."""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            try:
                return json.loads(response[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(response[start_idx:end_idx])
            except json.JSONDecodeError:
                pass
        return None
