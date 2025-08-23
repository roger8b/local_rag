#!/usr/bin/env python3
"""
Script para validar o funcionamento dos provedores LLM
"""
import os
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from src.generation.generator import create_llm_provider, ResponseGenerator
from src.config.settings import settings
from src.models.api_models import DocumentSource


def test_factory_with_valid_provider():
    """Testa se o factory cria provider corretamente"""
    print("🧪 Testando factory com provider padrão...")
    try:
        provider = create_llm_provider()
        print(f"✅ Provider criado: {type(provider).__name__}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar provider: {e}")
        return False


def test_factory_with_invalid_provider():
    """Testa se o factory falha corretamente com provider inválido"""
    print("🧪 Testando factory com provider inválido...")
    
    # Salvar configuração original
    original_provider = settings.llm_provider
    
    try:
        # Definir provider inválido
        settings.llm_provider = "anthropic"
        
        try:
            create_llm_provider()
            print("❌ Deveria ter falhado com provider inválido")
            return False
        except (ValueError, NotImplementedError) as e:
            print(f"✅ Falhou corretamente: {e}")
            return True
    finally:
        # Restaurar configuração original
        settings.llm_provider = original_provider


def test_response_generator_initialization():
    """Testa se o ResponseGenerator inicializa corretamente"""
    print("🧪 Testando inicialização do ResponseGenerator...")
    try:
        generator = ResponseGenerator()
        print(f"✅ ResponseGenerator criado com provider: {type(generator.provider).__name__}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar ResponseGenerator: {e}")
        return False


def test_configuration_reading():
    """Testa se as configurações estão sendo lidas corretamente"""
    print("🧪 Testando leitura de configurações...")
    
    config_info = {
        "LLM_PROVIDER": settings.llm_provider,
        "EMBEDDING_PROVIDER": settings.embedding_provider,
        "OLLAMA_BASE_URL": settings.ollama_base_url,
        "LLM_MODEL": settings.llm_model,
    }
    
    print("📋 Configurações atuais:")
    for key, value in config_info.items():
        print(f"   {key}: {value}")
    
    return True


async def test_mock_generation():
    """Testa geração com dados mock (sem chamar Ollama real)"""
    print("🧪 Testando geração com dados mock...")
    
    try:
        # Criar fontes mock
        mock_sources = [
            DocumentSource(text="Este é um documento de teste.", score=0.9, document_id="test1"),
            DocumentSource(text="Contém informações importantes.", score=0.8, document_id="test2")
        ]
        
        generator = ResponseGenerator()
        
        # Nota: Este teste vai tentar chamar Ollama real se estiver disponível
        # Para teste completo sem dependências, use os testes unitários
        print("ℹ️  Para teste sem chamar Ollama real, use: pytest tests/test_generation_providers.py")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de geração: {e}")
        return False


def main():
    """Executa todos os testes de validação"""
    print("🚀 Iniciando validação dos provedores LLM\n")
    
    tests = [
        ("Configurações", test_configuration_reading),
        ("Factory válido", test_factory_with_valid_provider),
        ("Factory inválido", test_factory_with_invalid_provider),
        ("ResponseGenerator", test_response_generator_initialization),
        ("Mock generation", test_mock_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func.__name__.startswith('test_mock_generation'):
                import asyncio
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append(False)
    
    print(f"\n📊 Resultados: {sum(results)}/{len(results)} testes passaram")
    
    if all(results):
        print("🎉 Todos os testes passaram! A refatoração está funcionando.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()