from typing import Optional


def render_page(rag_client=None, st=None):
    if st is None:
        import streamlit as st  # type: ignore
    if rag_client is None:
        from src.api.client import RAGClient
        rag_client = RAGClient()

    st.title("🧰 Gerenciador do Banco de Dados")

    status = rag_client.get_db_status()
    if not status.get("ok"):
        st.error(f"Erro ao obter status: {status.get('error')}")
        return
    data = status.get("data", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Documentos", data.get("documents", 0))
    c2.metric("Chunks", data.get("chunks", 0))
    idx_ok = "Sim" if data.get("vector_index_exists") else "Não"
    c3.metric("Índice Vetorial", idx_ok)

    st.markdown("---")
    st.subheader("Índice Vetorial")
    if st.button("Recriar índice vetorial"):
        with st.spinner("Recriando índice..."):
            res = rag_client.reindex_db()
        if res.get("ok"):
            st.success("Índice (re)criado com sucesso.")
            st.rerun()  # type: ignore[attr-defined]
        else:
            st.error(f"Falha ao recriar índice: {res.get('error')}")

    st.markdown("---")
    st.subheader("Limpeza (Ambiente de Desenvolvimento)")
    confirm = st.checkbox("Entendo os riscos: removerá todos os chunks e o índice vetorial.")
    if st.button("Limpar base (dev)", disabled=not confirm):
        with st.spinner("Limpando base..."):
            res = rag_client.clear_db(confirm=True)
        if res.get("ok"):
            st.success("Base limpa com sucesso.")
            st.rerun()  # type: ignore[attr-defined]
        else:
            st.error(f"Falha ao limpar base: {res.get('error')}")


if __name__ == "__main__":
    render_page()

