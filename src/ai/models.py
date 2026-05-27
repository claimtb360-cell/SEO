"""AI model definitions and provider configuration."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    MISTRAL = "mistral"
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    LOCAL = "local"  # Ollama / local models


@dataclass
class AIModel:
    """Represents an AI model configuration."""
    provider: AIProvider
    model_id: str
    display_name: str
    max_tokens: int = 4096
    supports_streaming: bool = True
    supports_system_prompt: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "max_tokens": self.max_tokens,
            "supports_streaming": self.supports_streaming,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "description": self.description,
        }


# All supported models (updated May 2026)
AVAILABLE_MODELS: List[AIModel] = [
    # ─── OpenAI (May 2026) ───────────────────────────────────────────────────────
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-5.5",
        display_name="GPT-5.5",
        max_tokens=32768,
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.015,
        description="Latest flagship OpenAI model (May 2026), best for complex SEO content",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-5.5-instant",
        display_name="GPT-5.5 Instant",
        max_tokens=16384,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.002,
        description="Default ChatGPT model, fast and cheap — great for everyday SEO tasks",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-5.4",
        display_name="GPT-5.4",
        max_tokens=32768,
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.015,
        description="Previous flagship with 1.05M context window, excellent for large SEO audits",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-5.2",
        display_name="GPT-5.2",
        max_tokens=32768,
        cost_per_1k_input=0.002,
        cost_per_1k_output=0.01,
        description="Newest frontier model (May 27, 2026), cutting-edge capabilities",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        max_tokens=16384,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        description="Capable multimodal model, still widely available",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        max_tokens=16384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Budget option for bulk content generation",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="o3",
        display_name="O3",
        max_tokens=32768,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.04,
        description="Advanced reasoning model for complex SEO strategy and analysis",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="o4-mini",
        display_name="O4 Mini",
        max_tokens=16384,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.004,
        description="Compact reasoning model, fast for analysis tasks",
    ),
    # ─── Google Gemini (Google I/O 2026, May 19) ─────────────────────────────────
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-3.5-flash",
        display_name="Gemini 3.5 Flash",
        max_tokens=16384,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.001,
        description="Newest Gemini (May 2026), strongest for coding and agents",
    ),
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-3.1-pro",
        display_name="Gemini 3.1 Pro",
        max_tokens=16384,
        cost_per_1k_input=0.002,
        cost_per_1k_output=0.008,
        description="Latest pro iteration, excellent for detailed SEO analysis",
    ),
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-3-pro",
        display_name="Gemini 3 Pro",
        max_tokens=16384,
        cost_per_1k_input=0.00175,
        cost_per_1k_output=0.007,
        description="Multimodal reasoning, great for image-based SEO audits",
    ),
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-3-flash",
        display_name="Gemini 3 Flash",
        max_tokens=8192,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Fast Gemini model for quick SEO tasks",
    ),
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        max_tokens=8192,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Stable and recommended for new projects",
    ),
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        max_tokens=16384,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        description="Stable pro model with large context window",
    ),
    # ─── Anthropic (Claude, latest May 2025 releases) ────────────────────────────
    AIModel(
        provider=AIProvider.ANTHROPIC,
        model_id="claude-opus-4-20250514",
        display_name="Claude Opus 4",
        max_tokens=8192,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        description="Most capable Claude model for premium SEO content",
    ),
    AIModel(
        provider=AIProvider.ANTHROPIC,
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        max_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        description="Excellent for long-form SEO articles and natural writing",
    ),
    AIModel(
        provider=AIProvider.ANTHROPIC,
        model_id="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        max_tokens=8192,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.005,
        description="Fast and cost-effective for quick content drafts",
    ),
    # ─── DeepSeek ────────────────────────────────────────────────────────────────
    AIModel(
        provider=AIProvider.DEEPSEEK,
        model_id="deepseek-chat",
        display_name="DeepSeek Chat",
        max_tokens=8192,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        description="Affordable high-quality chat model for SEO content",
    ),
    AIModel(
        provider=AIProvider.DEEPSEEK,
        model_id="deepseek-reasoner",
        display_name="DeepSeek Reasoner",
        max_tokens=8192,
        cost_per_1k_input=0.00055,
        cost_per_1k_output=0.00219,
        description="Advanced reasoning for complex SEO strategy and analysis",
    ),
    # ─── Groq (ultra-fast inference) ─────────────────────────────────────────────
    AIModel(
        provider=AIProvider.GROQ,
        model_id="llama-3.3-70b-versatile",
        display_name="Llama 3.3 70B (Groq)",
        max_tokens=8192,
        cost_per_1k_input=0.00059,
        cost_per_1k_output=0.00079,
        description="Ultra-fast inference, great for real-time content suggestions",
    ),
    AIModel(
        provider=AIProvider.GROQ,
        model_id="llama-4-scout-17b-16e-instruct",
        display_name="Llama 4 Scout 17B (Groq)",
        max_tokens=8192,
        cost_per_1k_input=0.00011,
        cost_per_1k_output=0.00034,
        description="Latest Llama model on Groq, fast and capable",
    ),
    AIModel(
        provider=AIProvider.GROQ,
        model_id="mixtral-8x7b-32768",
        display_name="Mixtral 8x7B (Groq)",
        max_tokens=32768,
        cost_per_1k_input=0.00024,
        cost_per_1k_output=0.00024,
        description="Large context window, fast and affordable",
    ),
    # ─── Mistral ─────────────────────────────────────────────────────────────────
    AIModel(
        provider=AIProvider.MISTRAL,
        model_id="mistral-large-latest",
        display_name="Mistral Large",
        max_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.009,
        description="Top-tier multilingual SEO content generation",
    ),
    AIModel(
        provider=AIProvider.MISTRAL,
        model_id="mistral-small-latest",
        display_name="Mistral Small",
        max_tokens=8192,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.003,
        description="Affordable multilingual content drafts",
    ),
]

# Storage for custom models added at runtime
_custom_models: List[AIModel] = []


def get_available_models(provider: Optional[AIProvider] = None) -> List[AIModel]:
    """Get list of available AI models, optionally filtered by provider."""
    if provider:
        return [m for m in AVAILABLE_MODELS if m.provider == provider]
    return AVAILABLE_MODELS


def get_model(model_id: str) -> Optional[AIModel]:
    """Get a model by its ID."""
    for model in AVAILABLE_MODELS + _custom_models:
        if model.model_id == model_id:
            return model
    return None


def get_all_models(include_custom: bool = True) -> List[AIModel]:
    """Return AVAILABLE_MODELS plus any custom models.

    Args:
        include_custom: Whether to include dynamically added custom models.

    Returns:
        Combined list of built-in and custom AI models.
    """
    if include_custom:
        return AVAILABLE_MODELS + _custom_models
    return list(AVAILABLE_MODELS)


async def fetch_models_from_provider(
    provider: str, api_key: str, base_url: str = None
) -> List[dict]:
    """Fetch available models dynamically from a provider's /v1/models endpoint.

    Args:
        provider: The provider name (e.g., 'openai', 'deepseek').
        api_key: The API key for authentication.
        base_url: Optional base URL override. Defaults to provider's standard URL.

    Returns:
        List of model dicts with at least 'id' and 'object' fields.
    """
    import httpx

    default_urls = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "mistral": "https://api.mistral.ai/v1",
    }

    url = base_url or default_urls.get(provider, "https://api.openai.com/v1")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{url}/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

    # OpenAI-compatible APIs return {"data": [...]}
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    elif isinstance(data, list):
        return data
    return []
