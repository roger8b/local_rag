#!/usr/bin/env python3
"""
Aplicação principal do Local RAG System com interface Streamlit (Fase 5.1).

Funcionalidades principais:
- Seleção dinâmica de modo de operação (Consulta/Ingestão)
- Seleção dinâmica de provedor LLM (Ollama/OpenAI/Gemini)
- Seleção dinâmica de modelo específico para cada provedor
- Interface de chat para consultas RAG
- Interface de upload de documentos

Uso:
    streamlit run streamlit_app.py
    
Configuração:
    API_BASE_URL: URL da API (default: http://localhost:8000)
"""

import streamlit as st
import requests
from src.ui.pages.document_upload import render_page as upload_page
from src.ui.pages.query_interface import render_page as query_page

# Configuração da página
st.set_page_config(
    page_title="Local RAG System - Fase 5.1",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "Consulta"
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = "ollama"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "default_model" not in st.session_state:
    st.session_state.default_model = None

# ============================================================================
# SIDEBAR - Centro de Controle Principal
# ============================================================================

st.sidebar.title("🔍 Local RAG System")
st.sidebar.markdown("### 🎛️ Centro de Controle")

# 1. Seleção de Modo de Operação
st.sidebar.markdown("#### 📋 Modo de Operação")
selected_mode = st.sidebar.radio(
    "Escolha o modo:",
    ["Consulta", "Ingestão"],
    index=0 if st.session_state.selected_mode == "Consulta" else 1,
    help="Consulta: Fazer perguntas sobre documentos. Ingestão: Adicionar novos documentos."
)

# Update session state if changed
if selected_mode != st.session_state.selected_mode:
    st.session_state.selected_mode = selected_mode
    st.rerun()

st.sidebar.markdown("---")

# 2. Seleção de Provedor LLM
st.sidebar.markdown("#### 🤖 Provedor de LLM")
provider_options = {
    "ollama": "🏠 Local (Ollama)",
    "openai": "☁️ OpenAI",
    "gemini": "✨ Google Gemini"
}

selected_provider = st.sidebar.selectbox(
    "Provedor:",
    list(provider_options.keys()),
    index=list(provider_options.keys()).index(st.session_state.selected_provider),
    format_func=lambda x: provider_options[x],
    help="Selecione qual provedor usar para gerar respostas"
)

# Update session state and fetch models if provider changed
if selected_provider != st.session_state.selected_provider:
    st.session_state.selected_provider = selected_provider
    st.session_state.selected_model = None  # Reset model selection
    st.session_state.available_models = []
    st.session_state.default_model = None
    
    # Fetch models for new provider
    try:
        response = requests.get(f"http://localhost:8000/api/v1/models/{selected_provider}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.available_models = data.get("models", [])
            st.session_state.default_model = data.get("default", None)
            st.session_state.selected_model = st.session_state.default_model
        else:
            st.sidebar.error(f"❌ Erro ao buscar modelos: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Erro de conexão: {str(e)}")

# 3. Seleção de Modelo
if st.session_state.available_models:
    st.sidebar.markdown("#### 🎯 Modelo Específico")
    
    # Show current default
    if st.session_state.default_model:
        st.sidebar.caption(f"**Padrão:** {st.session_state.default_model}")
    
    selected_model = st.sidebar.selectbox(
        "Modelo:",
        st.session_state.available_models,
        index=st.session_state.available_models.index(st.session_state.selected_model) if st.session_state.selected_model in st.session_state.available_models else 0,
        help="Modelo específico a ser usado"
    )
    
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model

elif st.session_state.selected_provider:
    st.sidebar.markdown("#### 🎯 Modelo Específico")
    st.sidebar.info("⏳ Carregando modelos disponíveis...")

# Show provider status
st.sidebar.markdown("---")
st.sidebar.markdown("#### 📊 Status dos Provedores")

# Provider status check
provider_status = {}
try:
    # Check Ollama
    ollama_resp = requests.get("http://localhost:11434/api/tags", timeout=2)
    provider_status["ollama"] = "🟢 Online" if ollama_resp.status_code == 200 else "🔴 Offline"
except:
    provider_status["ollama"] = "🔴 Offline"

# Check OpenAI (just configuration)
import os
if os.getenv("OPENAI_API_KEY", "").startswith("sk-"):
    provider_status["openai"] = "🟢 Configurado"
else:
    provider_status["openai"] = "⚠️ API Key não configurada"

# Check Gemini (just configuration)  
if os.getenv("GOOGLE_API_KEY", "") and len(os.getenv("GOOGLE_API_KEY", "")) > 20:
    provider_status["gemini"] = "🟢 Configurado"
else:
    provider_status["gemini"] = "⚠️ API Key não configurada"

for provider, status in provider_status.items():
    st.sidebar.write(f"• {provider_options[provider]}: {status}")

# API Health Check
st.sidebar.markdown("---")
st.sidebar.markdown("#### 🔧 Status da API")
try:
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        st.sidebar.success("🟢 API Online")
    else:
        st.sidebar.error("🔴 API com problemas")
except:
    st.sidebar.error("🔴 API Offline")

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

# Render the appropriate page based on selected mode
if st.session_state.selected_mode == "Ingestão":
    # Upload page with embedding provider selection
    upload_page()
elif st.session_state.selected_mode == "Consulta":
    # Query page with selected provider and model
    query_page(
        selected_provider=st.session_state.selected_provider,
        selected_model=st.session_state.selected_model
    )

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("*Local RAG System v2.0 - Fase 5.1*")