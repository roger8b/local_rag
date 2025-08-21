import os
import requests
from typing import Optional, Dict, Any
from src.config.settings import settings


def _get_provider_status(provider: str) -> tuple[str, str]:
    """Get status emoji and description for a provider"""
    if provider == "ollama":
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                return "🟢", "Online e disponível"
            else:
                return "🔴", "Offline"
        except:
            return "🔴", "Offline"
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.startswith("sk-") and len(api_key) > 20:
            return "🟢", "Configurado"
        else:
            return "🔴", "API key não configurada"
    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and len(api_key) > 20:
            return "🟢", "Configurado"
        else:
            return "🔴", "API key não configurada"
    else:
        return "❓", "Desconhecido"


def _fetch_embedding_models_for_provider(provider: str) -> Dict[str, Any]:
    """Fetch available embedding models for a provider"""
    # For embedding models, we use hardcoded lists to ensure only embedding models are shown
    if provider == "ollama":
        return {
            "models": ["nomic-embed-text", "all-minilm", "mxbai-embed-large"], 
            "default": "nomic-embed-text"
        }
    elif provider == "openai":
        return {
            "models": [
                "text-embedding-3-small", 
                "text-embedding-3-large", 
                "text-embedding-ada-002"
            ], 
            "default": "text-embedding-3-small"
        }
    elif provider == "gemini":
        return {
            "models": ["embedding-001", "text-embedding-004"], 
            "default": "embedding-001"
        }
    
    return {"models": [], "default": None}


def _fetch_llm_models_for_provider(provider: str) -> Dict[str, Any]:
    """Fetch available LLM models for a provider"""
    try:
        response = requests.get(f"http://localhost:8000/api/v1/models/{provider}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback to static lists with proper LLM models
    if provider == "ollama":
        return {
            "models": ["qwen3:8b", "llama3.2:3b", "llama2:13b"], 
            "default": "qwen3:8b"
        }
    elif provider == "openai":
        return {
            "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], 
            "default": "gpt-4o-mini"
        }
    elif provider == "gemini":
        return {
            "models": ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"], 
            "default": "gemini-2.0-flash-exp"
        }
    
    return {"models": [], "default": None}


def render_page(rag_client=None, st=None):
    """Render the document upload page with advanced model selection.

    Parameters:
        rag_client: an object with a .upload_file(file_content, filename, embedding_provider, model_name) -> {ok, data|error}
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
    st.subheader("⚙️ Configuração de Modelos")
    
    # Create two columns for embedding and LLM configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 **Embedding**")
        
        # Embedding provider selection
        embedding_providers = {
            "ollama": "🏠 Local (Ollama)",
            "openai": "☁️ OpenAI Embeddings"
        }
        
        selected_embedding_provider = st.selectbox(
            "Provider:",
            list(embedding_providers.keys()),
            format_func=lambda x: embedding_providers[x],
            key="embedding_provider_selector"
        )
        
        # Show embedding provider status
        emb_status, emb_desc = _get_provider_status(selected_embedding_provider)
        st.caption(f"{emb_status} {emb_desc}")
        
        # Fetch and display embedding models
        embedding_models_data = _fetch_embedding_models_for_provider(selected_embedding_provider)
        embedding_models = embedding_models_data.get("models", [])
        default_embedding_model = embedding_models_data.get("default")
        
        if embedding_models:
            selected_embedding_model = st.selectbox(
                "Model:",
                embedding_models,
                index=embedding_models.index(default_embedding_model) if default_embedding_model in embedding_models else 0,
                key="embedding_model_selector"
            )
        else:
            selected_embedding_model = None
            st.error("⚠️ Modelos indisponíveis")
    
    with col2:
        st.markdown("#### 🤖 **LLM**")
        
        # LLM provider selection
        llm_providers = {
            "ollama": "🏠 Local (Ollama)", 
            "openai": "☁️ OpenAI GPT",
            "gemini": "✨ Google Gemini"
        }
        
        selected_llm_provider = st.selectbox(
            "Provider:",
            list(llm_providers.keys()),
            format_func=lambda x: llm_providers[x],
            key="llm_provider_selector"
        )
        
        # Show LLM provider status
        llm_status, llm_desc = _get_provider_status(selected_llm_provider)
        st.caption(f"{llm_status} {llm_desc}")
        
        # Fetch and display LLM models
        llm_models_data = _fetch_llm_models_for_provider(selected_llm_provider)
        llm_models = llm_models_data.get("models", [])
        default_llm_model = llm_models_data.get("default")
        
        if llm_models:
            selected_llm_model = st.selectbox(
                "Model:",
                llm_models,
                index=llm_models.index(default_llm_model) if default_llm_model in llm_models else 0,
                key="llm_model_selector"
            )
        else:
            selected_llm_model = None
            st.error("⚠️ Modelos indisponíveis")

    st.markdown("---")

    # File upload section

    # File uploader widget
    uploaded_file = st.file_uploader(
        "📄 Arquivo (.txt, .pdf)",
        type=['txt', 'pdf']
    )

    # Show file information if file is selected
    if uploaded_file is not None:
        file_size = len(uploaded_file.read())
        uploaded_file.seek(0)
        file_size_mb = file_size / (1024 * 1024)
        
        # File info  
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"📁 **{uploaded_file.name}** • {file_size_mb:.2f} MB")
        with col2:
            status = "✅ Ready" if file_size_mb <= 10.0 else "❌ Too large"
            st.caption(f"{status}")

        # Validation and send button
        emb_status_ok = emb_status == "🟢"
        llm_status_ok = llm_status == "🟢" 
        is_file_too_large = file_size_mb > 10.0
        models_available = selected_embedding_model is not None and selected_llm_model is not None
        
        send_button_disabled = is_file_too_large or not emb_status_ok or not llm_status_ok or not models_available
        
        # Show only critical errors
        if is_file_too_large:
            st.error(f"File too large: {file_size_mb:.2f} MB (max 10 MB)")
        elif not emb_status_ok or not llm_status_ok or not models_available:
            st.error("Configuration incomplete")

        send_button = st.button("📤 Upload", disabled=send_button_disabled)
        
        if send_button:
            file_content = uploaded_file.read()
            filename = uploaded_file.name

            # Simple spinner for processing
            with st.spinner(f"Processando {filename} com {embedding_providers[selected_embedding_provider]}..."):
                try:
                    result = rag_client.upload_file(
                        file_content, 
                        filename, 
                        embedding_provider=selected_embedding_provider,
                        model_name=selected_embedding_model
                    )
                except Exception as e:
                    result = {"ok": False, "error": str(e)}

            # Show result
            if result.get("ok"):
                st.success("✅ **Documento processado com sucesso**")
                
                # Compact summary
                result_data = result.get("data", {})
                chunks_created = result_data.get("chunks_created", "N/A")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"📄 **{filename}** • {chunks_created} chunks")
                with col2:
                    st.caption(f"🔍 **{selected_embedding_provider}** • {selected_embedding_model}")
                
            else:
                error_msg = result.get("error", "Erro desconhecido")
                st.error(f"❌ **Erro**: {error_msg}")
                
                # Minimal debug info
                with st.expander("🔧 Debug"):
                    st.code(f"""
Provider: {selected_embedding_provider}
Model: {selected_embedding_model}
File: {filename} ({file_size_mb:.2f} MB)
Error: {error_msg}
                    """)
    else:
        # Disabled button when no file is selected
        st.button("📤 Upload", disabled=True)

    # Minimal info for advanced users
    with st.expander("ℹ️ Info"):
        st.markdown("""
        **Embedding**: Converts text to vectors for search  
        **LLM**: Processes content during ingestion  
        **Limits**: 10 MB max, .txt/.pdf only
        
        **API Keys**: Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` env vars
        """)


if __name__ == "__main__":
    # Allow running as a script for local debug
    render_page()
