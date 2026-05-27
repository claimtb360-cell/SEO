"""Content Editor/Optimizer - Rewrite sections, improve readability, fix SEO issues, A/B variations."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.logger import logger
from .providers import get_provider


EDITOR_SYSTEM = """You are an expert content editor specializing in SEO optimization.
You improve existing content while preserving the author's voice and meaning.
Focus on: readability, keyword optimization, engagement, and structure.
Always return clean, publish-ready content."""

REWRITE_SECTION_PROMPT = """Rewrite this section to improve SEO and readability:

**Section Content:**
{section_content}

**Target Keyword:** {keyword}
**Goals:** {goals}
**Tone:** {tone}
**Language:** {language}

Improvements to make:
- Improve readability (shorter sentences, active voice)
- Naturally integrate keyword (if missing)
- Add engaging transitions
- Break up long paragraphs
- Strengthen opening and closing of section
- Keep the same information and meaning

Return only the rewritten section in markdown format."""

READABILITY_IMPROVE_PROMPT = """Improve the readability of this content without changing its meaning:

**Content:**
{content}

**Target Reading Level:** {reading_level}
**Language:** {language}

Rules:
1. Break sentences longer than 20 words into shorter ones
2. Replace complex words with simpler alternatives
3. Use active voice instead of passive
4. Add transitional phrases between paragraphs
5. Break up walls of text into shorter paragraphs
6. Add bullet points where listing items
7. Keep technical accuracy

Return the improved content in markdown format.
At the end add:
---
**Readability Changes:**
- Sentences shortened: <count>
- Complex words replaced: <count>
- Paragraphs split: <count>
- Passive to active: <count>"""

FIX_SEO_ISSUES_PROMPT = """Fix the following SEO issues in this content:

**Content:**
{content}

**Primary Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Issues to Fix:**
{issues}

For each issue, make the minimum necessary change to fix it while maintaining content quality.
Return the fixed content in markdown format.

At the end add:
---
**Fixes Applied:**
{fix_template}"""

AB_VARIATION_PROMPT = """Create {num_variations} A/B test variations of this content element:

**Element Type:** {element_type}
**Original:** {original}
**Primary Keyword:** {keyword}
**Goal:** {goal}

For each variation:
- Keep the same core message
- Change angle, wording, or format
- Optimize for the stated goal
- Include the keyword naturally

Return as JSON:
{{
    "original": "{original}",
    "variations": [
        {{
            "id": "A",
            "content": "<variation>",
            "strategy": "<what was changed and why>",
            "predicted_improvement": "<what metric should improve>"
        }}
    ]
}}"""

EXPAND_CONTENT_PROMPT = """Expand this section with more detail, examples, and value:

**Current Content:**
{content}

**Keyword:** {keyword}
**Target Additional Words:** {additional_words}
**What to Add:** {expansion_type}
**Language:** {language}

Expansion options: examples, statistics, case studies, step-by-step details, expert quotes, comparisons.

Write the expanded version maintaining the same tone and style.
Naturally include the keyword 1-2 more times."""

SHORTEN_CONTENT_PROMPT = """Condense this content while keeping all key information:

**Current Content:**
{content}

**Target Word Count:** {target_words}
**Keyword to Keep:** {keyword}
**Priority Information:** {priorities}

Rules:
- Remove redundant phrases
- Combine similar points
- Keep all keyword mentions
- Maintain SEO value
- Preserve key data/stats

Return the shortened version."""


@dataclass
class EditOperation:
    """Single edit operation performed."""
    operation_type: str  # rewrite, readability, seo_fix, expand, shorten
    section_edited: str = ""
    before_preview: str = ""
    after_preview: str = ""
    changes_made: List[str] = field(default_factory=list)


@dataclass
class ContentEditorResult:
    """Result of content editing."""
    edited_content: str = ""
    original_word_count: int = 0
    edited_word_count: int = 0
    operations_performed: List[EditOperation] = field(default_factory=list)
    ab_variations: List[Dict[str, Any]] = field(default_factory=list)
    seo_issues_fixed: List[str] = field(default_factory=list)
    readability_before: str = ""
    readability_after: str = ""
    model_used: str = ""
    provider_used: str = ""
    generation_time_sec: float = 0.0
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edited_content": self.edited_content,
            "original_word_count": self.original_word_count,
            "edited_word_count": self.edited_word_count,
            "operations_performed": [
                {
                    "type": op.operation_type,
                    "section": op.section_edited,
                    "changes": op.changes_made,
                }
                for op in self.operations_performed
            ],
            "ab_variations": self.ab_variations,
            "seo_issues_fixed": self.seo_issues_fixed,
            "readability_before": self.readability_before,
            "readability_after": self.readability_after,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "generation_time_sec": self.generation_time_sec,
            "success": self.success,
            "error": self.error,
        }


class ContentEditor:
    """AI-powered content editor for SEO optimization."""

    def __init__(self, provider: str = "openai", model_id: str = "gpt-4o-mini"):
        self.provider_name = provider
        self.model_id = model_id

    async def rewrite_section(
        self,
        section_content: str,
        keyword: str,
        goals: str = "Improve readability and SEO",
        tone: str = "professional",
        language: str = "en",
    ) -> ContentEditorResult:
        """Rewrite a specific section for better SEO and readability."""
        import time
        start = time.time()

        result = ContentEditorResult(
            original_word_count=len(section_content.split()),
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = REWRITE_SECTION_PROMPT.format(
                section_content=section_content[:5000],
                keyword=keyword,
                goals=goals,
                tone=tone,
                language=language,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=EDITOR_SYSTEM,
                max_tokens=4096,
                temperature=0.6,
            )

            result.edited_content = response
            result.edited_word_count = len(response.split())
            result.operations_performed.append(EditOperation(
                operation_type="rewrite",
                section_edited="full_section",
                before_preview=section_content[:100],
                after_preview=response[:100],
                changes_made=["Rewrote section for better SEO and readability"],
            ))
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Section rewrite failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def improve_readability(
        self,
        content: str,
        reading_level: str = "8th grade",
        language: str = "en",
    ) -> ContentEditorResult:
        """Improve content readability to target reading level."""
        import time
        start = time.time()

        result = ContentEditorResult(
            original_word_count=len(content.split()),
            readability_before=self._assess_readability(content),
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = READABILITY_IMPROVE_PROMPT.format(
                content=content[:8000],
                reading_level=reading_level,
                language=language,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=EDITOR_SYSTEM,
                max_tokens=8192,
                temperature=0.4,
            )

            result.edited_content = response
            result.edited_word_count = len(response.split())
            result.readability_after = self._assess_readability(response)
            result.operations_performed.append(EditOperation(
                operation_type="readability",
                section_edited="full_content",
                changes_made=[
                    f"Readability: {result.readability_before} → {result.readability_after}",
                    f"Target level: {reading_level}",
                ],
            ))
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Readability improvement failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def fix_seo_issues(
        self,
        content: str,
        keyword: str,
        secondary_keywords: str = "",
        issues: Optional[List[str]] = None,
    ) -> ContentEditorResult:
        """Fix specific SEO issues in content."""
        import time
        start = time.time()

        result = ContentEditorResult(
            original_word_count=len(content.split()),
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        # Auto-detect issues if not provided
        if not issues:
            issues = self._detect_seo_issues(content, keyword)

        if not issues:
            result.edited_content = content
            result.edited_word_count = len(content.split())
            result.success = True
            result.seo_issues_fixed = ["No issues detected"]
            result.generation_time_sec = round(time.time() - start, 2)
            return result

        try:
            provider = get_provider(self.provider_name, self.model_id)

            issues_text = "\n".join(f"- {issue}" for issue in issues)
            fix_template = "\n".join(f"- [ ] {issue}" for issue in issues)

            prompt = FIX_SEO_ISSUES_PROMPT.format(
                content=content[:8000],
                keyword=keyword,
                secondary_keywords=secondary_keywords or "N/A",
                issues=issues_text,
                fix_template=fix_template,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=EDITOR_SYSTEM,
                max_tokens=8192,
                temperature=0.3,
            )

            result.edited_content = response
            result.edited_word_count = len(response.split())
            result.seo_issues_fixed = issues
            result.operations_performed.append(EditOperation(
                operation_type="seo_fix",
                section_edited="full_content",
                changes_made=issues,
            ))
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"SEO fix failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def generate_ab_variations(
        self,
        original: str,
        keyword: str,
        element_type: str = "title",
        goal: str = "Increase CTR",
        num_variations: int = 3,
    ) -> ContentEditorResult:
        """Generate A/B test variations of a content element."""
        import time
        start = time.time()

        result = ContentEditorResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = AB_VARIATION_PROMPT.format(
                num_variations=num_variations,
                element_type=element_type,
                original=original,
                keyword=keyword,
                goal=goal,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=EDITOR_SYSTEM,
                max_tokens=2048,
                temperature=0.8,
            )

            data = self._parse_json(response)
            if data:
                result.ab_variations = data.get("variations", [])
            else:
                # Fallback: parse as text
                result.ab_variations = [{"content": response, "strategy": "AI generated"}]

            result.edited_content = original
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"A/B variation generation failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def expand_content(
        self,
        content: str,
        keyword: str,
        additional_words: int = 300,
        expansion_type: str = "examples and details",
        language: str = "en",
    ) -> ContentEditorResult:
        """Expand content with more detail."""
        import time
        start = time.time()

        result = ContentEditorResult(
            original_word_count=len(content.split()),
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = EXPAND_CONTENT_PROMPT.format(
                content=content[:6000],
                keyword=keyword,
                additional_words=additional_words,
                expansion_type=expansion_type,
                language=language,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=EDITOR_SYSTEM,
                max_tokens=8192,
                temperature=0.6,
            )

            result.edited_content = response
            result.edited_word_count = len(response.split())
            result.operations_performed.append(EditOperation(
                operation_type="expand",
                section_edited="full_content",
                changes_made=[
                    f"Expanded by ~{result.edited_word_count - result.original_word_count} words",
                    f"Added: {expansion_type}",
                ],
            ))
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Content expansion failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def shorten_content(
        self,
        content: str,
        keyword: str,
        target_words: int = 500,
        priorities: str = "Keep key facts, data, and keyword mentions",
    ) -> ContentEditorResult:
        """Shorten content while preserving key information."""
        import time
        start = time.time()

        result = ContentEditorResult(
            original_word_count=len(content.split()),
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            provider = get_provider(self.provider_name, self.model_id)

            prompt = SHORTEN_CONTENT_PROMPT.format(
                content=content[:8000],
                target_words=target_words,
                keyword=keyword,
                priorities=priorities,
            )

            response = await provider.generate(
                prompt=prompt,
                system_prompt=EDITOR_SYSTEM,
                max_tokens=4096,
                temperature=0.3,
            )

            result.edited_content = response
            result.edited_word_count = len(response.split())
            result.operations_performed.append(EditOperation(
                operation_type="shorten",
                section_edited="full_content",
                changes_made=[
                    f"Reduced from {result.original_word_count} to {result.edited_word_count} words",
                    f"Target was {target_words} words",
                ],
            ))
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Content shortening failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    def _detect_seo_issues(self, content: str, keyword: str) -> List[str]:
        """Auto-detect common SEO issues."""
        issues = []
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        words = content.split()

        # Keyword in first paragraph
        first_para = content.split("\n\n")[0] if "\n\n" in content else content[:300]
        if keyword_lower not in first_para.lower():
            issues.append(f"Keyword '{keyword}' not found in first paragraph")

        # Keyword in headings
        headings = [l for l in content.split("\n") if l.startswith("## ")]
        if headings and not any(keyword_lower in h.lower() for h in headings):
            issues.append(f"Keyword '{keyword}' not in any H2 heading")

        # Keyword density
        count = content_lower.count(keyword_lower)
        density = (count / len(words)) * 100 if words else 0
        if density < 0.5:
            issues.append(f"Keyword density too low ({density:.1f}%, target 1-2%)")
        elif density > 3.0:
            issues.append(f"Keyword density too high ({density:.1f}%, risk of stuffing)")

        # No subheadings
        if "## " not in content:
            issues.append("Missing H2 subheadings - add structure")

        # No lists
        if "- " not in content and "1. " not in content:
            issues.append("No bullet/numbered lists - add for scannability")

        # Long paragraphs
        paragraphs = [p for p in content.split("\n\n") if len(p.split()) > 100]
        if paragraphs:
            issues.append(f"{len(paragraphs)} paragraphs over 100 words - break them up")

        # Missing meta suggestion
        if "meta" not in content_lower and "description" not in content_lower:
            issues.append("Consider adding meta title/description at the end")

        return issues

    def _assess_readability(self, content: str) -> str:
        """Quick readability assessment."""
        sentences = [s.strip() for s in content.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            return "Unknown"
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_len <= 12:
            return "Very Easy"
        elif avg_len <= 16:
            return "Easy"
        elif avg_len <= 20:
            return "Medium"
        elif avg_len <= 25:
            return "Hard"
        return "Very Hard"

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
