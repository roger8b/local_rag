from typing import Optional, List, Dict


def render_page(rag_client=None, st=None):
    """Render the Document Manager page."""
    if st is None:
        import streamlit as st  # type: ignore
    if rag_client is None:
        from src.api.client import RAGClient
        rag_client = RAGClient()

    st.title("🗂️ Gerenciador de Documentos")

    # Fetch documents
    res = rag_client.list_documents()
    if not res.get("ok"):
        st.error(f"Erro ao listar documentos: {res.get('error')}")
        return
    docs: List[Dict] = res.get("data", [])

    if not docs:
        st.info("Nenhum documento ingerido ainda.")
        return

    # Header
    cols = st.columns([4, 2, 3, 2, 2])
    cols[0].markdown("**Arquivo**")
    cols[1].markdown("**Tipo**")
    cols[2].markdown("**Ingestão**")
    cols[3].markdown("**Doc ID**")
    cols[4].markdown("**Ações**")

    for doc in docs:
        c = st.columns([4, 2, 3, 2, 2])
        c[0].markdown(doc.get("filename", "-"))
        c[1].markdown(doc.get("filetype", "-"))
        c[2].markdown(str(doc.get("ingested_at", "-")))
        c[3].code(doc.get("doc_id", "-"))

        if c[4].button("Remover", key=f"del-{doc.get('doc_id')}"):
            with st.spinner("Removendo documento..."):
                del_res = rag_client.delete_document(doc.get("doc_id"))
            if del_res.get("ok"):
                st.success("Documento removido com sucesso.")
                try:
                    st.experimental_rerun()  # type: ignore[attr-defined]
                except Exception:
                    st.rerun()  # type: ignore[attr-defined]
            else:
                st.error(f"Erro ao remover documento: {del_res.get('error')}")


if __name__ == "__main__":
    render_page()

