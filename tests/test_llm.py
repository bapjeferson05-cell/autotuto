import json
from autotuto import llm


def test_dispatch_ollama(monkeypatch):
    capturado = {}
    def fake_urlopen(req, timeout):
        capturado["url"] = req.full_url
        capturado["body"] = json.loads(req.data)
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def read(s): return json.dumps({"message": {"content": '{"ok": 1}'}}).encode()
        return R()
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "ollama")
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    out = llm.perguntar([{"role": "user", "content": "oi"}], timeout=5)
    assert json.loads(out) == {"ok": 1}
    assert "/api/chat" in capturado["url"] and capturado["body"]["format"] == "json"


def test_claude_sem_chave_erra(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVEDOR", "claude")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        llm.perguntar([{"role": "user", "content": "x"}], timeout=5)
        assert False
    except ConnectionError:
        pass


def test_perguntar_e_resolvido_em_runtime_nao_no_import():
    # `def f(perguntar=llm.perguntar)` congela a função no import: trocar
    # `llm.perguntar` depois (mock, ou provedor escolhido em runtime) não tinha
    # efeito nenhum. Descoberto porque a bateria não conseguia rodar offline.
    from autotuto import avaliador, cerebro, llm, planejador

    chamadas = []

    def falso(mensagens, **k):
        chamadas.append(mensagens)
        raise ConnectionError("sem llm")

    original = llm.perguntar
    llm.perguntar = falso
    try:
        planejador.planeja("qualquer coisa")
        cerebro.roteia_interrupcao("oi", "ctx", {"por_que": [{"diz": "x"}]})
        avaliador.avalia_resposta("p", ["x"], "resposta do aluno")
    finally:
        llm.perguntar = original
    assert len(chamadas) == 3, chamadas


# ───── constrained decoding: JSON Schema no `format` do ollama

def test_esquema_vai_no_format_do_ollama():
    # "json" solto garante que sai um JSON — e só. Com o schema, o decoder é
    # obrigado a respeitar a FORMA, e o plano deixa de poder vir torto.
    import json as _json

    from autotuto import llm
    from autotuto.schema import esquema_json

    vistos = []

    class _Falsa:
        def __init__(self, corpo): self._c = corpo
        def read(self): return b'{"message": {"content": "{}"}}'
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _espia(req, timeout=None):
        vistos.append(_json.loads(req.data))
        return _Falsa(None)

    original = llm.urllib.request.urlopen
    llm.urllib.request.urlopen = _espia
    try:
        llm._ollama([{"role": "user", "content": "oi"}], 5, True, esquema_json())
        llm._ollama([{"role": "user", "content": "oi"}], 5, True, None)
    finally:
        llm.urllib.request.urlopen = original

    assert isinstance(vistos[0]["format"], dict)          # o schema foi junto
    assert vistos[0]["format"]["properties"]["blocos"]["type"] == "array"
    assert vistos[1]["format"] == "json"                  # sem esquema: como antes


def test_esquema_vem_desligado_por_padrao():
    # formato restrito derruba raciocínio (paper "Let Me Speak Freely?") e
    # schema fundo quebra modelo pequeno. Fica off até a bateria medir.
    from autotuto import config
    assert config.LLM_ESQUEMA_ESTRITO is False


def test_planejador_so_manda_esquema_quando_a_flag_liga():
    import json as _json

    from autotuto import config, planejador
    from autotuto.aulas import carregar

    vistos = []

    def espia(mensagens, *, timeout, json_mode=True, esquema=None):
        vistos.append(esquema)
        return _json.dumps(carregar("trapezio").para_json())

    planejador.planeja("qualquer coisa", perguntar=espia)
    assert vistos[-1] is None

    config.LLM_ESQUEMA_ESTRITO = True
    try:
        planejador.planeja("qualquer coisa", perguntar=espia)
    finally:
        config.LLM_ESQUEMA_ESTRITO = False
    assert isinstance(vistos[-1], dict)
