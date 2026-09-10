import io

from PIL import Image

from autotuto.calc import area_trapezio
from autotuto.figuras.canvas import figura
from autotuto.figuras.catalogo import GERADORES
from autotuto.figuras.lousa import nova_figura, para_png, passo_latex

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _dims(png):
    return Image.open(io.BytesIO(png)).size


def test_passo_latex_gera_png():
    png = passo_latex(r"A = \dfrac{(B+b)h}{2}")
    assert png[:8] == PNG_MAGIC
    assert _dims(png)[0] > 100


def test_passo_latex_com_step_real_do_calc():
    # todo passo LaTeX do calc tem que passar pelo mathtext do matplotlib
    for passo in area_trapezio(B=18, b=10, h=6).passos:
        png = passo_latex(passo)
        assert png[:4] == b"\x89PNG"


def test_nova_figura_e_para_png():
    fig, ax = nova_figura()
    ax.plot([0, 1, 2], [0, 1, 0])
    png = para_png(fig)
    assert png[:4] == b"\x89PNG"


def test_figura_composicao_minima():
    png = figura({
        "pontos": {"A": [0, 0], "B": [4, 0], "C": [2, 3]},
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}],
        "rotulos": [{"xy": [2, -0.5], "texto": "base"}],
    })
    assert png[:4] == b"\x89PNG"


def test_figura_coords_cruas_e_todos_os_elementos():
    png = figura({
        "pontos": {"A": [0, 0], "B": [4, 0], "C": [4, 3]},
        "segmentos": [["A", "B"], ["B", [4, 3]], [[4, 3], "A"]],
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": False}],
        "angulos": [{"vertice": "B", "de": "A", "para": "C"}],
        "marcas": [{"tipo": "cong", "de": "A", "para": "B"},
                   {"tipo": "par", "de": "B", "para": "C"}],
        "rotulos": [{"xy": [2, -0.4], "texto": "4"}],
    })
    assert png[:4] == b"\x89PNG"


def test_figura_spec_vazio_nao_quebra():
    assert figura({})[:4] == b"\x89PNG"


def test_todos_os_geradores_desenham():
    # "figura" recebe um spec posicional; os geradores nomeados recebem kwargs
    spec_minimo = {"pontos": {"A": [0, 0], "B": [1, 0], "C": [0, 1]},
                   "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}]}
    kwargs = {
        "dois_retangulos": {"B": 18, "b": 10, "h": 6},
        "balanca": {"esq": "3x", "dir": "15"},
        "tabela_prop": {"a": 3, "b": 24, "c": 5, "x": 40},
    }
    for nome, fn in GERADORES.items():
        if nome == "figura":
            png = fn(spec_minimo)
        else:
            png = fn(**kwargs.get(nome, {}))
        assert png[:4] == b"\x89PNG", nome


def test_geradores_tem_as_chaves_esperadas():
    assert set(GERADORES) == {"figura", "trapezio", "triangulo", "retangulo",
                              "dois_retangulos", "balanca", "tabela_prop",
                              "reta_numerica"}
    assert GERADORES["figura"] is figura
