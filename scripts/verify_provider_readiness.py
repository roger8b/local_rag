#!/usr/bin/env python3
"""
Script para verificar se OpenAI e Gemini funcionarão quando implementados
"""
import asyncio


async def test_openai_readiness():
    """Testa se OpenAI funcionará quando implementado"""
    print("🔍 Testando se OpenAI funcionará quando implementado...")
    
    try:
        # Testar biblioteca
        import openai
        from src.config.settings import settings
        
        if not settings.openai_api_key:
            print("❌ OPENAI_API_KEY não configurada")
            return False
            
        # Testar conectividade
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Teste 1: Listar modelos
        models = client.models.list()
        print(f"✅ OpenAI conectividade OK - {len(models.data)} modelos")
        
        # Teste 2: Testar chat completion (similar ao que seria implementado)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo recomendado para o projeto
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": "Diga apenas 'teste' como resposta."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ Chat Completion funcionando: '{result}'")
        
        # Teste 3: Testar embeddings
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input="texto de teste"
        )
        
        embedding = embedding_response.data[0].embedding
        print(f"✅ Embeddings funcionando: {len(embedding)} dimensões")
        
        return True
        
    except ImportError:
        print("❌ Biblioteca openai não instalada")
        print("   Instale com: pip install openai")
        return False
    except Exception as e:
        print(f"❌ Erro OpenAI: {e}")
        return False


async def test_gemini_readiness():
    """Testa se Gemini funcionará quando implementado"""
    print("🔍 Testando se Gemini funcionará quando implementado...")
    
    try:
        # Testar biblioteca
        import google.generativeai as genai
        from src.config.settings import settings
        
        if not settings.google_api_key:
            print("❌ GOOGLE_API_KEY não configurada")
            return False
            
        # Configurar API
        genai.configure(api_key=settings.google_api_key)
        
        # Teste 1: Listar modelos
        models = list(genai.list_models())
        print(f"✅ Gemini conectividade OK - {len(models)} modelos")
        
        # Teste 2: Testar geração (similar ao que seria implementado)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Diga apenas 'teste' como resposta.")
        
        result = response.text
        print(f"✅ Geração funcionando: '{result.strip()}'")
        
        return True
        
    except ImportError:
        print("❌ Biblioteca google-generativeai não instalada")
        print("   Instale com: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Erro Gemini: {e}")
        return False


def show_implementation_plan():
    """Mostra o que precisa ser implementado"""
    print("\n📋 PLANO DE IMPLEMENTAÇÃO")
    print("=" * 50)
    
    print("\n🔧 Para OpenAI Provider:")
    print("1. Instalar biblioteca: pip install openai")
    print("2. Criar src/generation/providers/openai.py")
    print("3. Implementar classe OpenAIProvider(LLMProvider)")
    print("4. Atualizar factory em generator.py")
    print("5. Adicionar testes")
    
    print("\n🔧 Para Gemini Provider:")
    print("1. Instalar biblioteca: pip install google-generativeai")
    print("2. Criar src/generation/providers/gemini.py")
    print("3. Implementar classe GeminiProvider(LLMProvider)")
    print("4. Atualizar factory em generator.py")
    print("5. Adicionar testes")
    
    print("\n📝 Template de implementação:")
    print("""
class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"
    
    async def generate_response(self, question: str, sources: List[DocumentSource]) -> str:
        prompt = self._build_prompt(question, sources)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
""")


async def main():
    """Executa todos os testes de readiness"""
    print("🚀 VERIFICAÇÃO DE READINESS PARA PROVIDERS FUTUROS")
    print("=" * 60)
    
    # Testar OpenAI
    print("\n🤖 OPENAI")
    print("-" * 30)
    openai_ready = await test_openai_readiness()
    
    # Testar Gemini
    print("\n🧠 GEMINI")
    print("-" * 30)
    gemini_ready = await test_gemini_readiness()
    
    # Mostrar resumo
    print("\n📊 RESUMO FINAL")
    print("=" * 30)
    print(f"OpenAI pronto: {'✅ SIM' if openai_ready else '❌ NÃO'}")
    print(f"Gemini pronto: {'✅ SIM' if gemini_ready else '❌ NÃO'}")
    
    if openai_ready and gemini_ready:
        print("\n🎉 AMBOS PROVIDERS ESTÃO PRONTOS!")
        print("   A implementação funcionará quando o código for criado.")
    elif openai_ready or gemini_ready:
        print(f"\n⚠️  {'OpenAI' if openai_ready else 'Gemini'} está pronto")
        print("   O outro provider precisa de configuração.")
    else:
        print("\n❌ NENHUM PROVIDER EXTERNO ESTÁ PRONTO")
        print("   Mas Ollama está funcionando!")
    
    # Mostrar plano de implementação
    show_implementation_plan()


if __name__ == "__main__":
    asyncio.run(main())