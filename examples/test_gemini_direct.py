#!/usr/bin/env python3
"""
Teste direto do provider Gemini
"""
import asyncio
import os
import sys
sys.path.append('src')

# Carregar variáveis do .env
from dotenv import load_dotenv
load_dotenv()

from src.generation.providers.gemini import GeminiProvider
from src.models.api_models import DocumentSource

async def test_gemini():
    """Teste direto do Gemini provider"""
    print("🧠 Testando Gemini Provider diretamente...")
    
    # Configurar API key
    google_key = os.getenv('GOOGLE_API_KEY', '')
    if not google_key:
        print("❌ GOOGLE_API_KEY não configurada")
        return
    
    os.environ['GOOGLE_API_KEY'] = google_key
    
    # Criar fontes fictícias baseadas no conteúdo Pokemon
    sources = [
        DocumentSource(
            text="A jornada de um treinador em Kanto tradicionalmente começa no laboratório do Professor Samuel Carvalho. Lá, eles escolhem um de três parceiros: Bulbasaur (Grama/Venenoso), Charmander (Fogo), ou Squirtle (Água).",
            score=0.95
        ),
        DocumentSource(
            text="Ash Ketchum, da cidade de Pallet, é um protagonista cuja meta é se tornar um Mestre Pokémon. Seu primeiro Pokémon e amigo inseparável é o Pikachu.",
            score=0.90
        ),
        DocumentSource(
            text="Eevee pode evoluir para múltiplas formas diferentes. Com uma Pedra da Água, evolui para Vaporeon. Com uma Pedra do Trovão, torna-se Jolteon. Com uma Pedra de Fogo, transforma-se em Flareon.",
            score=0.88
        )
    ]
    
    try:
        provider = GeminiProvider()
        print(f"✅ Provider Gemini inicializado")
        
        questions = [
            "Quais são os Pokémon iniciais de Kanto?",
            "Como Eevee evolui para suas diferentes formas?",
            "Qual é o objetivo de Ash Ketchum?"
        ]
        
        # Log para arquivo
        with open("/tmp/gemini_test.log", "w", encoding="utf-8") as f:
            f.write("=== Teste Gemini Provider ===\n\n")
            
            for i, question in enumerate(questions, 1):
                print(f"📋 Pergunta {i}: {question}")
                f.write(f"PERGUNTA {i}: {question}\n")
                f.write("="*40 + "\n")
                
                try:
                    response = await provider.generate_response(question, sources)
                    print(f"✅ Resposta: {response[:100]}...")
                    f.write(f"RESPOSTA: {response}\n")
                    
                except Exception as e:
                    print(f"❌ Erro na pergunta {i}: {str(e)}")
                    f.write(f"ERRO: {str(e)}\n")
                
                f.write("\n" + "="*60 + "\n\n")
        
        print("📁 Log salvo em: /tmp/gemini_test.log")
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_gemini())