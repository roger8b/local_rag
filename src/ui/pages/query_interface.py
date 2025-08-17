from typing import Optional


def render_page(rag_client=None, st=None):
    """Render the chat interface page.

    Parameters:
        rag_client: an object with a .query(question) -> {ok, data|error}
        st: streamlit module (or compatible), defaults to imported streamlit
    """
    if st is None:
        import streamlit as st  # type: ignore
    if rag_client is None:
        from src.api.client import RAGClient
        rag_client = RAGClient()

    # Title
    st.title("Local RAG - Interface de Consulta")

    # Initialize conversation state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Render existing messages
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):  # type: ignore[attr-defined]
            st.markdown(msg["content"])  # type: ignore[attr-defined]

    # Chat input
    user_input = st.chat_input("Faça sua pergunta")  # type: ignore[attr-defined]
    if user_input:
        # Append user message and re-render
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)  # type: ignore[attr-defined]

        # Call backend with loading indicator
        with st.spinner("Processando..."):
            result = rag_client.query(user_input)

        if result.get("ok"):
            answer = result["data"].get("answer", "")
            st.session_state["messages"].append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)  # type: ignore[attr-defined]
        else:
            friendly = "Desculpe, não consegui processar sua pergunta. Tente novamente."
            st.session_state["messages"].append({"role": "assistant", "content": friendly})
            with st.chat_message("assistant"):
                st.markdown(friendly)  # type: ignore[attr-defined]


if __name__ == "__main__":
    # Allow running as a script for local debug
    render_page()
