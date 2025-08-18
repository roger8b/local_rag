from typing import Optional
import os


def get_provider_status(provider: str) -> tuple[str, str]:
    """Get status emoji and description for a provider"""
    if provider == "ollama":
        # Ollama is always considered available (local)
        return "🟢", "Local (sempre disponível)"
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.startswith("sk-"):
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


def render_page(rag_client=None, st=None, selected_provider=None):
    """Render the chat interface page.

    Parameters:
        rag_client: an object with a .query(question, provider) -> {ok, data|error}
        st: streamlit module (or compatible), defaults to imported streamlit
        selected_provider: LLM provider selected from global selector
    """
    if st is None:
        import streamlit as st  # type: ignore
    if rag_client is None:
        from src.api.client import RAGClient
        rag_client = RAGClient()

    # Title
    st.title("🤖 Local RAG - Interface de Consulta")
    
    # Show current provider info
    if selected_provider:
        provider_status, provider_desc = get_provider_status(selected_provider)
        st.info(f"{provider_status} Usando **{selected_provider.upper()}** - {provider_desc}")
    else:
        default_provider = os.getenv("LLM_PROVIDER", "ollama")
        st.info(f"🔄 Usando provider **padrão** ({default_provider.upper()})")

    # Initialize conversation state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Render existing messages
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):  # type: ignore[attr-defined]
            # Show provider info for assistant messages
            if msg["role"] == "assistant" and "provider_used" in msg:
                st.caption(f"🤖 Gerado por: {msg['provider_used']}")
            st.markdown(msg["content"])  # type: ignore[attr-defined]

    # Chat input
    user_input = st.chat_input("Faça sua pergunta")  # type: ignore[attr-defined]
    if user_input:
        # Append user message and re-render
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)  # type: ignore[attr-defined]

        # Call backend with loading indicator
        provider_display = selected_provider.upper() if selected_provider else "provider padrão"
        with st.spinner(f"Processando com {provider_display}..."):
            result = rag_client.query(user_input, provider=selected_provider)

        if result.get("ok"):
            data = result["data"]
            answer = data.get("answer", "")
            provider_used = data.get("provider_used", "unknown")
            
            # Store message with provider info
            message_content = {"role": "assistant", "content": answer, "provider_used": provider_used}
            st.session_state["messages"].append(message_content)
            
            with st.chat_message("assistant"):
                st.caption(f"🤖 Gerado por: {provider_used}")
                st.markdown(answer)  # type: ignore[attr-defined]
                
                # Show sources if available
                if "sources" in data and data["sources"]:
                    with st.expander(f"📚 Fontes utilizadas ({len(data['sources'])})"):
                        for i, source in enumerate(data["sources"], 1):
                            st.markdown(f"**Fonte {i}** (score: {source['score']:.3f})")
                            st.markdown(f"```\n{source['text'][:200]}...\n```")
        else:
            friendly = "Desculpe, não consegui processar sua pergunta. Tente novamente."
            error_detail = result.get("error", "")
            if "configuração" in error_detail.lower() or "api" in error_detail.lower():
                friendly += f"\n\n⚠️ Erro: {error_detail}"
                
            st.session_state["messages"].append({"role": "assistant", "content": friendly})
            with st.chat_message("assistant"):
                st.markdown(friendly)  # type: ignore[attr-defined]


if __name__ == "__main__":
    # Allow running as a script for local debug
    render_page()
