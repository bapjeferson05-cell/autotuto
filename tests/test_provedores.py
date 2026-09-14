"""test_provedores.py — o caminho OpenAI-compatível (Groq, OpenRouter, NVIDIA,
GitHub Models, Gemini...) e o comando que grava a chave. Zero rede: o urlopen é
trocado por dublê, igual test_llm.py já faz."""
import json

import pytest

from autotuto import chaves, llm, provedores


class _Resp:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._payload


def _fake_urlopen(capturado, texto="{}"):
    def _f(req, timeout):
        capturado["url"] = req.full_url
        capturado["headers"] = dict(req.headers)
        capturado["body"] = json.loads(req.data)
        return _Resp({"choices": [{"message": {"content": texto}}]})
    return _f


# ───────────────────────────────────────────── a tabela de provedores
def test_todo_provedor_tem_os_campos_que_o_llm_usa():
    for nome, info in provedores.PROVEDORES.items():
        for campo in ("base", "chave_env", "modelo", "json_nativo", "limite", "onde", "cadastro"):
            assert campo in info, f"{nome} não tem '{campo}'"
        assert info["base"].startswith("http"), nome


def test_nomes_inclui_nativos_e_nuvem():
    assert "ollama" in provedores.nomes() and "groq" in provedores.nomes()
    assert provedores.conhecido("openrouter") and not provedores.conhecido("inexistente")


# ───────────────────────────────────────────── o caminho OpenAI-compatível
def test_groq_monta_a_chamada_certa(monkeypatch):
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "chave-secreta")
    monkeypatch.setattr(llm.urllib.request, "urlopen", _fake_urlopen(cap, '{"ok":1}'))

    out = llm.perguntar([{"role": "user", "content": "oi"}], timeout=5)

    assert json.loads(out) == {"ok": 1}
    assert cap["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert cap["headers"]["Authorization"] == "Bearer chave-secreta"
    assert cap["body"]["model"] == "llama-3.3-70b-versatile"


def test_sem_chave_avisa_onde_pegar(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ConnectionError) as e:
        llm.perguntar([{"role": "user", "content": "x"}], timeout=5)
    assert "GROQ_API_KEY" in str(e.value) and "console.groq.com" in str(e.value)


def test_json_mode_instrui_no_system_pra_todo_provedor(monkeypatch):
    """A instrução de JSON tem que ir no system mesmo em provedor sem
    response_format nativo (nvidia) — senão volta prosa e o planejador quebra."""
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "k")
    monkeypatch.setattr(llm.urllib.request, "urlopen", _fake_urlopen(cap))

    llm.perguntar([{"role": "system", "content": "seja o professor"},
                   {"role": "user", "content": "oi"}], timeout=5)

    assert "JSON" in cap["body"]["messages"][0]["content"]
    assert "response_format" not in cap["body"]  # nvidia não aceita


def test_provedor_com_json_nativo_manda_response_format(monkeypatch):
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setattr(llm.urllib.request, "urlopen", _fake_urlopen(cap))
    llm.perguntar([{"role": "user", "content": "oi"}], timeout=5)
    assert cap["body"]["response_format"] == {"type": "json_object"}


def test_json_mode_off_nao_mexe_nas_mensagens(monkeypatch):
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setattr(llm.urllib.request, "urlopen", _fake_urlopen(cap))
    llm.perguntar([{"role": "user", "content": "oi"}], timeout=5, json_mode=False)
    assert cap["body"]["messages"] == [{"role": "user", "content": "oi"}]
    assert "response_format" not in cap["body"]


def test_nao_muta_a_lista_de_mensagens_do_chamador(monkeypatch):
    """O planejador reusa a lista de mensagens no loop de correção — se a gente
    grudasse a instrução de JSON no dict dele, ela se repetiria a cada tentativa."""
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setattr(llm.urllib.request, "urlopen", _fake_urlopen(cap))

    original = [{"role": "system", "content": "seja o professor"}]
    llm.perguntar(original, timeout=5)

    assert original == [{"role": "system", "content": "seja o professor"}]


def test_base_url_propria_ganha_do_provedor(monkeypatch):
    """AUTOTUTO_BASE_URL é o que deixa apontar num vLLM/LM Studio local."""
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setattr(llm.config, "LLM_BASE_URL", "http://localhost:8000/v1/")
    monkeypatch.setattr(llm.urllib.request, "urlopen", _fake_urlopen(cap))
    llm.perguntar([{"role": "user", "content": "oi"}], timeout=5)
    assert cap["url"] == "http://localhost:8000/v1/chat/completions"


def test_modelo_explicito_ganha_do_default_do_provedor(monkeypatch):
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setattr(llm.config, "LLM_MODELO_NUVEM", "llama-3.1-8b-instant")
    monkeypatch.setattr(llm.urllib.request, "urlopen", _fake_urlopen(cap))
    llm.perguntar([{"role": "user", "content": "oi"}], timeout=5)
    assert cap["body"]["model"] == "llama-3.1-8b-instant"


def test_ollama_continua_sendo_o_default(monkeypatch):
    """Ninguém que já usava o projeto pode acordar com outro provedor."""
    cap = {}
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "ollama")

    def fake(req, timeout):
        cap["url"] = req.full_url
        return _Resp({"message": {"content": "{}"}})

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake)
    llm.perguntar([{"role": "user", "content": "oi"}], timeout=5)
    assert "/api/chat" in cap["url"]


# ───────────────────────────────────────────── python -m autotuto.chaves
def test_configura_grava_chave_e_provedor(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(chaves, "ENV", tmp_path / ".env")

    chaves.configura("groq", "gsk-teste")

    conteudo = (tmp_path / ".env").read_text()
    assert "GROQ_API_KEY=gsk-teste" in conteudo
    assert "AUTOTUTO_LLM=groq" in conteudo


def test_configura_preserva_chaves_de_outros_provedores(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(chaves, "ENV", tmp_path / ".env")
    chaves.configura("groq", "gsk-1")
    chaves.configura("gemini", "gem-2")
    conteudo = (tmp_path / ".env").read_text()
    assert "GROQ_API_KEY=gsk-1" in conteudo      # a antiga continua lá
    assert "GEMINI_API_KEY=gem-2" in conteudo
    assert "AUTOTUTO_LLM=gemini" in conteudo     # mas o ativo virou o novo


def test_env_gravado_so_o_dono_le(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(chaves, "ENV", tmp_path / ".env")
    chaves.configura("groq", "gsk-1")
    assert oct((tmp_path / ".env").stat().st_mode)[-3:] == "600"


def test_mascara_nao_vaza_a_chave():
    assert chaves._mascara("gsk-abcdefgh1234") == "····1234"
    assert "abcdefgh" not in chaves._mascara("gsk-abcdefgh1234")
