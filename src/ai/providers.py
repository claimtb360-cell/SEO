"""AI provider clients - unified interface for multiple AI APIs."""

from typing import Optional, Dict, Any, AsyncGenerator
from abc import ABC, abstractmethod

from src.utils.config import settings
from src.utils.logger import logger


class BaseAIProvider(ABC):
    """Base class for AI provider implementations."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """Generate text from the AI model."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream text generation from the AI model."""
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider (GPT-4o, GPT-4 Turbo, etc.)."""

    def __init__(self, model_id: str = "gpt-4o-mini"):
        self.model_id = model_id
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url or "https://api.openai.com/v1"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> str:
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream(self, prompt: str, system_prompt: Optional[str] = None,
                     max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass


class AnthropicProvider(BaseAIProvider):
    """Anthropic API provider (Claude models)."""

    def __init__(self, model_id: str = "claude-sonnet-4-20250514"):
        self.model_id = model_id
        self.api_key = settings.anthropic_api_key

    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> str:
        import httpx

        body: Dict[str, Any] = {
            "model": self.model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def stream(self, prompt: str, system_prompt: Optional[str] = None,
                     max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        import httpx
        import json

        body: Dict[str, Any] = {
            "model": self.model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        if system_prompt:
            body["system"] = system_prompt

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=body,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            if chunk.get("type") == "content_block_delta":
                                text = chunk.get("delta", {}).get("text", "")
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            pass


class GoogleProvider(BaseAIProvider):
    """Google Gemini API provider."""

    def __init__(self, model_id: str = "gemini-2.0-flash"):
        self.model_id = model_id
        self.api_key = settings.gemini_api_key

    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> str:
        import httpx

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": contents,
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def stream(self, prompt: str, system_prompt: Optional[str] = None,
                     max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        # Gemini streaming uses SSE
        result = await self.generate(prompt, system_prompt, max_tokens, temperature)
        # Simulate streaming for compatibility
        for word in result.split(" "):
            yield word + " "


class GroqProvider(BaseAIProvider):
    """Groq API provider (ultra-fast inference)."""

    def __init__(self, model_id: str = "llama-3.3-70b-versatile"):
        self.model_id = model_id
        self.api_key = settings.groq_api_key

    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> str:
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream(self, prompt: str, system_prompt: Optional[str] = None,
                     max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        import httpx
        import json

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass


class MistralProvider(BaseAIProvider):
    """Mistral AI provider."""

    def __init__(self, model_id: str = "mistral-large-latest"):
        self.model_id = model_id
        self.api_key = settings.mistral_api_key

    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> str:
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream(self, prompt: str, system_prompt: Optional[str] = None,
                     max_tokens: int = 4096, temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        result = await self.generate(prompt, system_prompt, max_tokens, temperature)
        for word in result.split(" "):
            yield word + " "


def get_provider(provider: str, model_id: str) -> BaseAIProvider:
    """Factory function to get the appropriate AI provider."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "groq": GroqProvider,
        "mistral": MistralProvider,
    }

    provider_class = providers.get(provider)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider}. Available: {list(providers.keys())}")

    return provider_class(model_id=model_id)
