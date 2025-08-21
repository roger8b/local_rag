from abc import ABC, abstractmethod
from typing import List
from src.models.api_models import DocumentSource


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, question: str, sources: List[DocumentSource]) -> str:
        """
        Generate a response using the LLM provider
        
        Args:
            question: The user's question
            sources: List of document sources for context
            
        Returns:
            Generated response as string
        """
        pass
    
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