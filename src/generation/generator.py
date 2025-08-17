import httpx
from typing import List
from src.config.settings import settings
from src.models.api_models import DocumentSource


class ResponseGenerator:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.llm_model
    
    def _build_prompt(self, question: str, sources: List[DocumentSource]) -> str:
        """Build the prompt for the LLM using the question and retrieved sources"""
        context = "\n\n".join([
            f"Documento {i+1} (Score: {source.score:.3f}):\n{source.text}"
            for i, source in enumerate(sources)
        ])
        
        prompt = f"""Você é um assistente especializado em responder perguntas baseado em documentos fornecidos.

CONTEXTO:
{context}

PERGUNTA: {question}

INSTRUÇÕES:
- Use apenas as informações fornecidas no contexto acima para responder
- Se a informação não estiver disponível no contexto, diga que não possui informações suficientes
- Seja preciso e conciso em sua resposta
- Cite qual documento utilizou quando relevante

RESPOSTA:"""
        
        return prompt
    
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
            raise Exception(f"Error generating response: {str(e)}")