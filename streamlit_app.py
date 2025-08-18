#!/usr/bin/env python3
"""
Aplicação principal do Local RAG System com interface Streamlit.

Este arquivo unifica todas as funcionalidades do sistema:
- Interface de chat para consultas RAG (Fase 3)
- Interface de upload de documentos (Fase 4)

Uso:
    streamlit run streamlit_app.py
    
Configuração:
    API_BASE_URL: URL da API (default: http://localhost:8000)
"""

import streamlit as st
from src.ui.pages.document_upload import render_page as upload_page
from src.ui.pages.query_interface import render_page as query_page
from src.ui.components.provider_selector import render_llm_provider_selector

# Configuração da página
st.set_page_config(
    page_title="Local RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🔍 Local RAG System")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Escolha uma funcionalidade:",
    ["💬 Consulta", "📤 Upload de Documentos"],
    index=0
)

st.sidebar.markdown("---")

# Global LLM Provider Selector (only for query page)
selected_llm_provider = None
if page == "💬 Consulta":
    selected_llm_provider = render_llm_provider_selector(st, "global")
    st.sidebar.markdown("---")

st.sidebar.markdown("""
### ℹ️ Sobre o Sistema
- **Consulta**: Faça perguntas sobre os documentos indexados
- **Upload**: Adicione novos documentos (.txt) à base de conhecimento

### 🔧 Status da API
""")

# Simple API health check
try:
    import requests
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        st.sidebar.success("🟢 API Online")
    else:
        st.sidebar.error("🔴 API com problemas")
except:
    st.sidebar.error("🔴 API Offline")

# Render selected page
if page == "📤 Upload de Documentos":
    upload_page()
elif page == "💬 Consulta":
    query_page(selected_provider=selected_llm_provider)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("*Local RAG System v1.0*")