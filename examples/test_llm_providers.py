#!/usr/bin/env python3
"""
Script para testar todos os providers LLM com perguntas sobre Pokemon
usando a API query. Gera log temporal das respostas para análise.
"""
import httpx
import json
import asyncio
from datetime import datetime
import os
import sys

# Lista de perguntas para testar o contexto Pokemon
POKEMON_QUESTIONS = [
    "Quais são os Pokémon iniciais de Kanto?",
    "Como Eevee evolui para suas diferentes formas?", 
    "Quem é o líder da Equipe Rocket?",
    "Qual é o principal objetivo de Ash Ketchum?",
    "Quais são os Líderes de Ginásio de Kanto mencionados?",
    "Qual a conexão entre Kanto e Johto?"
]

# Configuração dos providers para teste
PROVIDERS = [
    {
        "name": "Ollama",
        "env_vars": {
            "LLM_PROVIDER": "ollama",
            "EMBEDDING_PROVIDER": "ollama"
        }
    },
    {
        "name": "OpenAI", 
        "env_vars": {
            "LLM_PROVIDER": "openai",
            "EMBEDDING_PROVIDER": "ollama"  # Mantemos Ollama para embeddings
        }
    },
    {
        "name": "Gemini",
        "env_vars": {
            "LLM_PROVIDER": "gemini", 
            "EMBEDDING_PROVIDER": "ollama"  # Mantemos Ollama para embeddings
        }
    }
]

API_BASE_URL = "http://localhost:8000/api/v1"


def setup_environment(provider_config):
    """Configura as variáveis de ambiente para o provider"""
    for key, value in provider_config["env_vars"].items():
        os.environ[key] = value
    print(f"🔧 Configurado para provider: {provider_config['name']}")


def log_response(provider_name, question, response_data, log_file):
    """Salva a resposta no arquivo de log"""
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "provider": provider_name,
        "question": question,
        "response": response_data
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n" + "="*80 + "\n")


async def test_query(question, provider_name, log_file):
    """Testa uma pergunta específica via API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/query",
                json={"question": question},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"  ✅ Pergunta respondida com sucesso")
                print(f"  📝 Resposta: {response_data['answer'][:100]}...")
                
                log_response(provider_name, question, response_data, log_file)
                return True
            else:
                error_data = {
                    "error": f"HTTP {response.status_code}",
                    "detail": response.text
                }
                print(f"  ❌ Erro HTTP {response.status_code}: {response.text}")
                log_response(provider_name, question, error_data, log_file)
                return False
                
    except Exception as e:
        error_data = {
            "error": "Exception",
            "detail": str(e)
        }
        print(f"  💥 Exceção: {str(e)}")
        log_response(provider_name, question, error_data, log_file)
        return False


async def test_provider(provider_config, log_file):
    """Testa todas as perguntas para um provider específico"""
    provider_name = provider_config["name"]
    print(f"\n🚀 Testando provider: {provider_name}")
    print("="*50)
    
    # Configurar ambiente (nota: isso requer restart do servidor para surtir efeito)
    setup_environment(provider_config)
    
    # Aguardar um pouco para possível restart/recarga
    print("⏳ Aguardando configuração...")
    await asyncio.sleep(2)
    
    success_count = 0
    total_questions = len(POKEMON_QUESTIONS)
    
    for i, question in enumerate(POKEMON_QUESTIONS, 1):
        print(f"\n📋 Pergunta {i}/{total_questions}: {question}")
        
        success = await test_query(question, provider_name, log_file)
        if success:
            success_count += 1
    
    print(f"\n📊 Resultado para {provider_name}: {success_count}/{total_questions} perguntas respondidas com sucesso")
    return success_count


def create_log_file():
    """Cria arquivo de log temporário"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"/tmp/llm_provider_test_{timestamp}.json"
    
    # Inicializar o arquivo de log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"# Teste de Providers LLM - {datetime.now().isoformat()}\n")
        f.write(f"# Arquivo Pokemon carregado com {len(POKEMON_QUESTIONS)} perguntas de teste\n")
        f.write("="*80 + "\n")
    
    return log_file


async def main():
    """Função principal"""
    print("🧪 Iniciando Teste de Providers LLM com Contexto Pokemon")
    print("="*60)
    
    # Criar arquivo de log
    log_file = create_log_file()
    print(f"📁 Log será salvo em: {log_file}")
    
    total_success = 0
    total_tests = 0
    
    # Testar cada provider
    for provider_config in PROVIDERS:
        success_count = await test_provider(provider_config, log_file)
        total_success += success_count
        total_tests += len(POKEMON_QUESTIONS)
    
    # Resultado final
    print(f"\n🎯 RESULTADO FINAL")
    print("="*30)
    print(f"✅ Sucesso: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
    print(f"📁 Log completo: {log_file}")
    
    # Mostrar comando para visualizar o log
    print(f"\n💡 Para visualizar o log:")
    print(f"   cat {log_file}")
    print(f"   jq . {log_file}")


if __name__ == "__main__":
    asyncio.run(main())