from typing import List, Optional, Tuple
import inspect
from src.config.settings import settings
from src.models.api_models import DocumentSource
from src.generation.providers.base import LLMProvider
from src.generation.providers.ollama import OllamaProvider
from src.generation.providers.openai import OpenAIProvider
from src.generation.providers.gemini import GeminiProvider


def create_llm_provider() -> LLMProvider:
    """Factory function to create the appropriate LLM provider based on settings"""
    provider = settings.llm_provider.lower()
    
    if provider == "ollama":
        return OllamaProvider()
    elif provider == "openai":
        return OpenAIProvider()
    elif provider == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Provedor de LLM '{provider}' não suportado")


def create_llm_provider_dynamic(provider_override: Optional[str] = None) -> Tuple[LLMProvider, str]:
    """
    Factory function to create LLM provider with optional override
    
    Args:
        provider_override: Optional provider name to override default settings
        
    Returns:
        Tuple of (provider_instance, provider_name_used)
        
    Raises:
        ValueError: If provider is not supported or configuration is missing
    """
    # Use override if provided, otherwise fall back to settings
    provider_name = provider_override.lower() if provider_override else settings.llm_provider.lower()
    
    # Validate provider is supported
    supported_providers = ["ollama", "openai", "gemini"]
    if provider_name not in supported_providers:
        raise ValueError(
            f"Provedor de LLM '{provider_name}' não suportado. "
            f"Provedores disponíveis: {', '.join(supported_providers)}"
        )
    
    try:
        if provider_name == "ollama":
            return OllamaProvider(), "ollama"
        elif provider_name == "openai":
            return OpenAIProvider(), "openai"
        elif provider_name == "gemini":
            return GeminiProvider(), "gemini"
    except ValueError as e:
        # Re-raise with more context about the provider
        if "API" in str(e) or "key" in str(e).lower():
            raise ValueError(
                f"Erro de configuração para o provedor '{provider_name}': {str(e)}. "
                f"Verifique se as credenciais estão configuradas corretamente."
            )
        raise


class ResponseGenerator:
    def __init__(self, provider_override: Optional[str] = None):
        """
        When no override is provided, initialize provider eagerly using create_llm_provider()
        (keeps compatibility with existing tests). When an override is provided, defer
        provider construction to first use to avoid requiring credentials during __init__.
        """
        if provider_override is None:
            self.provider = create_llm_provider()
            self.provider_name = settings.llm_provider.lower()
        else:
            self.provider = None
            self.provider_name = provider_override.lower()

    def _ensure_provider(self) -> LLMProvider:
        if self.provider is None:
            provider, effective_name = create_llm_provider_dynamic(self.provider_name)
            self.provider = provider
            self.provider_name = effective_name
        return self.provider

    async def generate_response(self, question: str, sources: List[DocumentSource]) -> str:
        provider = self._ensure_provider()
        result = provider.generate_response(question, sources)
        if inspect.isawaitable(result):
            return await result  # type: ignore[no-any-return]
        return result  # type: ignore[no-any-return]

    def get_provider_name(self) -> str:
        return self.provider_name
