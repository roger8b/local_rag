"""Configuração de testes compartilhada.

Garante que a raiz do repositório esteja no sys.path para permitir
imports como `from src...` em todos os ambientes (incluindo GitHub Actions).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

