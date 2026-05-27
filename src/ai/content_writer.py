"""AI Content Writer - generates SEO-optimized content using multiple AI models."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.utils.logger import logger
from .models import AIProvider, get_model, get_available_models
from .providers import get_provider, BaseAIProvider
from .prompts import SEO_WRITER_SYSTEM, CONTENT_TYPES


@dataclass
class ContentRequest:
    """Request for AI content generation."""
    topic: str
    keyword: str
    content_type: str = "article"  # article, blog_post, product_description, meta_tags, rewrite, outline
    secondary_keywords: str = ""
    word_count: int = 1500
    tone: str = "professional"  # professional, conversational, technical, casual, formal
    audience: str = "general"
    language: str = "en"
    instructions: str = ""
    original_content: str = ""  # For rewrite mode
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "keyword": self.keyword,
            "content_type": self.content_type,
            "secondary_keywords": self.secondary_keywords,
            "word_count": self.word_count,
            "tone": self.tone,
            "audience": self.audience,
            "language": self.language,
            "provider": self.provider,
            "model_id": self.model_id,
        }


@dataclass
class ContentResult:
    """Result of AI content generation."""
    content: str = ""
    meta_title: str = ""
    meta_description: str = ""
    word_count: int = 0
    model_used: str = ""
    provider_used: str = ""
    generation_time_sec: float = 0.0
    estimated_cost: float = 0.0
    seo_score: Optional[float] = None
    suggestions: List[str] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "word_count": self.word_count,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "generation_time_sec": self.generation_time_sec,
            "estimated_cost": self.estimated_cost,
            "seo_score": self.seo_score,
            "suggestions": self.suggestions,
            "success": self.success,
            "error": self.error,
        }


class AIContentWriter:
    """Generates SEO-optimized content using AI models."""

    def __init__(self):
        pass

    async def generate(self, request: ContentRequest) -> ContentResult:
        """Generate SEO content based on the request."""
        import time
        start = time.time()
        result = ContentResult(
            model_used=request.model_id,
            provider_used=request.provider,
        )

        try:
            # Get AI provider
            provider = get_provider(request.provider, request.model_id)

            # Build prompt
            prompt = self._build_prompt(request)

            # Generate content
            logger.info(f"Generating content with {request.provider}/{request.model_id}")
            content = await provider.generate(
                prompt=prompt,
                system_prompt=SEO_WRITER_SYSTEM,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            result.content = content
            result.word_count = len(content.split())
            result.success = True

            # Extract meta tags if present in content
            result.meta_title = self._extract_meta_title(content)
            result.meta_description = self._extract_meta_description(content)

            # Estimate cost
            model_info = get_model(request.model_id)
            if model_info:
                input_tokens = len(prompt.split()) * 1.3  # rough estimate
                output_tokens = len(content.split()) * 1.3
                result.estimated_cost = round(
                    (input_tokens / 1000 * model_info.cost_per_1k_input) +
                    (output_tokens / 1000 * model_info.cost_per_1k_output),
                    4,
                )

            # Basic SEO score for the generated content
            result.seo_score = self._quick_seo_score(content, request.keyword)
            result.suggestions = self._get_suggestions(content, request)

        except Exception as e:
            result.error = str(e)
            logger.error(f"AI content generation failed: {e}")

        result.generation_time_sec = round(time.time() - start, 2)
        return result

    async def generate_multiple(
        self,
        request: ContentRequest,
        models: List[Dict[str, str]],
    ) -> List[ContentResult]:
        """Generate content with multiple models for comparison."""
        import asyncio
        results = []
        for model_config in models:
            req = ContentRequest(
                topic=request.topic,
                keyword=request.keyword,
                content_type=request.content_type,
                secondary_keywords=request.secondary_keywords,
                word_count=request.word_count,
                tone=request.tone,
                audience=request.audience,
                language=request.language,
                instructions=request.instructions,
                original_content=request.original_content,
                provider=model_config["provider"],
                model_id=model_config["model_id"],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            result = await self.generate(req)
            results.append(result)
        return results

    def _build_prompt(self, request: ContentRequest) -> str:
        """Build the appropriate prompt based on content type."""
        template = CONTENT_TYPES.get(request.content_type, CONTENT_TYPES["article"])

        return template.format(
            topic=request.topic,
            keyword=request.keyword,
            secondary_keywords=request.secondary_keywords or "N/A",
            word_count=request.word_count,
            tone=request.tone,
            audience=request.audience,
            language=request.language,
            instructions=request.instructions or "None",
            original_content=request.original_content or "",
        )

    def _extract_meta_title(self, content: str) -> str:
        """Try to extract meta title from generated content."""
        lines = content.split("\n")
        for line in lines:
            lower = line.lower().strip()
            if "meta title" in lower and ":" in line:
                return line.split(":", 1)[1].strip().strip('"').strip("*")
        # Fallback: use first H1
        for line in lines:
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    def _extract_meta_description(self, content: str) -> str:
        """Try to extract meta description from generated content."""
        lines = content.split("\n")
        for line in lines:
            lower = line.lower().strip()
            if "meta description" in lower and ":" in line:
                return line.split(":", 1)[1].strip().strip('"').strip("*")
        return ""

    def _quick_seo_score(self, content: str, keyword: str) -> float:
        """Calculate a quick SEO score for generated content."""
        score = 70.0  # Base score for AI-generated content
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        # Keyword in content
        keyword_count = content_lower.count(keyword_lower)
        word_count = len(content.split())
        if word_count > 0:
            density = (keyword_count / word_count) * 100
            if 1.0 <= density <= 2.5:
                score += 10
            elif 0.5 <= density < 1.0:
                score += 5

        # Has headings
        if "## " in content or "### " in content:
            score += 5

        # Has keyword in first 100 words
        first_100 = " ".join(content.split()[:100]).lower()
        if keyword_lower in first_100:
            score += 5

        # Word count check
        if word_count >= 1000:
            score += 5
        elif word_count >= 500:
            score += 3

        # Has lists
        if "- " in content or "1. " in content:
            score += 3

        # Has FAQ
        if "faq" in content_lower or "frequently asked" in content_lower:
            score += 2

        return min(100.0, score)

    def _get_suggestions(self, content: str, request: ContentRequest) -> List[str]:
        """Generate improvement suggestions for the content."""
        suggestions = []
        word_count = len(content.split())
        keyword_lower = request.keyword.lower()
        content_lower = content.lower()

        if word_count < request.word_count * 0.8:
            suggestions.append(f"Content is shorter than requested ({word_count} vs {request.word_count} words). Consider expanding.")

        keyword_count = content_lower.count(keyword_lower)
        if keyword_count == 0:
            suggestions.append(f"Target keyword '{request.keyword}' not found in content. Add it naturally.")
        elif keyword_count < 3:
            suggestions.append(f"Keyword usage is low ({keyword_count}x). Consider adding more natural mentions.")

        if "## " not in content:
            suggestions.append("Add H2 subheadings to improve content structure.")

        if "- " not in content and "1. " not in content:
            suggestions.append("Add bullet points or numbered lists for better readability.")

        first_paragraph = content.split("\n\n")[0] if "\n\n" in content else content[:200]
        if keyword_lower not in first_paragraph.lower():
            suggestions.append("Include the target keyword in the first paragraph/introduction.")

        return suggestions
