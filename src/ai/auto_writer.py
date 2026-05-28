"""Auto Article Writer - Full pipeline: Research → Outline → Draft → Optimize → Publish-ready."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.utils.logger import logger
from .providers import get_provider
from .keyword_researcher import KeywordResearcher


AUTO_WRITER_SYSTEM = """You are a professional SEO content writer who creates high-quality, 
well-researched articles that rank in search engines. You follow a structured writing process:
research, outline, draft, then optimize. Your content is engaging, factual, and valuable to readers."""

OUTLINE_PROMPT = """Create a detailed article outline for:

**Topic:** {topic}
**Primary Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Target Word Count:** {word_count}
**Tone:** {tone}
**Audience:** {audience}
**Language:** {language}
**Search Intent:** {search_intent}
**Key Topics to Cover:** {key_topics}

Create a JSON outline:
{{
    "title": "<SEO-optimized title with keyword>",
    "meta_title": "<50-60 char meta title>",
    "meta_description": "<150-160 char meta description>",
    "slug": "<url-friendly-slug>",
    "introduction": {{
        "hook": "<attention-grabbing opening line>",
        "context": "<why this topic matters>",
        "thesis": "<main point of the article>",
        "estimated_words": <int>
    }},
    "sections": [
        {{
            "heading": "<H2 heading with keyword variation>",
            "subheadings": ["<H3 subheading>"],
            "key_points": ["<main point to cover>"],
            "keywords_to_include": ["<keywords for this section>"],
            "content_type": "<paragraph/list/comparison/how-to/example>",
            "estimated_words": <int>
        }}
    ],
    "faq_section": [
        {{"question": "<FAQ question>", "brief_answer": "<1-2 sentence preview>"}}
    ],
    "conclusion": {{
        "summary_points": ["<key takeaway>"],
        "cta": "<call to action>",
        "estimated_words": <int>
    }},
    "internal_link_suggestions": ["<topics to link to>"],
    "external_source_suggestions": ["<authoritative sources to reference>"]
}}"""

DRAFT_SECTION_PROMPT = """Write this section of an article:

**Article Title:** {title}
**Section Heading:** {heading}
**Subheadings:** {subheadings}
**Key Points to Cover:** {key_points}
**Keywords to Include:** {keywords}
**Content Type:** {content_type}
**Target Words:** {target_words}
**Tone:** {tone}
**Language:** {language}

**Context (previous section summary):** {context}

Rules:
- Write naturally, avoid keyword stuffing
- Include the keywords organically (1-2 times each)
- Use short paragraphs (2-3 sentences)
- Add transition from previous section
- Include examples or data where relevant
- Use markdown formatting (##, ###, -, **bold**)
- Make it engaging and valuable

Write the complete section content:"""

OPTIMIZE_DRAFT_PROMPT = """Optimize this article draft for SEO and readability:

**Full Draft:**
{draft}

**Primary Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Target Keyword Density:** 1.5-2%

Optimization checklist:
1. Ensure keyword appears in first paragraph
2. Add keyword to at least one H2 heading
3. Improve transition sentences between sections
4. Add internal link anchor text suggestions [like this](url-placeholder)
5. Ensure conclusion has a clear CTA
6. Fix any readability issues (sentences > 20 words)
7. Add power words for engagement
8. Ensure proper heading hierarchy
9. Add alt text suggestions for any images mentioned
10. Format for featured snippet (if applicable)

Return the optimized article in Markdown format. At the end, add:
---
**SEO Metadata:**
- Meta Title: <optimized>
- Meta Description: <optimized>
- Focus Keyword: {keyword}
- Keyword Density: <calculated %>
- Word Count: <total>
- Readability: <Easy/Medium/Hard>
- Changes Made: <bullet list of improvements>"""


@dataclass
class ArticleOutline:
    title: str = ""
    meta_title: str = ""
    meta_description: str = ""
    slug: str = ""
    introduction: Dict[str, Any] = field(default_factory=dict)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    faq_section: List[Dict[str, str]] = field(default_factory=list)
    conclusion: Dict[str, Any] = field(default_factory=dict)
    internal_link_suggestions: List[str] = field(default_factory=list)
    external_source_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "slug": self.slug,
            "introduction": self.introduction,
            "sections": self.sections,
            "faq_section": self.faq_section,
            "conclusion": self.conclusion,
            "internal_link_suggestions": self.internal_link_suggestions,
            "external_source_suggestions": self.external_source_suggestions,
        }


@dataclass
class AutoWriterResult:
    """Result of the auto-writing pipeline."""
    # Pipeline status
    stage: str = ""  # research, outline, draft, optimize, complete
    pipeline_complete: bool = False

    # Research results
    keyword_data: Dict[str, Any] = field(default_factory=dict)

    # Outline
    outline: Optional[ArticleOutline] = None

    # Draft
    raw_draft: str = ""
    draft_word_count: int = 0

    # Final optimized content
    final_content: str = ""
    final_word_count: int = 0
    meta_title: str = ""
    meta_description: str = ""
    slug: str = ""

    # Scoring
    seo_score: float = 0.0
    readability_score: str = ""
    keyword_density: float = 0.0

    # Metadata
    model_used: str = ""
    provider_used: str = ""
    total_time_sec: float = 0.0
    estimated_cost: float = 0.0
    stages_completed: List[str] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "pipeline_complete": self.pipeline_complete,
            "keyword_data": self.keyword_data,
            "outline": self.outline.to_dict() if self.outline else None,
            "raw_draft": self.raw_draft,
            "draft_word_count": self.draft_word_count,
            "final_content": self.final_content,
            "final_word_count": self.final_word_count,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "slug": self.slug,
            "seo_score": self.seo_score,
            "readability_score": self.readability_score,
            "keyword_density": self.keyword_density,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "total_time_sec": self.total_time_sec,
            "estimated_cost": self.estimated_cost,
            "stages_completed": self.stages_completed,
            "success": self.success,
            "error": self.error,
        }


class AutoWriter:
    """Automated article writing pipeline: Research → Outline → Draft → Optimize."""

    def __init__(self, provider: str = "openai", model_id: str = "gpt-4o-mini"):
        self.provider_name = provider
        self.model_id = model_id

    async def write_article(
        self,
        topic: str,
        keyword: str,
        secondary_keywords: str = "",
        word_count: int = 1500,
        tone: str = "professional",
        audience: str = "general",
        language: str = "en",
        niche: str = "general",
        skip_research: bool = False,
    ) -> AutoWriterResult:
        """Execute the full auto-writing pipeline."""
        import time
        start = time.time()

        result = AutoWriterResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            # Stage 1: Keyword Research
            if not skip_research:
                result.stage = "research"
                logger.info(f"[AutoWriter] Stage 1: Researching '{keyword}'")
                research_data = await self._research_keyword(keyword, niche, language)
                result.keyword_data = research_data
                result.stages_completed.append("research")

                # Extract useful data for outline
                search_intent = research_data.get("search_intent", "informational")
                key_topics = research_data.get("trending_subtopics", [])
                if not secondary_keywords:
                    related = research_data.get("related_keywords", [])
                    secondary_keywords = ", ".join(
                        kw.get("keyword", "") for kw in related[:5]
                    )
            else:
                search_intent = "informational"
                key_topics = []

            # Stage 2: Create Outline
            result.stage = "outline"
            logger.info("[AutoWriter] Stage 2: Creating outline")
            outline = await self._create_outline(
                topic=topic,
                keyword=keyword,
                secondary_keywords=secondary_keywords,
                word_count=word_count,
                tone=tone,
                audience=audience,
                language=language,
                search_intent=search_intent,
                key_topics=key_topics,
            )
            result.outline = outline
            result.stages_completed.append("outline")

            # Stage 3: Write Draft (section by section)
            result.stage = "draft"
            logger.info("[AutoWriter] Stage 3: Writing draft")
            draft = await self._write_draft(outline, tone, language, keyword)
            result.raw_draft = draft
            result.draft_word_count = len(draft.split())
            result.stages_completed.append("draft")

            # Stage 4: Optimize
            result.stage = "optimize"
            logger.info("[AutoWriter] Stage 4: Optimizing content")
            optimized = await self._optimize_draft(draft, keyword, secondary_keywords)
            result.final_content = optimized
            result.final_word_count = len(optimized.split())
            result.stages_completed.append("optimize")

            # Extract metadata
            result.meta_title = outline.meta_title
            result.meta_description = outline.meta_description
            result.slug = outline.slug

            # Calculate scores
            result.seo_score = self._calculate_seo_score(optimized, keyword)
            result.keyword_density = self._calculate_density(optimized, keyword)
            result.readability_score = self._assess_readability(optimized)

            result.stage = "complete"
            result.pipeline_complete = True
            result.success = True

        except Exception as e:
            result.error = f"Failed at stage '{result.stage}': {str(e)}"
            logger.error(f"[AutoWriter] Error: {e}")

        result.total_time_sec = round(time.time() - start, 2)
        return result

    async def create_outline_only(
        self,
        topic: str,
        keyword: str,
        secondary_keywords: str = "",
        word_count: int = 1500,
        tone: str = "professional",
        audience: str = "general",
        language: str = "en",
    ) -> AutoWriterResult:
        """Create just the outline (for user review before full generation)."""
        import time
        start = time.time()

        result = AutoWriterResult(
            model_used=self.model_id,
            provider_used=self.provider_name,
        )

        try:
            outline = await self._create_outline(
                topic=topic, keyword=keyword,
                secondary_keywords=secondary_keywords,
                word_count=word_count, tone=tone,
                audience=audience, language=language,
                search_intent="informational", key_topics=[],
            )
            result.outline = outline
            result.stage = "outline"
            result.stages_completed.append("outline")
            result.success = True
        except Exception as e:
            result.error = str(e)

        result.total_time_sec = round(time.time() - start, 2)
        return result

    async def _research_keyword(self, keyword: str, niche: str, language: str) -> Dict[str, Any]:
        """Stage 1: Research keyword using KeywordResearcher."""
        researcher = KeywordResearcher(self.provider_name, self.model_id)
        research_result = await researcher.research(keyword, niche=niche, language=language)
        return research_result.to_dict() if research_result.success else {}

    async def _create_outline(
        self, topic: str, keyword: str, secondary_keywords: str,
        word_count: int, tone: str, audience: str, language: str,
        search_intent: str, key_topics: List[str],
    ) -> ArticleOutline:
        """Stage 2: Create structured outline."""
        provider = get_provider(self.provider_name, self.model_id)

        prompt = OUTLINE_PROMPT.format(
            topic=topic, keyword=keyword,
            secondary_keywords=secondary_keywords or "N/A",
            word_count=word_count, tone=tone,
            audience=audience, language=language,
            search_intent=search_intent,
            key_topics=", ".join(key_topics[:10]) if key_topics else "N/A",
        )

        response = await provider.generate(
            prompt=prompt,
            system_prompt=AUTO_WRITER_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )

        data = self._parse_json(response)
        outline = ArticleOutline()

        if data:
            outline.title = data.get("title", topic)
            outline.meta_title = data.get("meta_title", "")
            outline.meta_description = data.get("meta_description", "")
            outline.slug = data.get("slug", "")
            outline.introduction = data.get("introduction", {})
            outline.sections = data.get("sections", [])
            outline.faq_section = data.get("faq_section", [])
            outline.conclusion = data.get("conclusion", {})
            outline.internal_link_suggestions = data.get("internal_link_suggestions", [])
            outline.external_source_suggestions = data.get("external_source_suggestions", [])

        return outline

    async def _write_draft(
        self, outline: ArticleOutline, tone: str, language: str, keyword: str,
    ) -> str:
        """Stage 3: Write the article section by section."""
        provider = get_provider(self.provider_name, self.model_id)
        parts = []

        # Write introduction
        intro_prompt = f"""Write an engaging introduction for an article titled "{outline.title}".
Hook: {outline.introduction.get('hook', '')}
Context: {outline.introduction.get('context', '')}
Thesis: {outline.introduction.get('thesis', '')}
Target words: {outline.introduction.get('estimated_words', 150)}
Keyword to include: {keyword}
Tone: {tone}, Language: {language}

Write in markdown format starting with # {outline.title}"""

        intro = await provider.generate(
            prompt=intro_prompt,
            system_prompt=AUTO_WRITER_SYSTEM,
            max_tokens=1024,
            temperature=0.7,
        )
        parts.append(intro)

        # Write each section
        context = "Introduction written about " + outline.introduction.get("thesis", "the topic")
        for section in outline.sections:
            prompt = DRAFT_SECTION_PROMPT.format(
                title=outline.title,
                heading=section.get("heading", ""),
                subheadings=", ".join(section.get("subheadings", [])),
                key_points="\n".join(f"- {p}" for p in section.get("key_points", [])),
                keywords=", ".join(section.get("keywords_to_include", [keyword])),
                content_type=section.get("content_type", "paragraph"),
                target_words=section.get("estimated_words", 200),
                tone=tone,
                language=language,
                context=context,
            )

            section_content = await provider.generate(
                prompt=prompt,
                system_prompt=AUTO_WRITER_SYSTEM,
                max_tokens=2048,
                temperature=0.7,
            )
            parts.append(section_content)
            context = f"Section '{section.get('heading', '')}' covered: {', '.join(section.get('key_points', [])[:2])}"

        # Write FAQ section
        if outline.faq_section:
            faq_text = "\n\n## Frequently Asked Questions\n\n"
            for faq in outline.faq_section:
                faq_text += f"### {faq.get('question', '')}\n\n"
                faq_text += f"{faq.get('brief_answer', '')}\n\n"

            faq_prompt = f"""Expand these FAQ answers to 2-3 sentences each, naturally including the keyword '{keyword}':

{faq_text}

Tone: {tone}, Language: {language}"""

            faq_content = await provider.generate(
                prompt=faq_prompt,
                system_prompt=AUTO_WRITER_SYSTEM,
                max_tokens=1024,
                temperature=0.6,
            )
            parts.append(faq_content)

        # Write conclusion
        conclusion_prompt = f"""Write a conclusion for the article "{outline.title}".
Summary points: {', '.join(outline.conclusion.get('summary_points', []))}
CTA: {outline.conclusion.get('cta', 'Take action today')}
Target words: {outline.conclusion.get('estimated_words', 150)}
Keyword: {keyword}
Tone: {tone}, Language: {language}

Start with ## Conclusion"""

        conclusion = await provider.generate(
            prompt=conclusion_prompt,
            system_prompt=AUTO_WRITER_SYSTEM,
            max_tokens=512,
            temperature=0.6,
        )
        parts.append(conclusion)

        return "\n\n".join(parts)

    async def _optimize_draft(self, draft: str, keyword: str, secondary_keywords: str) -> str:
        """Stage 4: Optimize the draft for SEO."""
        provider = get_provider(self.provider_name, self.model_id)

        prompt = OPTIMIZE_DRAFT_PROMPT.format(
            draft=draft[:12000],
            keyword=keyword,
            secondary_keywords=secondary_keywords or "N/A",
        )

        optimized = await provider.generate(
            prompt=prompt,
            system_prompt=AUTO_WRITER_SYSTEM,
            max_tokens=8192,
            temperature=0.4,
        )

        return optimized

    def _calculate_seo_score(self, content: str, keyword: str) -> float:
        """Calculate basic SEO score."""
        score = 60.0
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        if keyword_lower in " ".join(content.split()[:100]).lower():
            score += 10
        if "## " in content:
            score += 5
        heading_lines = [l for l in content.split("\n") if l.startswith("## ")]
        if any(keyword_lower in h.lower() for h in heading_lines):
            score += 10
        if "- " in content or "1. " in content:
            score += 5
        if "faq" in content_lower or "frequently" in content_lower:
            score += 5
        density = self._calculate_density(content, keyword)
        if 1.0 <= density <= 2.5:
            score += 10
        elif 0.5 <= density < 1.0:
            score += 5
        if len(content.split()) >= 1000:
            score += 5

        return min(100.0, score)

    def _calculate_density(self, content: str, keyword: str) -> float:
        """Calculate keyword density percentage."""
        words = content.lower().split()
        keyword_lower = keyword.lower()
        count = content.lower().count(keyword_lower)
        total = len(words) if words else 1
        keyword_words = len(keyword_lower.split())
        return round((count / (total / keyword_words)) * 100, 2)

    def _assess_readability(self, content: str) -> str:
        """Quick readability assessment."""
        sentences = [s.strip() for s in content.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            return "Unknown"
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_len <= 15:
            return "Easy"
        elif avg_len <= 20:
            return "Medium"
        return "Hard"

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from AI response."""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        if "```json" in response:
            try:
                start = response.index("```json") + 7
                end = response.index("```", start)
                return json.loads(response[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass
        elif "```" in response:
            try:
                start = response.index("```") + 3
                # Skip language identifier if present
                newline = response.index("\n", start)
                start = newline + 1
                end = response.index("```", start)
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
