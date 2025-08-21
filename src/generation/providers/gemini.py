import google.generativeai as genai
from typing import List
from src.config.settings import settings
from src.models.api_models import DocumentSource
from .base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation"""
    
    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY é obrigatória para usar o provedor Gemini")
        
        # Configure the Gemini API
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.google_model)
    
    async def generate_response(self, question: str, sources: List[DocumentSource]) -> str:
        """Generate response using Google Gemini LLM"""
        try:
            prompt = self._build_prompt(question, sources)
            
            # Add system instruction for Gemini
            system_instruction = "Você é um assistente especializado em responder perguntas baseado em documentos fornecidos."
            full_prompt = f"{system_instruction}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=1000,
                )
            )
            
            if not response.text:
                raise Exception("Gemini retornou resposta vazia")
            
            return response.text.strip()
            
        except Exception as e:
            # Handle various Gemini-specific errors
            error_msg = str(e).lower()
            
            if "api_key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
                raise Exception("Erro de autenticação Gemini: Chave de API inválida")
            elif "quota" in error_msg or "rate" in error_msg or "limit" in error_msg:
                raise Exception("Erro de rate limit Gemini: Muitas requisições")
            elif "safety" in error_msg or "blocked" in error_msg:
                raise Exception("Erro de segurança Gemini: Conteúdo bloqueado por políticas de segurança")
            else:
                raise Exception(f"Erro ao gerar resposta com Gemini: {str(e)}")