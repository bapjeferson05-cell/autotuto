"""test_calc.py — professor/calc.py é o motor de aritmética do projeto: a razão de
ele existir é que o LLM erra conta (README/PESQUISA_pedagogia-llm.md) e o Python não
pode. Isso nunca tinha um teste dedicado — só verificação manual. Cobre as 16 funções
do CATALOGO com valores conhecidos e os casos de borda de cada uma.
"""
import math

import pytest

from professor import calc


# ─────────────────────────────────────────────────────────── áreas / perímetros
def test_area_trapezio():
    r = calc.area_trapezio(B=18, b=10, h=6)
    assert r.valor == 84.0
    assert len(r.passos) == 3


def test_area_triangulo():
    r = calc.area_triangulo(base=8, altura=5)
    assert r.valor == 20.0


def test_area_circulo():
    r = calc.area_circulo(r=4)
    assert r.valor == pytest.approx(50.27, abs=0.01)


def test_area_retangulo():
    assert calc.area_retangulo(base=6, altura=4).valor == 24


def test_comprimento_circunferencia_por_raio():
    assert calc.comprimento_circunferencia(r=4).valor == pytest.approx(25.13, abs=0.01)


def test_comprimento_circunferencia_por_diametro_bate_com_raio():
    assert calc.comprimento_circunferencia(d=8).valor == calc.comprimento_circunferencia(r=4).valor


def test_perimetro_poligono_regular():
    assert calc.perimetro_poligono_regular(n=6, lado=5).valor == 30


# ─────────────────────────────────────────────────────────── pitágoras
def test_pitagoras_acha_hipotenusa():
    r = calc.pitagoras(a=3, b=4)
    assert r.valor == 5.0


def test_pitagoras_acha_cateto_dado_a_e_c():
    assert calc.pitagoras(a=3, c=5).valor == 4.0


def test_pitagoras_acha_cateto_dado_b_e_c_e_simetrico():
    assert calc.pitagoras(b=4, c=5).valor == 3.0


# ─────────────────────────────────────────────────────────── equações
def test_eq_primeiro_grau_resolve():
    r = calc.eq_primeiro_grau(a=2, b=-10)
    assert r.valor == "5"


def test_eq_primeiro_grau_fracao_nao_inteira():
    r = calc.eq_primeiro_grau(a=3, b=1)
    assert r.valor == "\\tfrac{-1}{3}"


def test_eq_primeiro_grau_a_zero_e_b_nao_zero_e_sem_solucao():
    assert calc.eq_primeiro_grau(a=0, b=5).valor == "sem solução"


def test_eq_primeiro_grau_a_zero_e_b_zero_e_infinitas_solucoes():
    assert calc.eq_primeiro_grau(a=0, b=0).valor == "infinitas"


def test_bhaskara_duas_raizes():
    r = calc.bhaskara(a=1, b=-2, c=-3)
    assert r.valor == (3.0, -1.0)


def test_bhaskara_sem_raizes_reais():
    r = calc.bhaskara(a=1, b=0, c=1)
    assert r.valor == "sem raízes reais"
    assert any("Delta" in p or "\\Delta" in p for p in r.passos)


# ─────────────────────────────────────────────────────────── proporção / %
def test_porcentagem_quanto_e_pct_de_todo():
    r = calc.porcentagem(todo=240, pct=15)
    assert r.valor == 36.0


def test_porcentagem_parte_sobre_todo():
    r = calc.porcentagem(parte=30, todo=240)
    assert r.valor == 12.5


def test_regra_de_tres():
    r = calc.regra_de_tres(a=3, b=12, c=5)
    assert r.valor == 20.0


# ─────────────────────────────────────────────────────────── mdc / mmc
def test_mdc():
    assert calc.mdc(12, 18).valor == 6


def test_mmc():
    assert calc.mmc(4, 6).valor == 12


def test_mdc_e_mmc_sao_coerentes_entre_si():
    a, b = 12, 18
    assert calc.mdc(a, b).valor * calc.mmc(a, b).valor == a * b


# ─────────────────────────────────────────────────────────── dia a dia
def test_media():
    assert calc.media([7, 8, 6, 9]).valor == 7.5


def test_velocidade_media():
    assert calc.velocidade_media(distancia=240, tempo=3).valor == 80.0


def test_juros_simples():
    r = calc.juros_simples(capital=1000, taxa=2, tempo=6)
    assert r.valor == 120.0
    assert any("1120" in p for p in r.passos)  # o montante (capital + juros) aparece nos passos


# ─────────────────────────────────────────────────────────── contrato geral
@pytest.mark.parametrize("nome", list(calc.CATALOGO))
def test_todo_gerador_do_catalogo_devolve_resultado_com_passos(nome):
    """Contrato mínimo: todo item do CATALOGO (o que o esquema.py expõe pro LLM e
    pro backend web) devolve um Resultado com pelo menos um passo em LaTeX."""
    exemplos = {
        "area_trapezio": dict(B=18, b=10, h=6),
        "area_triangulo": dict(base=8, altura=5),
        "area_circulo": dict(r=4),
        "area_retangulo": dict(base=6, altura=4),
        "pitagoras": dict(a=3, b=4),
        "eq_primeiro_grau": dict(a=2, b=-10),
        "bhaskara": dict(a=1, b=-2, c=-3),
        "porcentagem": dict(todo=240, pct=15),
        "regra_de_tres": dict(a=3, b=12, c=5),
        "mdc": dict(a=12, b=18),
        "mmc": dict(a=4, b=6),
        "media": dict(valores=[7, 8, 6, 9]),
        "velocidade_media": dict(distancia=240, tempo=3),
        "juros_simples": dict(capital=1000, taxa=2, tempo=6),
        "comprimento_circunferencia": dict(r=4),
        "perimetro_poligono_regular": dict(n=6, lado=5),
    }
    r = calc.CATALOGO[nome](**exemplos[nome])
    assert isinstance(r.passos, list) and len(r.passos) >= 1
    assert all(isinstance(p, str) and p for p in r.passos)
    assert r.valor not in (None, "")
