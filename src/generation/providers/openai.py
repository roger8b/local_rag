import openai
from typing import List
from src.config.settings import settings
from src.models.api_models import DocumentSource
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY é obrigatória para usar o provedor OpenAI")
        
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate_response(self, question: str, sources: List[DocumentSource]) -> str:
        """Generate response using OpenAI LLM"""
        try:
            prompt = self._build_prompt(question, sources)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é um assistente especializado em responder perguntas baseado em documentos fornecidos."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except openai.AuthenticationError:
            raise Exception("Erro de autenticação OpenAI: Chave de API inválida")
        except openai.RateLimitError:
            raise Exception("Erro de rate limit OpenAI: Muitas requisições")
        except openai.APIError as e:
            raise Exception(f"Erro da API OpenAI: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao gerar resposta com OpenAI: {str(e)}")