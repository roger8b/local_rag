#!/usr/bin/env python3
"""
Teste simples da API query com o provider atual
"""
import requests
import json
from datetime import datetime

# Perguntas sobre Pokemon
questions = [
    "Quais são os Pokémon iniciais de Kanto?",
    "Como Eevee evolui para suas diferentes formas?", 
    "Quem é o líder da Equipe Rocket?",
    "Qual é o principal objetivo de Ash Ketchum?"
]

API_URL = "http://localhost:8000/api/v1/query"

# Criar arquivo de log
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"/tmp/pokemon_test_{timestamp}.log"

print(f"🧪 Testando API Query com contexto Pokemon")
print(f"📁 Log: {log_file}")

with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"=== Teste Pokemon API - {datetime.now().isoformat()} ===\n\n")
    
    for i, question in enumerate(questions, 1):
        print(f"\n📋 Pergunta {i}: {question}")
        f.write(f"PERGUNTA {i}: {question}\n")
        f.write("="*50 + "\n")
        
        try:
            response = requests.post(
                API_URL,
                json={"question": question},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Resposta: {data['answer'][:100]}...")
                
                f.write("STATUS: SUCCESS\n")
                f.write(f"RESPOSTA: {data['answer']}\n")
                f.write(f"FONTES: {len(data['sources'])} documentos\n")
                f.write(f"PERGUNTA ORIGINAL: {data['question']}\n")
                
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                f.write(f"STATUS: ERROR {response.status_code}\n")
                f.write(f"ERRO: {response.text}\n")
                
        except Exception as e:
            print(f"💥 Exceção: {str(e)}")
            f.write(f"STATUS: EXCEPTION\n")
            f.write(f"ERRO: {str(e)}\n")
            
        f.write("\n" + "="*80 + "\n\n")

print(f"\n📁 Log completo salvo em: {log_file}")
print(f"💡 Para ver: cat {log_file}")