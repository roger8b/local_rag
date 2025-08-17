from typing import Optional


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
    st.title("Upload de Documentos")

    # Page description
    st.markdown("""
    ### Faça o upload de seus documentos de texto
    
    Use esta página para adicionar novos documentos à base de conhecimento do sistema.
    Apenas arquivos de texto (`.txt`) são suportados.
    """)

    # File uploader widget - restricted to .txt files
    uploaded_file = st.file_uploader(
        "Selecione um arquivo de texto (.txt)",
        type=['txt'],
        help="Apenas arquivos de texto (.txt) são permitidos"
    )

    # Send button - only enabled when file is selected
    if uploaded_file is not None:
        send_button = st.button("Enviar Documento")
        
        if send_button:
            # Read file content
            file_content = uploaded_file.read()
            filename = uploaded_file.name
            
            # Show spinner while processing
            with st.spinner("Processando documento..."):
                result = rag_client.upload_file(file_content, filename)
            
            # Handle response
            if result.get("ok"):
                st.success("Documento enviado com sucesso! O documento foi processado e está pronto para consulta.")
            else:
                error_msg = result.get("error", "Erro desconhecido")
                st.error(f"Erro ao enviar documento: {error_msg}")
    else:
        # Disabled button when no file is selected
        st.button("Enviar Documento", disabled=True)

    # Additional information
    st.markdown("""
    ---
    **Instruções:**
    - Selecione um arquivo `.txt` do seu computador
    - Clique em "Enviar Documento" para processar o arquivo
    - Após o envio bem-sucedido, você poderá fazer perguntas sobre o conteúdo na página de consulta
    """)


if __name__ == "__main__":
    # Allow running as a script for local debug
    render_page()