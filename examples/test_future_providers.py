#!/usr/bin/env python3
"""
Script para testar se os provedores futuros (OpenAI, Gemini) funcionarão
quando implementados, validando configurações e conectividade.
"""
import os
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config.settings import settings


def test_openai_configuration():
    """Testa se as configurações OpenAI estão corretas"""
    print("🔍 Testando configuração OpenAI...")
    
    issues = []
    
    # Verificar se a API key está configurada
    if not settings.openai_api_key or settings.openai_api_key.strip() == "":
        issues.append("❌ OPENAI_API_KEY não está configurada")
    else:
        # Verificar formato básico da chave
        api_key = settings.openai_api_key.strip()
        if not api_key.startswith("sk-"):
            issues.append("❌ OPENAI_API_KEY não parece ter formato válido (deve começar com 'sk-')")
        elif len(api_key) < 50:
            issues.append("⚠️  OPENAI_API_KEY parece muito curta")
        else:
            print(f"✅ OPENAI_API_KEY configurada (primeiros chars: {api_key[:10]}...)")
    
    # Verificar dimensões
    if settings.openai_embedding_dimensions <= 0:
        issues.append("❌ OPENAI_EMBEDDING_DIMENSIONS deve ser > 0")
    else:
        print(f"✅ OPENAI_EMBEDDING_DIMENSIONS: {settings.openai_embedding_dimensions}")
    
    return issues


def test_openai_connectivity():
    """Testa conectividade com OpenAI (se a chave estiver configurada)"""
    print("🌐 Testando conectividade OpenAI...")
    
    if not settings.openai_api_key or settings.openai_api_key.strip() == "":
        return ["⚠️  Pulando teste de conectividade - API key não configurada"]
    
    try:
        # Tentar importar e usar o cliente OpenAI
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Fazer uma chamada simples para testar a chave
        try:
            # Lista os modelos disponíveis (operação barata)
            models = client.models.list()
            print(f"✅ Conectividade OpenAI OK - {len(models.data)} modelos disponíveis")
            
            # Verificar se modelos esperados estão disponíveis
            model_names = [model.id for model in models.data]
            
            expected_models = ["gpt-4o", "gpt-4", "text-embedding-3-small", "text-embedding-ada-002"]
            available_expected = [model for model in expected_models if model in model_names]
            
            print(f"✅ Modelos esperados disponíveis: {available_expected}")
            
            return []
            
        except openai.AuthenticationError:
            return ["❌ Chave de API OpenAI inválida"]
        except openai.RateLimitError:
            return ["⚠️  Rate limit atingido, mas chave parece válida"]
        except Exception as e:
            return [f"❌ Erro ao conectar com OpenAI: {str(e)}"]
            
    except ImportError:
        return ["⚠️  Biblioteca 'openai' não instalada - instale com: pip install openai"]


def test_gemini_configuration():
    """Testa se as configurações Gemini estão corretas"""
    print("🔍 Testando configuração Google Gemini...")
    
    issues = []
    
    # Verificar se a API key está configurada
    if not settings.google_api_key or settings.google_api_key.strip() == "":
        issues.append("❌ GOOGLE_API_KEY não está configurada")
    else:
        api_key = settings.google_api_key.strip()
        if len(api_key) < 30:
            issues.append("⚠️  GOOGLE_API_KEY parece muito curta")
        else:
            print(f"✅ GOOGLE_API_KEY configurada (primeiros chars: {api_key[:10]}...)")
    
    return issues


def test_gemini_connectivity():
    """Testa conectividade com Google Gemini (se a chave estiver configurada)"""
    print("🌐 Testando conectividade Google Gemini...")
    
    if not settings.google_api_key or settings.google_api_key.strip() == "":
        return ["⚠️  Pulando teste de conectividade - API key não configurada"]
    
    try:
        # Tentar importar e usar o cliente Google Generative AI
        import google.generativeai as genai
        
        genai.configure(api_key=settings.google_api_key)
        
        try:
            # Listar modelos disponíveis
            models = list(genai.list_models())
            print(f"✅ Conectividade Gemini OK - {len(models)} modelos disponíveis")
            
            # Verificar se modelo esperado está disponível
            model_names = [model.name for model in models]
            expected_models = ["models/gemini-pro", "models/gemini-pro-vision"]
            available_expected = [model for model in expected_models if model in model_names]
            
            print(f"✅ Modelos esperados disponíveis: {available_expected}")
            
            return []
            
        except Exception as e:
            return [f"❌ Erro ao conectar com Gemini: {str(e)}"]
            
    except ImportError:
        return ["⚠️  Biblioteca 'google-generativeai' não instalada - instale com: pip install google-generativeai"]


def test_provider_switching():
    """Testa se a mudança de providers funciona corretamente"""
    print("🔄 Testando mudança de providers...")
    
    from src.generation.generator import create_llm_provider
    
    # Salvar configuração original
    original_llm = settings.llm_provider
    original_embedding = settings.embedding_provider
    
    results = []
    
    try:
        # Testar cada configuração
        test_configs = [
            ("ollama", "ollama", "Local completo"),
            ("openai", "ollama", "OpenAI LLM + Ollama Embeddings"),
            ("openai", "openai", "OpenAI completo"),
            ("gemini", "ollama", "Gemini LLM + Ollama Embeddings"),
        ]
        
        for llm_prov, emb_prov, desc in test_configs:
            try:
                settings.llm_provider = llm_prov
                settings.embedding_provider = emb_prov
                
                if llm_prov in ["openai", "gemini"]:
                    # Estes vão falhar com NotImplementedError, o que é esperado
                    try:
                        create_llm_provider()
                        results.append(f"❌ {desc}: Deveria falhar (não implementado)")
                    except NotImplementedError:
                        results.append(f"✅ {desc}: Falhou corretamente (não implementado)")
                    except Exception as e:
                        results.append(f"⚠️  {desc}: Erro inesperado: {e}")
                else:
                    # Ollama deveria funcionar
                    provider = create_llm_provider()
                    results.append(f"✅ {desc}: Funcionou ({type(provider).__name__})")
                    
            except Exception as e:
                results.append(f"❌ {desc}: Erro: {e}")
    
    finally:
        # Restaurar configuração original
        settings.llm_provider = original_llm
        settings.embedding_provider = original_embedding
    
    return results


def main():
    """Executa todos os testes de validação de providers futuros"""
    print("🚀 Testando Readiness para Providers Futuros\n")
    
    all_issues = []
    
    # Testar OpenAI
    print("=" * 50)
    print("🤖 OPENAI")
    print("=" * 50)
    
    openai_config_issues = test_openai_configuration()
    openai_connectivity_issues = test_openai_connectivity()
    
    all_issues.extend(openai_config_issues)
    all_issues.extend(openai_connectivity_issues)
    
    # Testar Gemini
    print("\n" + "=" * 50)
    print("🧠 GOOGLE GEMINI")
    print("=" * 50)
    
    gemini_config_issues = test_gemini_configuration()
    gemini_connectivity_issues = test_gemini_connectivity()
    
    all_issues.extend(gemini_config_issues)
    all_issues.extend(gemini_connectivity_issues)
    
    # Testar mudança de providers
    print("\n" + "=" * 50)
    print("🔄 MUDANÇA DE PROVIDERS")
    print("=" * 50)
    
    switch_results = test_provider_switching()
    for result in switch_results:
        print(result)
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO")
    print("=" * 50)
    
    if all_issues:
        print("⚠️  Issues encontradas:")
        for issue in all_issues:
            print(f"   {issue}")
    else:
        print("✅ Todas as configurações estão prontas!")
    
    print(f"\n🎯 Status da implementação:")
    print(f"   ✅ Ollama: Implementado e funcionando")
    print(f"   🚧 OpenAI: Estrutura pronta, aguardando implementação")
    print(f"   🚧 Gemini: Estrutura pronta, aguardando implementação")


if __name__ == "__main__":
    main()