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


def test_contorno_do_poligono_preenchido_fica_opaco():
    # F4: o `alpha` do preenchimento NÃO pode apagar o traço de giz. Com o bug
    # antigo (alpha no patch inteiro) a borda saía ~cinza-escuro sobre o fundo.
    png = figura({
        "pontos": {"A": [0, 0], "B": [4, 0], "C": [2, 3]},
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}],
    })
    mais_claro = Image.open(io.BytesIO(png)).convert("L").getextrema()[1]
    assert mais_claro > 200, mais_claro       # existe traço quase branco (giz cheio)


def test_segmento_tracejado_renderiza():
    # F5: suporte a segmento em forma de dict com "tracejado"
    png = figura({
        "pontos": {"D": [4, 6], "H": [4, 0]},
        "segmentos": [{"de": "D", "para": "H", "tracejado": True}],
    })
    assert png[:4] == b"\x89PNG"


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
                              "reta_numerica", "circulo", "fracao"}
    assert GERADORES["figura"] is figura


def test_reta_numerica_rejeita_passo_nao_positivo():
    # Bug do code-review: passo<=0 fazia `while n <= fim` nunca avançar o
    # suficiente e travar num loop infinito. Tem que falhar rápido, não travar.
    import pytest
    from autotuto.figuras.catalogo import reta_numerica
    with pytest.raises(ValueError):
        reta_numerica(inicio=0, fim=10, passo=0)
    with pytest.raises(ValueError):
        reta_numerica(inicio=0, fim=10, passo=-1)


# ─────────────────────────────────────────────── o arco do ângulo (bug do reflexo)

def _arcos_de(pontos, ang):
    """Desenha só o ângulo num ax limpo e devolve os patches Arc criados."""
    from matplotlib.patches import Arc

    from autotuto.figuras.canvas import _desenha_angulo
    from autotuto.figuras.lousa import nova_figura

    _, ax = nova_figura()
    _desenha_angulo(ax, {"pontos": pontos}, ang)
    return [p for p in ax.patches if isinstance(p, Arc)]


def test_arco_nunca_desenha_o_angulo_reflexo():
    # BUG: o Arc do matplotlib varre SEMPRE anti-horário de theta1 a theta2.
    # Com min/max, lados em 170° e -170° (que são 20° de abertura!) viravam
    # theta1=-170, theta2=170 -> arco de 340°: o professor marcava o ângulo de
    # FORA e a fala não batia com o desenho. O aluno via uma mentira no quadro.
    casos = [
        # (pontos do vértice/lados, abertura real em graus)
        ({"V": [0, 0], "A": [-0.985, 0.174], "C": [-0.985, -0.174]}, 20.0),   # ±180
        ({"V": [0, 0], "A": [1, 0], "C": [0.5, 0.866]}, 60.0),                # normal
        ({"V": [0, 0], "A": [0.5, 0.866], "C": [1, 0]}, 60.0),                # invertido
        ({"V": [0, 0], "A": [1, 0], "C": [-0.940, 0.342]}, 160.0),            # obtuso
    ]
    for pontos, esperado in casos:
        arcos = _arcos_de(pontos, {"vertice": "V", "de": "A", "para": "C"})
        assert len(arcos) == 1, pontos
        varrido = (arcos[0].theta2 - arcos[0].theta1) % 360
        assert abs(varrido - esperado) < 1.0, (pontos, varrido, esperado)
        assert varrido <= 180.0 + 1e-9, (pontos, varrido)


def test_angulo_reto_vira_quadradinho_e_nao_arco():
    arcos = _arcos_de({"V": [0, 0], "A": [1, 0], "C": [0, 1]},
                      {"vertice": "V", "de": "A", "para": "C"})
    assert arcos == []


# ─────────────────────────────────────────────────────────── círculos e fatias

def test_circulo_inteiro_renderiza():
    png = figura({"pontos": {"O": [0, 0]},
                  "circulos": [{"centro": "O", "raio": 3, "preenche": True}]})
    assert png[:8] == PNG_MAGIC


def test_circulo_com_setor_e_tracejado():
    png = figura({"circulos": [
        {"centro": [0, 0], "raio": 4, "setor": [90, 180], "preenche": True},
        {"centro": [0, 0], "raio": 4, "setor": [180, 270], "tracejado": True},
    ]})
    assert png[:8] == PNG_MAGIC


def test_circulo_entra_no_autoscale():
    # patch do matplotlib NÃO mexe no datalim sozinho: sem update_datalim o
    # círculo ficava fora do enquadramento (lousa em branco pro aluno).
    from autotuto.figuras.canvas import _desenha_circulo
    from autotuto.figuras.lousa import nova_figura

    _, ax = nova_figura()
    _desenha_circulo(ax, {"pontos": {}}, {"centro": [50, 50], "raio": 5})
    x0, y0, x1, y1 = ax.dataLim.extents
    assert x0 <= 45.001 and x1 >= 54.999
    assert y0 <= 45.001 and y1 >= 54.999


def test_contorno_do_circulo_preenchido_fica_opaco():
    # mesma regra do polígono (F4): o alpha do preenchimento não pode apagar o giz
    png = figura({"circulos": [{"centro": [0, 0], "raio": 3, "preenche": True}]})
    mais_claro = Image.open(io.BytesIO(png)).convert("L").getextrema()[1]
    assert mais_claro > 200, mais_claro


def test_fracao_desenha_uma_fatia_por_denominador():
    from autotuto.figuras.catalogo import fracao
    for den in (1, 2, 3, 4, 8):
        assert fracao(num=1, den=den)[:8] == PNG_MAGIC


def test_fracao_rejeita_parametros_impossiveis():
    import pytest

    from autotuto.figuras.catalogo import fracao
    with pytest.raises(ValueError):
        fracao(num=1, den=0)
    with pytest.raises(ValueError):
        fracao(num=5, den=4)      # 5/4 de pizza não existe no desenho
    with pytest.raises(ValueError):
        fracao(num=-1, den=4)


def test_circulo_rejeita_raio_nao_positivo():
    import pytest

    from autotuto.figuras.catalogo import circulo
    with pytest.raises(ValueError):
        circulo(raio=0)
    with pytest.raises(ValueError):
        circulo(raio=-2)


def _luz_media(png):
    """Luminância média da imagem — proxy de 'quanto tem coisa pintada'."""
    import numpy as np
    return float(np.asarray(Image.open(io.BytesIO(png)).convert("L"),
                            dtype=float).mean())


def test_fatia_pintada_se_distingue_da_fatia_vazia():
    # A fatia pintada É a resposta da fração. Com o alpha discreto do polígono
    # (0.12) a pizza 3/4 saía quase idêntica à 0/4 na lousa escura: o desenho
    # não dizia 3/4 pro aluno. Por isso setor usa ALPHA_PINTADO.
    from autotuto.figuras.catalogo import fracao
    cheia, vazia = _luz_media(fracao(4, 4)), _luz_media(fracao(0, 4))
    assert cheia - vazia > 15, (cheia, vazia)


def test_preenchimento_de_figura_continua_discreto():
    # o outro lado da moeda: o fill que só diz "é desta figura que eu falo"
    # não pode virar bloco de cor e engolir o traço de giz.
    from autotuto.figuras.catalogo import fracao
    cheio = _luz_media(figura({"circulos": [{"centro": [0, 0], "raio": 5,
                                             "preenche": True}]}))
    vazio = _luz_media(figura({"circulos": [{"centro": [0, 0], "raio": 5}]}))
    destaque = _luz_media(fracao(4, 4)) - _luz_media(fracao(0, 4))
    assert 0 < cheio - vazio < destaque / 3, (cheio, vazio, destaque)


def test_circulo_com_raio_invalido_falha_alto():
    # não pode desenhar em silêncio um círculo que não existe: o tocador captura
    # a exceção e o professor admite a limitação em vez de mostrar um borrão.
    import pytest
    with pytest.raises(ValueError):
        figura({"circulos": [{"centro": [0, 0], "raio": 0}]})
    with pytest.raises(ValueError):
        figura({"circulos": [{"centro": [0, 0], "raio": -3}]})


def test_reta_numerica_recusa_intervalo_absurdo():
    # `reta_numerica(0, 1000000)` desenharia um milhão de traços e travaria a
    # aula — e, como o validador agora DESENHA pra validar, travaria o
    # planejador antes de o aluno ouvir a primeira frase.
    import pytest

    from autotuto import config
    from autotuto.figuras.catalogo import reta_numerica
    with pytest.raises(ValueError) as e:
        reta_numerica(inicio=0, fim=1_000_000, passo=1)
    assert str(config.MAX_MARCAS_RETA) in str(e.value)   # a mensagem ensina o teto
    # o intervalo normal de aula continua passando
    assert reta_numerica(inicio=0, fim=10, passo=1)[:4] == b"\x89PNG"
    assert reta_numerica(inicio=0, fim=1000, passo=100)[:4] == b"\x89PNG"


def test_reta_numerica_absurda_vira_aviso_grave_e_nao_trava():
    import time

    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [{"diz": "olha a reta", "figura": {
        "gerador": "reta_numerica",
        "params": {"inicio": 0, "fim": 1_000_000, "passo": 1}}}]}
    t0 = time.monotonic()
    avisos = checar_matematica(plano)
    assert time.monotonic() - t0 < 2.0        # falhou rápido, não desenhou
    assert avisos_graves(avisos)


def test_angulos_vizinhos_podem_ter_raios_diferentes():
    # dois ângulos vizinhos no MESMO raio (43° e 47° fechando o canto reto)
    # emendam num arco contínuo de 90°: o aluno vê UM ângulo, não dois.
    from matplotlib.patches import Arc

    from autotuto.figuras.canvas import _desenha_angulo
    from autotuto.figuras.lousa import nova_figura

    spec = {"pontos": {"V": [0, 0], "P": [4.5, 0], "Q": [0, 4.5], "R": [3.29, 3.07]}}
    _, ax = nova_figura()
    _desenha_angulo(ax, spec, {"vertice": "V", "de": "P", "para": "R", "raio": 0.9})
    _desenha_angulo(ax, spec, {"vertice": "V", "de": "R", "para": "Q", "raio": 1.7})
    arcos = [p for p in ax.patches if isinstance(p, Arc)]
    assert len(arcos) == 2
    larguras = sorted(a.get_width() for a in arcos)
    assert larguras[0] < larguras[1], larguras     # raios de fato diferentes


def test_raio_do_arco_tem_default_no_config():
    from matplotlib.patches import Arc

    from autotuto import config
    from autotuto.figuras.canvas import _desenha_angulo
    from autotuto.figuras.lousa import nova_figura

    _, ax = nova_figura()
    _desenha_angulo(ax, {"pontos": {"V": [0, 0], "A": [1, 0], "B": [0.5, 0.87]}},
                    {"vertice": "V", "de": "A", "para": "B"})
    arco = next(p for p in ax.patches if isinstance(p, Arc))
    assert arco.get_width() == 2 * config.RAIO_ARCO
