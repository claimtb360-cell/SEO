"""AI model definitions and provider configuration."""

from dataclasses import dataclass
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


# All supported models
AVAILABLE_MODELS: List[AIModel] = [
    # OpenAI
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        max_tokens=16384,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        description="Most capable OpenAI model, best for complex SEO content",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        max_tokens=16384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Fast and affordable, good for bulk content generation",
    ),
    AIModel(
        provider=AIProvider.OPENAI,
        model_id="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        max_tokens=4096,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        description="High quality content with broad knowledge",
    ),
    # Anthropic (Claude)
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
    # Google (Gemini)
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        max_tokens=8192,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
        description="Very fast, good for bulk SEO tasks",
    ),
    AIModel(
        provider=AIProvider.GOOGLE,
        model_id="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        max_tokens=8192,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        description="High quality with large context window",
    ),
    # Groq (fast inference)
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
        model_id="mixtral-8x7b-32768",
        display_name="Mixtral 8x7B (Groq)",
        max_tokens=32768,
        cost_per_1k_input=0.00024,
        cost_per_1k_output=0.00024,
        description="Large context, fast and affordable",
    ),
    # Mistral
    AIModel(
        provider=AIProvider.MISTRAL,
        model_id="mistral-large-latest",
        display_name="Mistral Large",
        max_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.009,
        description="Multilingual SEO content generation",
    ),
    # Cohere
    AIModel(
        provider=AIProvider.COHERE,
        model_id="command-r-plus",
        display_name="Command R+",
        max_tokens=4096,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        description="Enterprise-grade content with built-in RAG support",
    ),
]


def get_available_models(provider: Optional[AIProvider] = None) -> List[AIModel]:
    """Get list of available AI models, optionally filtered by provider."""
    if provider:
        return [m for m in AVAILABLE_MODELS if m.provider == provider]
    return AVAILABLE_MODELS


def get_model(model_id: str) -> Optional[AIModel]:
    """Get a model by its ID."""
    for model in AVAILABLE_MODELS:
        if model.model_id == model_id:
            return model
    return None
