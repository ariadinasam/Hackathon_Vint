"""Configuração comum do pytest.

Roda ANTES de qualquer import do app: força o snapshot SQLite do SGD (somente leitura), um banco do app
temporário (nunca o data/app.db real) e IA desligada (nenhuma chamada sai para a internet; os testes de IA
usam rede simulada).
"""
import os
import tempfile

os.environ["REFERENCE_MONTH"] = "2026-11"
os.environ["DATA_SOURCE"] = "sqlite"
os.environ["LLM_PROVIDER"] = "none"
os.environ["APP_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="vintmatch_teste_"), "app_teste.db")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _ia_limpa():
    """Cada teste começa sem a 'pausa' de provedor que falhou em outro teste."""
    from app import llm
    llm._falhou_em.clear()
    yield
    llm._falhou_em.clear()
