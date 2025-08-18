"""
Componente global para seleção de providers LLM e Embedding
"""
import os
from typing import Optional, Tuple
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


def get_provider_status(provider: str, provider_type: str = "llm") -> tuple[str, str]:
    """
    Get status emoji and description for a provider
    
    Args:
        provider: Provider name ("ollama", "openai", "gemini")
        provider_type: Type ("llm" or "embedding")
    """
    if provider == "ollama":
        return "🟢", "Local (sempre disponível)"
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


def render_llm_provider_selector(st, key_suffix: str = "") -> Optional[str]:
    """
    Render LLM provider selector in sidebar
    
    Args:
        st: Streamlit module
        key_suffix: Suffix for unique keys when multiple selectors
        
    Returns:
        Selected provider name or None for auto/default
    """
    with st.sidebar:
        st.markdown("### 🤖 Configuração de LLM")
        
        # Provider options with status
        providers_info = {
            "auto": ("Auto (padrão)", "🔄", "Usa configuração padrão do sistema"),
            "ollama": ("Ollama", *get_provider_status("ollama", "llm")),
            "openai": ("OpenAI", *get_provider_status("openai", "llm")),
            "gemini": ("Google Gemini", *get_provider_status("gemini", "llm"))
        }
        
        provider_options = []
        for key, (name, status, desc) in providers_info.items():
            provider_options.append(f"{status} {name}")
        
        selected_display = st.selectbox(
            "Escolha o Provider LLM:",
            provider_options,
            index=0,
            key=f"llm_provider_selector_{key_suffix}",
            help="Selecione qual modelo usar para gerar as respostas"
        )
        
        # Extract provider key from selection and show info
        selected_provider = None
        for key, (name, status, desc) in providers_info.items():
            if f"{status} {name}" == selected_display:
                if key != "auto":
                    selected_provider = key
                st.info(f"ℹ️ {desc}")
                
                # Show configuration help for unconfigured providers
                if status == "🔴":
                    if key == "openai":
                        st.warning("⚠️ Configure a OPENAI_API_KEY no arquivo .env")
                    elif key == "gemini":
                        st.warning("⚠️ Configure a GOOGLE_API_KEY no arquivo .env")
                break
        
        # Show current default provider from environment
        default_provider = os.getenv("LLM_PROVIDER", "ollama")
        st.caption(f"**Provider padrão do sistema:** {default_provider}")
        
        return selected_provider


def render_embedding_provider_selector(st, key_suffix: str = "") -> str:
    """
    Render embedding provider selector
    
    Args:
        st: Streamlit module  
        key_suffix: Suffix for unique keys when multiple selectors
        
    Returns:
        Selected embedding provider name
    """
    # Embedding providers configuration
    embedding_providers = {
        "ollama": {
            "label": "🏠 Local (Ollama)",
            "description": "Processamento local usando Ollama. Mais lento, mas totalmente privado.",
            "status": get_provider_status("ollama", "embedding"),
            "time_multiplier": 2.0
        },
        "openai": {
            "label": "☁️ OpenAI",
            "description": "Processamento remoto via OpenAI. Mais rápido, requer chave de API.",
            "status": get_provider_status("openai", "embedding"),
            "time_multiplier": 1.0
        },
        "gemini": {
            "label": "✨ Google Gemini",
            "description": "Processamento remoto via Google Gemini. (Futuramente disponível para embeddings)",
            "status": ("🔴", "Não suportado ainda"),
            "time_multiplier": 1.0
        }
    }
    
    st.markdown("### ⚙️ Configuração de Embeddings")
    
    # Create options list
    provider_options = []
    for key, config in embedding_providers.items():
        status_emoji, status_desc = config["status"]
        if key == "gemini":  # Skip Gemini for now as it's not implemented for embeddings
            continue
        provider_options.append(f"{status_emoji} {config['label']}")
    
    selected_display = st.selectbox(
        "Provedor de Embeddings:",
        provider_options,
        index=0,
        key=f"embedding_provider_selector_{key_suffix}",
        help="Modelo usado para processar documentos"
    )
    
    # Extract selected provider
    selected_provider = None
    for key, config in embedding_providers.items():
        status_emoji, status_desc = config["status"]
        if f"{status_emoji} {config['label']}" == selected_display:
            selected_provider = key
            
            # Show provider info
            if status_emoji == "🟢":
                st.success(f"✅ **{config['label']}** configurado.")
            else:
                st.error(f"❌ **{config['label']}** requer configuração.")
                
                if key == "openai":
                    st.code("""
# Configure no arquivo .env:
OPENAI_API_KEY=sk-your-key-here
                    """)
            
            st.info(config['description'])
            break
    
    return selected_provider or "ollama"


def get_embedding_provider_config(provider: str) -> dict:
    """Get configuration for embedding provider"""
    configs = {
        "ollama": {
            "time_multiplier": 2.0,
            "is_configured": True,
            "label": "🏠 Local (Ollama)"
        },
        "openai": {
            "time_multiplier": 1.0,
            "is_configured": bool(os.getenv("OPENAI_API_KEY", "").startswith("sk-")),
            "label": "☁️ OpenAI"
        },
        "gemini": {
            "time_multiplier": 1.0,
            "is_configured": False,  # Not yet supported for embeddings
            "label": "✨ Google Gemini"
        }
    }
    return configs.get(provider, configs["ollama"])