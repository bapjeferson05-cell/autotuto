import importlib

from autotuto import config


def _recarrega():
    """config.py lê os env vars uma vez, no import — precisa recarregar pra
    testar um AUTOTUTO_PERFIL/AUTOTUTO_LLM diferente (mesma pegadinha de llm.py,
    que copia LLM_PROVEDOR uma vez no import)."""
    importlib.reload(config)


def test_perfil_leve_usa_claude_por_padrao(monkeypatch):
    monkeypatch.setenv("AUTOTUTO_PERFIL", "leve")
    monkeypatch.delenv("AUTOTUTO_LLM", raising=False)
    _recarrega()
    try:
        assert config.LLM_PROVEDOR == "claude"
        assert config.STT_MODELO == "tiny"
    finally:
        _recarrega()  # não vaza estado pros outros testes


def test_perfil_pesado_e_o_padrao_de_sempre(monkeypatch):
    monkeypatch.delenv("AUTOTUTO_PERFIL", raising=False)
    monkeypatch.delenv("AUTOTUTO_LLM", raising=False)
    monkeypatch.delenv("AUTOTUTO_STT", raising=False)
    _recarrega()
    try:
        assert config.PERFIL == "pesado"
        assert config.LLM_PROVEDOR == "ollama"
        assert config.STT_MODELO == "base"
    finally:
        _recarrega()


def test_llm_explicito_sempre_ganha_do_perfil(monkeypatch):
    monkeypatch.setenv("AUTOTUTO_PERFIL", "leve")
    monkeypatch.setenv("AUTOTUTO_LLM", "ollama")
    _recarrega()
    try:
        assert config.LLM_PROVEDOR == "ollama"
    finally:
        _recarrega()
