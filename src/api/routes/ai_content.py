"""AI Content Generation & Optimization API routes."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.schemas import ApiResponse
from src.ai.content_writer import AIContentWriter, ContentRequest
from src.ai.seo_optimizer import AISEOOptimizer
from src.ai.models import get_available_models, AIProvider
from src.utils.config import settings

router = APIRouter(prefix="/ai", tags=["AI Content"])


@router.get("/test-keys", response_model=ApiResponse)
async def test_api_keys(admin_key: Optional[str] = None):
    """Test which API keys are configured and valid. Requires ADMIN_SECRET_KEY."""
    import httpx

    # Security: require admin key to access this endpoint
    admin_secret = settings.admin_secret_key
    if not admin_secret or admin_key != admin_secret:
        raise HTTPException(status_code=403, detail="Access denied. Provide ?admin_key=YOUR_SECRET")

    results = {}

    # Test OpenAI
    if settings.openai_api_key:
        base_url = settings.openai_base_url or "https://api.openai.com/v1"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                )
                results["openai"] = {"configured": True, "valid": r.status_code == 200, "status": r.status_code, "base_url": base_url}
        except Exception as e:
            results["openai"] = {"configured": True, "valid": False, "error": str(e)}
    else:
        results["openai"] = {"configured": False, "valid": False}

    # Test Anthropic
    if settings.anthropic_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={"model": "claude-3-5-haiku-20241022", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]},
                )
                results["anthropic"] = {"configured": True, "valid": r.status_code == 200, "status": r.status_code}
        except Exception as e:
            results["anthropic"] = {"configured": True, "valid": False, "error": str(e)}
    else:
        results["anthropic"] = {"configured": False, "valid": False}

    # Test Groq
    if settings.groq_api_key:
        results["groq"] = {"configured": True, "valid": None, "note": "Key present, not tested"}
    else:
        results["groq"] = {"configured": False, "valid": False}

    # Test Gemini
    if settings.gemini_api_key:
        results["gemini"] = {"configured": True, "valid": None, "note": "Key present, not tested"}
    else:
        results["gemini"] = {"configured": False, "valid": False}

    # Test DeepSeek
    if settings.deepseek_api_key:
        results["deepseek"] = {"configured": True, "valid": None, "note": "Key present, not tested"}
    else:
        results["deepseek"] = {"configured": False, "valid": False}

    return ApiResponse(success=True, data={"keys": results})


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



# ========================================
# New Feature Routes: Research, Auto-Write, Edit, Test
# ========================================

# ---- Additional Request Schemas ----

class KeywordResearchRequest(BaseModel):
    keyword: str
    niche: str = "general"
    market: str = "global"
    language: str = "en"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class SERPAnalysisRequest(BaseModel):
    keyword: str
    market: str = "global"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class KeywordClusterRequest(BaseModel):
    keywords: List[str]
    niche: str = "general"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class AutoWriteRequest(BaseModel):
    topic: str
    keyword: str
    secondary_keywords: str = ""
    word_count: int = 1500
    tone: str = "professional"
    audience: str = "general"
    language: str = "en"
    niche: str = "general"
    skip_research: bool = False
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class AutoOutlineRequest(BaseModel):
    topic: str
    keyword: str
    secondary_keywords: str = ""
    word_count: int = 1500
    tone: str = "professional"
    audience: str = "general"
    language: str = "en"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class EditorRewriteRequest(BaseModel):
    content: str
    keyword: str
    goals: str = "Improve readability and SEO"
    tone: str = "professional"
    language: str = "en"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class EditorReadabilityRequest(BaseModel):
    content: str
    reading_level: str = "8th grade"
    language: str = "en"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class EditorSEOFixRequest(BaseModel):
    content: str
    keyword: str
    secondary_keywords: str = ""
    issues: Optional[List[str]] = None
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class EditorABRequest(BaseModel):
    original: str
    keyword: str
    element_type: str = "title"
    goal: str = "Increase CTR"
    num_variations: int = 3
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class EditorExpandRequest(BaseModel):
    content: str
    keyword: str
    additional_words: int = 300
    expansion_type: str = "examples and details"
    language: str = "en"
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class ContentTestRequest(BaseModel):
    content: str
    keyword: str
    secondary_keywords: str = ""
    meta_title: str = ""
    meta_description: str = ""
    url: str = ""
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"


class ContentTestQuickRequest(BaseModel):
    content: str
    keyword: str
    secondary_keywords: str = ""
    meta_title: str = ""
    meta_description: str = ""


# ---- Keyword Research Endpoints ----

@router.post("/research/keyword", response_model=ApiResponse)
async def research_keyword(request: KeywordResearchRequest):
    """Perform comprehensive keyword research."""
    from src.ai.keyword_researcher import KeywordResearcher

    researcher = KeywordResearcher(provider=request.provider, model_id=request.model_id)
    result = await researcher.research(
        keyword=request.keyword,
        niche=request.niche,
        market=request.market,
        language=request.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Research failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/research/serp", response_model=ApiResponse)
async def analyze_serp(request: SERPAnalysisRequest):
    """Analyze SERP landscape for a keyword."""
    from src.ai.keyword_researcher import KeywordResearcher

    researcher = KeywordResearcher(provider=request.provider, model_id=request.model_id)
    result = await researcher.analyze_serp(keyword=request.keyword, market=request.market)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "SERP analysis failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/research/cluster", response_model=ApiResponse)
async def cluster_keywords(request: KeywordClusterRequest):
    """Group keywords into topic clusters."""
    from src.ai.keyword_researcher import KeywordResearcher

    researcher = KeywordResearcher(provider=request.provider, model_id=request.model_id)
    result = await researcher.cluster_keywords(keywords=request.keywords, niche=request.niche)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Clustering failed")

    return ApiResponse(success=True, data=result.to_dict())


# ---- Auto Writer Endpoints ----

@router.post("/auto-write", response_model=ApiResponse)
async def auto_write_article(request: AutoWriteRequest):
    """Auto-write a complete article (Research → Outline → Draft → Optimize)."""
    from src.ai.auto_writer import AutoWriter

    writer = AutoWriter(provider=request.provider, model_id=request.model_id)
    result = await writer.write_article(
        topic=request.topic,
        keyword=request.keyword,
        secondary_keywords=request.secondary_keywords,
        word_count=request.word_count,
        tone=request.tone,
        audience=request.audience,
        language=request.language,
        niche=request.niche,
        skip_research=request.skip_research,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Auto-write failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/auto-write/outline", response_model=ApiResponse)
async def auto_write_outline(request: AutoOutlineRequest):
    """Create an article outline only (for review before full generation)."""
    from src.ai.auto_writer import AutoWriter

    writer = AutoWriter(provider=request.provider, model_id=request.model_id)
    result = await writer.create_outline_only(
        topic=request.topic,
        keyword=request.keyword,
        secondary_keywords=request.secondary_keywords,
        word_count=request.word_count,
        tone=request.tone,
        audience=request.audience,
        language=request.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Outline generation failed")

    return ApiResponse(success=True, data=result.to_dict())


# ---- Content Editor Endpoints ----

@router.post("/editor/rewrite", response_model=ApiResponse)
async def editor_rewrite(request: EditorRewriteRequest):
    """Rewrite a section for better SEO and readability."""
    from src.ai.content_editor import ContentEditor

    editor = ContentEditor(provider=request.provider, model_id=request.model_id)
    result = await editor.rewrite_section(
        section_content=request.content,
        keyword=request.keyword,
        goals=request.goals,
        tone=request.tone,
        language=request.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Rewrite failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/editor/readability", response_model=ApiResponse)
async def editor_readability(request: EditorReadabilityRequest):
    """Improve content readability."""
    from src.ai.content_editor import ContentEditor

    editor = ContentEditor(provider=request.provider, model_id=request.model_id)
    result = await editor.improve_readability(
        content=request.content,
        reading_level=request.reading_level,
        language=request.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Readability improvement failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/editor/fix-seo", response_model=ApiResponse)
async def editor_fix_seo(request: EditorSEOFixRequest):
    """Auto-detect and fix SEO issues in content."""
    from src.ai.content_editor import ContentEditor

    editor = ContentEditor(provider=request.provider, model_id=request.model_id)
    result = await editor.fix_seo_issues(
        content=request.content,
        keyword=request.keyword,
        secondary_keywords=request.secondary_keywords,
        issues=request.issues,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "SEO fix failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/editor/ab-variations", response_model=ApiResponse)
async def editor_ab_variations(request: EditorABRequest):
    """Generate A/B test variations of a content element."""
    from src.ai.content_editor import ContentEditor

    editor = ContentEditor(provider=request.provider, model_id=request.model_id)
    result = await editor.generate_ab_variations(
        original=request.original,
        keyword=request.keyword,
        element_type=request.element_type,
        goal=request.goal,
        num_variations=request.num_variations,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "A/B generation failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/editor/expand", response_model=ApiResponse)
async def editor_expand(request: EditorExpandRequest):
    """Expand content with more detail and examples."""
    from src.ai.content_editor import ContentEditor

    editor = ContentEditor(provider=request.provider, model_id=request.model_id)
    result = await editor.expand_content(
        content=request.content,
        keyword=request.keyword,
        additional_words=request.additional_words,
        expansion_type=request.expansion_type,
        language=request.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Expansion failed")

    return ApiResponse(success=True, data=result.to_dict())


# ---- Content Testing Endpoints ----

@router.post("/test/full", response_model=ApiResponse)
async def test_content_full(request: ContentTestRequest):
    """Run full content test (SEO, readability, plagiarism, SERP preview)."""
    from src.ai.content_tester import ContentTester

    tester = ContentTester(provider=request.provider, model_id=request.model_id)
    result = await tester.full_test(
        content=request.content,
        keyword=request.keyword,
        secondary_keywords=request.secondary_keywords,
        meta_title=request.meta_title,
        meta_description=request.meta_description,
        url=request.url,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Test failed")

    return ApiResponse(success=True, data=result.to_dict())


@router.post("/test/quick", response_model=ApiResponse)
async def test_content_quick(request: ContentTestQuickRequest):
    """Quick SEO test (instant, no AI calls - just scoring)."""
    from src.ai.content_tester import ContentTester

    tester = ContentTester()
    result = tester.test_seo_only(
        content=request.content,
        keyword=request.keyword,
        secondary_keywords=request.secondary_keywords,
        meta_title=request.meta_title,
        meta_description=request.meta_description,
    )

    return ApiResponse(success=True, data=result.to_dict())
