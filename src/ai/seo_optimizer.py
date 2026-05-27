"""AI SEO Optimizer - uses AI to analyze and improve existing content for SEO."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.utils.logger import logger
from .providers import get_provider
from .models import get_model


# Optimization-specific prompts
OPTIMIZE_SYSTEM = """You are an expert SEO consultant and content optimizer.
Your job is to analyze content and provide specific, actionable improvements to boost search rankings.
Always return structured JSON when asked for analysis results.
Be specific with suggestions - don't give generic advice."""

ANALYZE_CONTENT_PROMPT = """Analyze the following content for SEO optimization opportunities.

**Content:**
{content}

**Target Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Current URL:** {url}

Provide a detailed JSON analysis with this exact structure:
{{
    "overall_score": <0-100>,
    "keyword_analysis": {{
        "primary_keyword_count": <int>,
        "keyword_density": <float percent>,
        "keyword_in_title": <bool>,
        "keyword_in_first_paragraph": <bool>,
        "keyword_in_headings": <bool>,
        "keyword_in_meta_description": <bool>,
        "lsi_keywords_found": [<list of related terms found>],
        "missing_lsi_keywords": [<list of related terms that should be added>]
    }},
    "content_quality": {{
        "readability_grade": "<Easy/Medium/Hard>",
        "tone_consistency": <0-100>,
        "engagement_score": <0-100>,
        "uniqueness_estimate": <0-100>,
        "content_depth": "<Shallow/Medium/Deep>"
    }},
    "structure_analysis": {{
        "has_proper_h1": <bool>,
        "heading_hierarchy_valid": <bool>,
        "paragraph_length_ok": <bool>,
        "has_lists": <bool>,
        "has_internal_links": <bool>,
        "has_external_links": <bool>,
        "has_images_mentioned": <bool>,
        "has_cta": <bool>
    }},
    "improvements": [
        {{
            "priority": "<high/medium/low>",
            "category": "<keyword/content/structure/meta/technical>",
            "issue": "<description of issue>",
            "suggestion": "<specific fix>",
            "example": "<example of the fix if applicable>"
        }}
    ],
    "rewritten_meta_title": "<optimized meta title 50-60 chars>",
    "rewritten_meta_description": "<optimized meta description 150-160 chars>",
    "suggested_headings": ["<list of H2 headings to add or modify>"],
    "content_gaps": ["<topics/questions this content should address>"]
}}"""

IMPROVE_CONTENT_PROMPT = """Rewrite and optimize the following content for better SEO performance.

**Original Content:**
{content}

**Target Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Optimization Goals:** {goals}
**Language:** {language}

Rules:
1. Maintain the original meaning and facts
2. Improve keyword placement (1.5-2% density for primary keyword)
3. Add proper H2/H3 structure if missing
4. Improve readability (shorter sentences, simpler words)
5. Add transitional phrases between sections
6. Make it more engaging and valuable to readers
7. Ensure keyword appears in: first paragraph, at least one heading, conclusion
8. Add FAQ section if not present
9. Improve meta title and description

Output the improved content in Markdown format with a brief "Changes Made" summary at the end."""

TITLE_SUGGESTIONS_PROMPT = """Generate 10 SEO-optimized title variations for:

**Topic:** {topic}
**Primary Keyword:** {keyword}
**Content Type:** {content_type}
**Language:** {language}

Requirements for each title:
- Include the primary keyword (preferably near the start)
- 50-60 characters long
- Compelling and click-worthy
- Mix of formats: how-to, listicle, question, power words

Return as a numbered list with character count for each."""

INTERNAL_LINKING_PROMPT = """Suggest internal linking opportunities for this content:

**Content:**
{content}

**Site Pages Available:**
{available_pages}

**Target Keyword:** {keyword}

For each suggestion provide:
1. Anchor text to use
2. Which URL to link to
3. Where in the content to place it (quote the surrounding text)
4. Why this link adds value

Return as a structured list."""


@dataclass
class OptimizationIssue:
    priority: str  # high, medium, low
    category: str  # keyword, content, structure, meta, technical
    issue: str
    suggestion: str
    example: str = ""


@dataclass
class SEOOptimizationResult:
    """Result of AI SEO optimization analysis."""
    overall_score: float = 0.0
    keyword_analysis: Dict[str, Any] = field(default_factory=dict)
    content_quality: Dict[str, Any] = field(default_factory=dict)
    structure_analysis: Dict[str, Any] = field(default_factory=dict)
    improvements: List[OptimizationIssue] = field(default_factory=list)
    rewritten_meta_title: str = ""
    rewritten_meta_description: str = ""
    suggested_headings: List[str] = field(default_factory=list)
    content_gaps: List[str] = field(default_factory=list)
    improved_content: Optional[str] = None
    title_suggestions: List[str] = field(default_factory=list)
    model_used: str = ""
    provider_used: str = ""
    generation_time_sec: float = 0.0
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "keyword_analysis": self.keyword_analysis,
            "content_quality": self.content_quality,
            "structure_analysis": self.structure_analysis,
            "improvements": [
                {"priority": i.priority, "category": i.category,
                 "issue": i.issue, "suggestion": i.suggestion, "example": i.example}
                for i in self.improvements
            ],
            "rewritten_meta_title": self.rewritten_meta_title,
            "rewritten_meta_description": self.rewritten_meta_description,
            "suggested_headings": self.suggested_headings,
            "content_gaps": self.content_gaps,
            "improved_content": self.improved_content,
            "title_suggestions": self.title_suggestions,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "generation_time_sec": self.generation_time_sec,
            "success": self.success,
            "error": self.error,
        }


class AISEOOptimizer:
    """Uses AI to analyze and optimize content for SEO."""

    def __init__(self, provider: str = "openai", model_id: str = "gpt-4o-mini"):
        self.provider_name = provider
        self.model_id = model_id

    async def analyze(
        self,
        content: str,
        keyword: str,
        secondary_keywords: str = "",
        url: str = "",
    ) -> SEOOptimizationResult:
        """Analyze content and provide SEO optimization suggestions."""
        import time
        import json
        start = time.time()

        result = SEOOptimizationResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = ANALYZE_CONTENT_PROMPT.format(
                content=content[:8000],  # Limit content length
                keyword=keyword,
                secondary_keywords=secondary_keywords or "N/A",
                url=url or "N/A",
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=OPTIMIZE_SYSTEM,
                max_tokens=4096,
                temperature=0.3,  # Lower temperature for analytical tasks
            )

            # Parse JSON response
            analysis = self._parse_json_response(response)

            if analysis:
                result.overall_score = analysis.get("overall_score", 0)
                result.keyword_analysis = analysis.get("keyword_analysis", {})
                result.content_quality = analysis.get("content_quality", {})
                result.structure_analysis = analysis.get("structure_analysis", {})
                result.rewritten_meta_title = analysis.get("rewritten_meta_title", "")
                result.rewritten_meta_description = analysis.get("rewritten_meta_description", "")
                result.suggested_headings = analysis.get("suggested_headings", [])
                result.content_gaps = analysis.get("content_gaps", [])

                for imp in analysis.get("improvements", []):
                    result.improvements.append(OptimizationIssue(
                        priority=imp.get("priority", "medium"),
                        category=imp.get("category", "content"),
                        issue=imp.get("issue", ""),
                        suggestion=imp.get("suggestion", ""),
                        example=imp.get("example", ""),
                    ))

                result.success = True
            else:
                # Fallback: use raw response
                result.error = "Could not parse structured response"
                result.success = False

        except Exception as e:
            result.error = str(e)
            logger.error(f"AI SEO optimization failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def improve_content(
        self,
        content: str,
        keyword: str,
        secondary_keywords: str = "",
        goals: str = "Improve keyword placement, readability, and structure",
        language: str = "en",
    ) -> SEOOptimizationResult:
        """Rewrite and improve content for better SEO."""
        import time
        start = time.time()

        result = SEOOptimizationResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = IMPROVE_CONTENT_PROMPT.format(
                content=content[:8000],
                keyword=keyword,
                secondary_keywords=secondary_keywords or "N/A",
                goals=goals,
                language=language,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=OPTIMIZE_SYSTEM,
                max_tokens=8192,
                temperature=0.5,
            )

            result.improved_content = response
            result.success = True

            # Quick score for improved content
            result.overall_score = self._quick_score(response, keyword)

        except Exception as e:
            result.error = str(e)
            logger.error(f"AI content improvement failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def generate_title_suggestions(
        self,
        topic: str,
        keyword: str,
        content_type: str = "article",
        language: str = "en",
    ) -> SEOOptimizationResult:
        """Generate multiple SEO title suggestions."""
        import time
        start = time.time()

        result = SEOOptimizationResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = TITLE_SUGGESTIONS_PROMPT.format(
                topic=topic,
                keyword=keyword,
                content_type=content_type,
                language=language,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=OPTIMIZE_SYSTEM,
                max_tokens=2048,
                temperature=0.8,  # Higher creativity for titles
            )

            # Parse titles from response
            titles = []
            for line in response.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Remove numbering and clean up
                    clean = line.lstrip("0123456789.-) ").strip()
                    if clean and len(clean) > 10:
                        titles.append(clean)

            result.title_suggestions = titles[:10]
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Title generation failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def suggest_internal_links(
        self,
        content: str,
        keyword: str,
        available_pages: List[str],
    ) -> SEOOptimizationResult:
        """Suggest internal linking opportunities."""
        import time
        start = time.time()

        result = SEOOptimizationResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            pages_str = "\n".join(f"- {page}" for page in available_pages[:30])
            prompt = INTERNAL_LINKING_PROMPT.format(
                content=content[:5000],
                available_pages=pages_str,
                keyword=keyword,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=OPTIMIZE_SYSTEM,
                max_tokens=2048,
                temperature=0.4,
            )

            result.improved_content = response  # Store suggestions in improved_content
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Internal linking suggestion failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from AI response, handling markdown code blocks."""
        import json

        # Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            try:
                return json.loads(response[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass

        if "```" in response:
            parts = response.split("```")
            for part in parts[1::2]:  # Odd indices are code blocks
                clean = part.strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()
                try:
                    return json.loads(clean)
                except json.JSONDecodeError:
                    continue

        # Try finding JSON object in text
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(response[start_idx:end_idx])
            except json.JSONDecodeError:
                pass

        return None

    def _quick_score(self, content: str, keyword: str) -> float:
        """Quick SEO score for content."""
        score = 60.0
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        if keyword_lower in content_lower:
            score += 10
        if "## " in content:
            score += 10
        if "- " in content or "1. " in content:
            score += 5
        if keyword_lower in " ".join(content.split()[:100]).lower():
            score += 10
        if len(content.split()) >= 800:
            score += 5

        return min(100.0, score)
