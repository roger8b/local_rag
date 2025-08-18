from typing import List
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


class ResponseGenerator:
    def __init__(self):
        self.provider = create_llm_provider()
    
    async def generate_response(self, question: str, sources: List[DocumentSource]) -> str:
        """Generate response using the configured LLM provider"""
        return await self.provider.generate_response(question, sources)