#!/usr/bin/env python3
"""
Script para verificar configurações do Local RAG System
"""

import os
from pathlib import Path

def check_openai_key():
    """Verifica se a OPENAI_API_KEY está configurada"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        if api_key.startswith("sk-"):
            print(f"✅ OPENAI_API_KEY configurada: {api_key[:8]}...{api_key[-4:]}")
            return True
        else:
            print("❌ OPENAI_API_KEY parece inválida (deve começar com 'sk-')")
            return False
    else:
        print("⚠️  OPENAI_API_KEY não configurada (apenas embeddings locais disponíveis)")
        return False

def check_env_file():
    """Verifica se arquivo .env existe"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print(f"✅ Arquivo .env encontrado: {env_path.absolute()}")
        return True
    elif env_example_path.exists():
        print(f"⚠️  Arquivo .env não encontrado, mas .env.example disponível")
        print(f"   Copie: cp {env_example_path} {env_path}")
        return False
    else:
        print("❌ Nem .env nem .env.example encontrados")
        return False

def check_neo4j_config():
    """Verifica configuração do Neo4j"""
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print(f"🔗 Neo4j URI: {neo4j_uri}")
    print(f"👤 Neo4j User: {neo4j_user}")
    print(f"🔒 Neo4j Password: {'*' * len(neo4j_password)}")
    print(f"🗄️ Neo4j Database: {neo4j_database}")
    return True

def check_ollama_config():
    """Verifica configuração do Ollama"""
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    llm_model = os.getenv("LLM_MODEL", "qwen2:8b")
    
    print(f"🤖 Ollama URL: {ollama_url}")
    print(f"📊 Embedding Model: {embedding_model}")
    print(f"💬 LLM Model: {llm_model}")
    return True

def check_api_url():
    """Verifica configuração da API URL"""
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    print(f"🌐 API URL: {api_url}")

def check_optional_config():
    """Verifica configurações opcionais"""
    redis_url = os.getenv("REDIS_URL")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    debug = os.getenv("DEBUG", "false")
    
    print("🔧 CONFIGURAÇÕES OPCIONAIS:")
    if redis_url:
        print(f"  ✅ Redis: {redis_url}")
    else:
        print("  ⚠️  Redis: Não configurado")
    
    print(f"  📝 Log Level: {log_level}")
    print(f"  🐛 Debug Mode: {debug}")

def main():
    print("🔍 Verificando configurações do Local RAG System...")
    print("=" * 60)
    
    # Verificar arquivo .env
    check_env_file()
    print()
    
    # Verificar Neo4j
    print("🗄️  CONFIGURAÇÕES NEO4J:")
    check_neo4j_config()
    print()
    
    # Verificar Ollama
    print("🤖 CONFIGURAÇÕES OLLAMA:")
    check_ollama_config()
    print()
    
    # Verificar OpenAI API Key
    print("☁️  CONFIGURAÇÕES OPENAI:")
    openai_ok = check_openai_key()
    print()
    
    # Verificar API URL
    print("🌐 CONFIGURAÇÕES DA API:")
    check_api_url()
    print()
    
    # Configurações opcionais
    check_optional_config()
    print()
    
    # Resumo
    print("=" * 60)
    print("📋 RESUMO DO SISTEMA:")
    print("✅ Neo4j: Configurado (banco de dados principal)")
    print("✅ Ollama: Configurado (modelos locais)")
    print(f"✅ API: Configurada ({os.getenv('API_BASE_URL', 'http://localhost:8000')})")
    
    if openai_ok:
        print("✅ OpenAI: Configurado (embeddings rápidos disponíveis)")
        print("🚀 Status: Sistema otimizado para performance")
    else:
        print("⚠️  OpenAI: Não configurado (apenas embeddings locais)")
        print("🏠 Status: Sistema totalmente local (mais lento)")
    
    print("\n📖 PRÓXIMOS PASSOS:")
    if not openai_ok:
        print("• Para embeddings mais rápidos:")
        print("  1. Obtenha API key: https://platform.openai.com/api-keys")
        print("  2. Configure: export OPENAI_API_KEY='sk-your-key'")
        print("  3. Ou adicione no .env: OPENAI_API_KEY=sk-your-key")
    
    print("• Para iniciar o sistema:")
    print("  1. Inicie Neo4j: docker-compose up neo4j -d")
    print("  2. Inicie API: python -m uvicorn src.main:app --reload")
    print("  3. Inicie UI: streamlit run streamlit_app.py")
    
    print("\n💡 Lembrete: Consultas sempre usam modelo local (Ollama)")

if __name__ == "__main__":
    main()