#!/usr/bin/env python3
"""
Teste da funcionalidade de seleção dinâmica de provider
"""
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000/api/v1/query"
QUESTION = "Qual é o objetivo de Ash Ketchum?"

def test_dynamic_provider_selection():
    """Testa seleção dinâmica de provider via API"""
    
    print("🧪 Testando Seleção Dinâmica de Provider LLM")
    print("=" * 50)
    
    # Teste 1: Provider padrão (sem especificar)
    print("\n1️⃣ Teste com provider padrão")
    try:
        response = requests.post(API_URL, json={"question": QUESTION}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            provider = data.get("provider_used", "não especificado")
            print(f"✅ Provider usado: {provider}")
            print(f"📝 Resposta: {data['answer'][:100]}...")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 2: Provider específico - OpenAI
    print("\n2️⃣ Teste com provider OpenAI")
    try:
        response = requests.post(API_URL, json={"question": QUESTION, "provider": "openai"}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            provider = data.get("provider_used", "não especificado")
            print(f"✅ Provider usado: {provider}")
            print(f"📝 Resposta: {data['answer'][:100]}...")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 3: Provider específico - Gemini
    print("\n3️⃣ Teste com provider Gemini")
    try:
        response = requests.post(API_URL, json={"question": QUESTION, "provider": "gemini"}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            provider = data.get("provider_used", "não especificado")
            print(f"✅ Provider usado: {provider}")
            print(f"📝 Resposta: {data['answer'][:100]}...")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 4: Provider inválido
    print("\n4️⃣ Teste com provider inválido")
    try:
        response = requests.post(API_URL, json={"question": QUESTION, "provider": "anthropic"}, timeout=30)
        if response.status_code == 500:
            data = response.json()
            print(f"✅ Erro esperado capturado: {data.get('detail', 'erro sem detalhes')}")
        else:
            print(f"⚠️ Resposta inesperada {response.status_code}: {response.text}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 5: Validação do schema da resposta
    print("\n5️⃣ Teste de validação do schema")
    try:
        response = requests.post(API_URL, json={"question": QUESTION, "provider": "ollama"}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["answer", "sources", "question", "provider_used"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Campos obrigatórios ausentes: {missing_fields}")
            else:
                print("✅ Schema da resposta válido")
                print(f"📊 Campos: {list(data.keys())}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Teste de seleção dinâmica concluído!")

if __name__ == "__main__":
    test_dynamic_provider_selection()