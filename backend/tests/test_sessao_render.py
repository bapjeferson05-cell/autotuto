"""test_sessao_render.py — cobre o caminho de renderização que as aulas de ouro
(trapézio, pitágoras...) nunca exercitam: geradores por `params` (funcao, triangulo,
solido, curva...), não só o `figura`/`spec` composto. Sem isso, um bloco gerado pelo
PLANEJADOR (LLM) pedindo um gráfico de função nunca tinha sido testado de verdade."""
import base64

from backend.services.sessao import _renderiza_bloco


def _decodifica(b64: str) -> bytes:
    return base64.b64decode(b64)


def test_figura_por_params_funcao_gera_png():
    bloco = {"diz": "Olha o gráfico da parábola.",
             "figura": {"gerador": "funcao",
                        "params": {"expr": "x**2 - 2*x - 3", "raiz": True, "vertice": True}}}
    saida = _renderiza_bloco(bloco)
    png = _decodifica(saida["figura_png_base64"])
    assert png.startswith(b"\x89PNG")


def test_figura_por_params_triangulo_gera_png():
    bloco = {"diz": "Um triângulo retângulo.",
             "figura": {"gerador": "triangulo", "params": {"tipo": "retangulo"}}}
    saida = _renderiza_bloco(bloco)
    assert _decodifica(saida["figura_png_base64"]).startswith(b"\x89PNG")


def test_figura_por_params_solido_3d_gera_png():
    bloco = {"diz": "Um cubo.",
             "figura": {"gerador": "solido", "params": {"nome": "cubo"}}}
    saida = _renderiza_bloco(bloco)
    assert _decodifica(saida["figura_png_base64"]).startswith(b"\x89PNG")


def test_calc_sem_mostra_passos_devolve_so_o_ultimo_passo():
    bloco = {"diz": "84 metros quadrados.",
             "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}}}
    saida = _renderiza_bloco(bloco)
    assert saida["valor"] == 84.0
    assert len(saida["passos_latex"]) == 1
