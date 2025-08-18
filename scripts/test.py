import ollama
import numpy as np

# Nome do modelo exatamente como está no Ollama
MODEL_NAME = 'nomic-embed-text'
TEXT_TO_EMBED = "Verificando a dimensão do modelo Nomic Embed via Ollama"

try:
    # Chama a função de embeddings do cliente Ollama
    response = ollama.embeddings(
        model=MODEL_NAME,
        prompt=TEXT_TO_EMBED
    )

    # O vetor de embedding está na chave 'embedding' da resposta
    vector = response['embedding']

    # Usa a função len() para obter o número de dimensões do vetor
    dimension = len(vector)
    
    # Você também pode usar numpy para verificar o formato, se preferir
    # vector_np = np.array(vector)
    # print(f"O formato do array numpy é: {vector_np.shape}")

    print(f"✅ Conexão com Ollama bem-sucedida!")
    print(f"✅ A dimensão do modelo '{MODEL_NAME}' é: {dimension}")

except Exception as e:
    print(f"❌ Ocorreu um erro ao tentar se comunicar com o Ollama.")
    print(f"Erro: {e}")
    print("\nPor favor, verifique se:")
    print("1. O serviço do Ollama está rodando na sua máquina.")
    print(f"2. O modelo '{MODEL_NAME}' foi baixado com o comando 'ollama pull {MODEL_NAME}'.")