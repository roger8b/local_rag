#!/usr/bin/env python3
"""
Teste direto do provider OpenAI
"""
import asyncio
import os
import sys
sys.path.append('src')

from src.generation.providers.openai import OpenAIProvider
from src.models.api_models import DocumentSource

async def test_openai():
    """Teste direto do OpenAI provider"""
    print("🤖 Testando OpenAI Provider diretamente...")
    
    # Configurar API key
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
    
    if not os.environ['OPENAI_API_KEY']:
        print("❌ OPENAI_API_KEY não configurada")
        return
    
    # Criar fontes fictícias baseadas no conteúdo Pokemon
    sources = [
        DocumentSource(
            text="A jornada de um treinador em Kanto tradicionalmente começa no laboratório do Professor Samuel Carvalho. Lá, eles escolhem um de três parceiros: Bulbasaur (Grama/Venenoso), Charmander (Fogo), ou Squirtle (Água).",
            score=0.95
        ),
        DocumentSource(
            text="Ash Ketchum, da cidade de Pallet, é um protagonista cuja meta é se tornar um Mestre Pokémon. Seu primeiro Pokémon e amigo inseparável é o Pikachu.",
            score=0.90
        )
    ]
    
    try:
        provider = OpenAIProvider()
        print(f"✅ Provider OpenAI inicializado com modelo: {provider.model}")
        
        question = "Quais são os Pokémon iniciais de Kanto?"
        print(f"📋 Pergunta: {question}")
        
        response = await provider.generate_response(question, sources)
        print(f"✅ Resposta OpenAI: {response}")
        
        # Log para arquivo
        with open("/tmp/openai_test.log", "w", encoding="utf-8") as f:
            f.write(f"Pergunta: {question}\n")
            f.write(f"Resposta: {response}\n")
            f.write(f"Modelo: {provider.model}\n")
        
        print("📁 Log salvo em: /tmp/openai_test.log")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai())