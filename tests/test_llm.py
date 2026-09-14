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
