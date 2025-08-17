import os
from typing import Optional
from src.config.settings import settings


def render_page(rag_client=None, st=None):
    """Render the document upload page.

    Parameters:
        rag_client: an object with a .upload_file(file_content, filename) -> {ok, data|error}
        st: streamlit module (or compatible), defaults to imported streamlit
    """
    if st is None:
        import streamlit as st  # type: ignore
    if rag_client is None:
        from src.api.client import RAGClient
        rag_client = RAGClient()

    # Page title
    st.title("📤 Upload de Documentos")
    
    # Configuration section
    st.subheader("⚙️ Configurações")
    
    # --- Configuração do Provedor de Embedding ---
    
    # Dicionário de provedores para escalabilidade
    EMBEDDING_PROVIDERS = {
        "ollama": {
            "label": "🏠 Local (Ollama)",
            "description": "Processamento local usando Ollama. Mais lento, mas totalmente privado.",
            "check": lambda: True, # Sempre disponível
            "time_multiplier": 2.0
        },
        "openai": {
            "label": "☁️ OpenAI",
            "description": "Processamento remoto via OpenAI. Mais rápido, requer chave de API.",
            "check": lambda: settings.openai_api_key,
            "time_multiplier": 1.0
        },
        # Adicione novos provedores aqui no futuro
        # "gemini": {
        #     "label": "✨ Google Gemini",
        #     "description": "Processamento remoto via Google Gemini.",
        #     "check": lambda: settings.gemini_api_key,
        #     "time_multiplier": 1.0
        # }
    }

    # --- Layout da UI ---
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Seleção do provedor de forma dinâmica
        provider_key = st.radio(
            "Provedor de Embeddings:",
            options=list(EMBEDDING_PROVIDERS.keys()),
            index=0,
            help="Modelo usado para processar documentos. Consultas sempre usam modelo local."
        )

    with col2:
        selected_provider = EMBEDDING_PROVIDERS[provider_key]
        
        # Verifica a configuração do provedor selecionado
        if selected_provider["check"]():
            st.info(f"✅ **{selected_provider['label']}** selecionado.")
            st.info(selected_provider['description'])
        else:
            st.error(f"❌ **{selected_provider['label']}** requer configuração.")
            if provider_key == "openai":
                st.markdown("""
                **Como configurar:**
                ```bash
                export OPENAI_API_KEY="sk-your-key-here"
                # Ou adicione em .env
                ```
                """)
        
        st.caption("💡 Consultas sempre usam modelo local independente desta configuração.")

    st.markdown("---")

    # Page description
    st.markdown("""
    ### 📄 Faça o upload de seus documentos de texto
    
    Use esta página para adicionar novos documentos à base de conhecimento do sistema.
    Apenas arquivos de texto (`.txt`) são suportados.
    """)

    # File uploader widget
    uploaded_file = st.file_uploader(
        "Selecione um arquivo de texto (.txt)",
        type=['txt'],
        help="Apenas arquivos de texto (.txt) são permitidos"
    )

    # Show file information if file is selected
    if uploaded_file is not None:
        file_size = len(uploaded_file.read())
        uploaded_file.seek(0)
        file_size_mb = file_size / (1024 * 1024)
        
        # Calcula o tempo estimado de forma dinâmica
        base_time = 60 + (file_size_mb * 30)
        time_multiplier = EMBEDDING_PROVIDERS[provider_key]["time_multiplier"]
        estimated_time = max(60, min(1200, base_time * time_multiplier))
        
        # File info display
        st.markdown("### 📊 Informações do Arquivo")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="📁 Tamanho", value=f"{file_size_mb:.2f} MB")
        with col2:
            st.metric(
                label="⏱️ Tempo Estimado", 
                value=f"~{estimated_time:.0f}s",
                help=f"Estimativa para o provedor {EMBEDDING_PROVIDERS[provider_key]['label']}"
            )
        with col3:
            if file_size_mb <= 10.0:
                st.metric(label="✅ Status", value="Pronto", delta="Válido")
            else:
                st.metric(label="❌ Status", value="Muito grande", delta="Inválido")
        
        st.markdown("")

        # Botão de envio e validações
        is_provider_configured = EMBEDDING_PROVIDERS[provider_key]["check"]()
        is_file_too_large = file_size_mb > 10.0
        
        send_button_disabled = is_file_too_large or not is_provider_configured
        
        if is_file_too_large:
            st.error(f"🚫 **Arquivo muito grande**: {file_size_mb:.2f} MB (limite de 10 MB).")
        elif not is_provider_configured:
            st.error(f"🔧 **Provedor não configurado**: Verifique as configurações para {EMBEDDING_PROVIDERS[provider_key]['label']}.")
        elif file_size_mb > 2.0:
            st.warning(f"⚠️ **Arquivo grande detectado**: O processamento pode levar alguns minutos.")
        else:
            st.success("✅ **Pronto para envio**.")

        send_button = st.button("📤 Enviar Documento", disabled=send_button_disabled)
        
        if send_button:
            file_content = uploaded_file.read()
            filename = uploaded_file.name

            # Execução com spinner para feedback simples (compatível com testes)
            with st.spinner("Enviando documento..."):
                result = rag_client.upload_file(file_content, filename)

            if result.get("ok"):
                st.success("Documento enviado com sucesso!")
            else:
                error_msg = result.get("error", "Erro desconhecido")
                st.error(f"Erro ao enviar documento: {error_msg}")
    else:
        # Disabled button when no file is selected
        st.button("Enviar Documento", disabled=True)

    # Additional information
    st.markdown("""
    ---
    ## 📋 Instruções de Uso
    
    ### 📤 Upload de Documentos
    1. **Configure** o tipo de embedding (Local ou OpenAI)
    2. **Selecione** um arquivo `.txt` do seu computador (máximo 10 MB)
    3. **Clique** em "Enviar Documento" e acompanhe o progresso
    4. **Aguarde** o processamento (tempo varia conforme tamanho e tipo de embedding)
    
    ### ⚙️ Configurações de Embedding
    - **🏠 Local (Ollama)**: Mais lento, mas totalmente privado
    - **☁️ OpenAI**: Mais rápido, requer API key configurada
    
    ### 🔐 Como Configurar OpenAI API Key
    ```bash
    # Método 1: Variável de ambiente (recomendado)
    export OPENAI_API_KEY="sk-your-openai-key-here"
    
    # Método 2: Arquivo .env na raiz do projeto
    echo "OPENAI_API_KEY=sk-your-openai-key-here" > .env
    
    # Método 3: Definir antes de executar
    OPENAI_API_KEY="sk-your-key" streamlit run streamlit_app.py
    ```
    
    📝 **Obter API Key**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
    
    ### 💬 Consultas
    - Independente do tipo de embedding, **consultas sempre usam modelo local**
    - Após upload, vá para a página "Consulta" para fazer perguntas sobre o documento
    
    ### 🔧 Dicas de Performance
    - Arquivos grandes (>2 MB) podem demorar vários minutos
    - Para melhor performance, divida arquivos muito grandes em partes menores
    - Use embeddings OpenAI se precisar de processamento mais rápido
    """)
    
    # Footer with current configuration
    st.markdown("---")
    st.caption(f"🔧 Configuração atual: Embeddings {EMBEDDING_PROVIDERS[provider_key]['label']} | Consultas sempre locais")


if __name__ == "__main__":
    # Allow running as a script for local debug
    render_page()
