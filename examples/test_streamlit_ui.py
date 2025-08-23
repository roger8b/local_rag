#!/usr/bin/env python3
"""
Teste manual da interface Streamlit atualizada
"""
import sys
sys.path.append('src')

from src.ui.components.provider_selector import get_provider_status, get_embedding_provider_config

def test_provider_validation():
    """Teste da validação de providers"""
    print("🧪 Testando Validação de Providers")
    print("=" * 40)
    
    providers = ["ollama", "openai", "gemini"]
    
    for provider in providers:
        llm_status, llm_desc = get_provider_status(provider, "llm")
        emb_status, emb_desc = get_provider_status(provider, "embedding") 
        
        print(f"\n🤖 {provider.upper()}:")
        print(f"  LLM: {llm_status} {llm_desc}")
        print(f"  Embedding: {emb_status} {emb_desc}")
        
        # Test embedding config
        config = get_embedding_provider_config(provider)
        print(f"  Config: {config}")

def test_embedding_configs():
    """Teste das configurações de embedding"""
    print("\n🔧 Testando Configurações de Embedding")
    print("=" * 40)
    
    providers = ["ollama", "openai", "gemini"]
    
    for provider in providers:
        config = get_embedding_provider_config(provider)
        status = "✅" if config["is_configured"] else "❌"
        print(f"{status} {provider.upper()}: {config['label']} (multiplicador: {config['time_multiplier']}x)")

if __name__ == "__main__":
    test_provider_validation()
    test_embedding_configs()
    
    print("\n🎯 Teste concluído!")
    print("💡 Para testar a interface completa, execute: streamlit run streamlit_app.py")