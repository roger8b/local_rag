import httpx
from typing import List
from src.config.settings import settings
from src.models.api_models import DocumentSource
from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama LLM provider implementation"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.llm_model
    
    async def generate_response(self, question: str, sources: List[DocumentSource]) -> str:
        """Generate response using Ollama LLM"""
        try:
            prompt = self._build_prompt(question, sources)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 1000
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["response"].strip()
                
        except Exception as e:
            raise Exception(f"Error generating response with Ollama: {str(e)}")