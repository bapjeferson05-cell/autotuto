import json, time, threading, urllib.request

from autotuto.visor import Visor


def _post(porta, rota, texto):
    urllib.request.urlopen(urllib.request.Request(
        f"http://127.0.0.1:{porta}{rota}", data=json.dumps({"texto": texto}).encode(),
        headers={"Content-Type": "application/json"}, method="POST"))


def test_estado_e_frame():
    v = Visor(porta=8123, ritmo=0.001).start()
    time.sleep(0.2)
    try:
        v.desenhar(b"\x89PNG_fake", "x")
        v.mostrar_fala("olá")
        with urllib.request.urlopen("http://127.0.0.1:8123/estado") as resp:
            s = json.loads(resp.read())
        assert s["professor"] == "olá" and s["frame"] == 1
        with urllib.request.urlopen("http://127.0.0.1:8123/frame.png") as resp:
            png = resp.read()
        assert png == b"\x89PNG_fake"
    finally:
        v.stop()


def test_tecla_vira_injecao_e_falar_devolve():
    v = Visor(porta=8124, ritmo=0.05).start()
    time.sleep(0.2)
    try:
        res = {}

        def fala_longa():
            res["r"] = v.falar("uma frase bem longa " * 5)

        th = threading.Thread(target=fala_longa)
        th.start()
        time.sleep(0.3)
        _post(8124, "/interromper", "não entendi")
        th.join(3)
        assert res["r"] == "não entendi"
    finally:
        v.stop()


def test_caixa_de_texto_vira_pergunta():
    v = Visor(porta=8125, ritmo=0.001).start()
    time.sleep(0.2)
    try:
        _post(8125, "/perguntar", "me explica trapézio")
        assert v.pop_pergunta() == "me explica trapézio"
        assert v.pop_pergunta() is None
    finally:
        v.stop()


def test_html_keydown_ignora_input():
    v = Visor(porta=8126, ritmo=0.001).start()
    time.sleep(0.2)
    try:
        html = urllib.request.urlopen("http://127.0.0.1:8126/").read().decode()
        assert 'e.target.tagName === "INPUT"' in html
        assert 'e.target.tagName === "TEXTAREA"' in html
    finally:
        v.stop()
