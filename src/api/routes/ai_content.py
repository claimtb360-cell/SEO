"""AI Content Generation & Optimization API routes."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.schemas import ApiResponse
from src.ai.content_writer import AIContentWriter, ContentRequest
from src.ai.seo_optimizer import AISEOOptimizer
from src.ai.models import get_available_models, AIProvider

router = APIRouter(prefix="/ai", tags=["AI Content"])


# ---- Request Schemas ----

class AIGenerateRequest(BaseModel):
    topic: str
    keyword: str
    content_type: str = "article"
    secondary_keywords: str = ""
    word_count: int = 1500
    tone: str = "professional"
    audience: str = "general"
    language: str = "en"
    instructions: str = ""
    original_content: str = ""
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096


class AIMultiGenerateRequest(BaseModel):
    topic: str
    keyword: str
    content_type: str = "article"
    secondary_keywords: str = ""
    word_count: int = 1500
    tone: str = "professional"
    audience: str = "general"
    language: str = "en"
    instructions: str = ""
    models: List[dict]  # [{"provider": "openai", "model_id": "gpt-4o-mini"}, ...]


class AIOptimizeRequest(BaseModel):
    content: str
    keyword: str
    secondary_keywords: str = ""
    url: str = ""
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class AIImproveRequest(BaseModel):
    content: str
    keyword: str
    secondary_keywords: str = ""
    goals: str = "Improve keyword placement, readability, and structure"
    language: str = "en"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class AITitleRequest(BaseModel):
    topic: str
    keyword: str
    content_type: str = "article"
    language: str = "en"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


# ---- API Endpoints ----

@router.get("/models", response_model=ApiResponse)
async def list_models(provider: Optional[str] = None):
    """List available AI models, optionally filtered by provider."""
    if provider:
        try:
            ai_provider = AIProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        models = get_available_models(ai_provider)
    else:
        models = get_available_models()

    return ApiResponse(
        success=True,
        data={
            "models": [m.to_dict() for m in models],
            "total": len(models),
            "providers": [p.value for p in AIProvider],
        },
    )


@router.post("/generate", response_model=ApiResponse)
async def generate_content(request: AIGenerateRequest):
    """Generate SEO-optimized content using AI."""
    writer = AIContentWriter()

    content_request = ContentRequest(
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
        provider=request.provider,
        model_id=request.model_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    result = await writer.generate(content_request)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Generation failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/generate/compare", response_model=ApiResponse)
async def generate_compare(request: AIMultiGenerateRequest):
    """Generate content with multiple AI models for comparison."""
    if len(request.models) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 models for comparison")

    writer = AIContentWriter()

    base_request = ContentRequest(
        topic=request.topic,
        keyword=request.keyword,
        content_type=request.content_type,
        secondary_keywords=request.secondary_keywords,
        word_count=request.word_count,
        tone=request.tone,
        audience=request.audience,
        language=request.language,
        instructions=request.instructions,
    )

    results = await writer.generate_multiple(base_request, request.models)

    return ApiResponse(
        success=True,
        data={
            "results": [r.to_dict() for r in results],
            "total_models": len(results),
            "best_score": max((r.seo_score or 0) for r in results) if results else 0,
        },
    )


@router.post("/optimize/analyze", response_model=ApiResponse)
async def optimize_analyze(request: AIOptimizeRequest):
    """Analyze content and get AI-powered SEO optimization suggestions."""
    optimizer = AISEOOptimizer(
        provider=request.provider,
        model_id=request.model_id,
    )

    result = await optimizer.analyze(
        content=request.content,
        keyword=request.keyword,
        secondary_keywords=request.secondary_keywords,
        url=request.url,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Analysis failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/optimize/improve", response_model=ApiResponse)
async def optimize_improve(request: AIImproveRequest):
    """Rewrite and improve content for better SEO using AI."""
    optimizer = AISEOOptimizer(
        provider=request.provider,
        model_id=request.model_id,
    )

    result = await optimizer.improve_content(
        content=request.content,
        keyword=request.keyword,
        secondary_keywords=request.secondary_keywords,
        goals=request.goals,
        language=request.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Improvement failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/optimize/titles", response_model=ApiResponse)
async def generate_titles(request: AITitleRequest):
    """Generate multiple SEO-optimized title suggestions."""
    optimizer = AISEOOptimizer(
        provider=request.provider,
        model_id=request.model_id,
    )

    result = await optimizer.generate_title_suggestions(
        topic=request.topic,
        keyword=request.keyword,
        content_type=request.content_type,
        language=request.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Title generation failed")

    return ApiResponse(success=True, data=result.to_dict())
