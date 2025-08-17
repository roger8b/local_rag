#!/usr/bin/env python3
"""
Script para executar a interface Streamlit de chat do Local RAG.

Uso recomendado:
    streamlit run run_interface.py --server.address 0.0.0.0 --server.port 8501

Observação: A URL da API é lida de API_BASE_URL (default http://localhost:8000).
"""

from src.ui.pages.query_interface import render_page


if __name__ == "__main__":
    # Executa a página de chat
    render_page()

