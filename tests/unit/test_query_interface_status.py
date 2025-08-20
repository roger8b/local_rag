import os
from src.ui.pages.query_interface import get_provider_status


def test_get_provider_status_openai_configured(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
    emoji, desc = get_provider_status("openai")
    assert emoji == "🟢"
    assert "Configurado" in desc


def test_get_provider_status_openai_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    emoji, desc = get_provider_status("openai")
    assert emoji == "🔴"
    assert "não configurada" in desc


def test_get_provider_status_gemini_configured(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "A" * 32)
    emoji, desc = get_provider_status("gemini")
    assert emoji == "🟢"
    assert "Configurado" in desc


def test_get_provider_status_gemini_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    emoji, desc = get_provider_status("gemini")
    assert emoji == "🔴"
    assert "não configurada" in desc
