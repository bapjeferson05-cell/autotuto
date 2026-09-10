import math
from autotuto.calc import (Resultado, area_trapezio, area_triangulo, area_retangulo,
                           pitagoras, eq_primeiro_grau, regra_de_tres, CATALOGO)

def test_trapezio_valor_e_passos():
    r = area_trapezio(B=18, b=10, h=6)
    assert r.valor == 84 and r.unidade == "u²"
    assert r.passos[0].startswith("A =") and "84" in r.passos[-1]

def test_triangulo():
    assert area_triangulo(8, 5).valor == 20

def test_pitagoras_hipotenusa():
    assert round(pitagoras(a=3, b=4).valor, 4) == 5.0

def test_pitagoras_cateto():
    r = pitagoras(a=3, c=5)
    assert round(r.valor, 4) == 4.0
    # F3: não pode renderizar a equação falsa "cat^2 = c^2 - cat^2"
    assert "cat^2 = c^2 - cat^2" not in " ".join(r.passos)
    assert r.passos[0] == "b^2 = c^2 - a^2"
    assert "3^2" in r.passos[1] and "5^2" in r.passos[1]


def test_pitagoras_cateto_b_conhecido():
    # F5: com `b` conhecido, a incógnita é `a` — a equação não pode mentir que
    # o conhecido era `a`.
    r = pitagoras(b=4, c=5)
    assert round(r.valor, 4) == 3.0
    assert r.passos[0] == "a^2 = c^2 - b^2"
    assert "4^2" in r.passos[1] and "5^2" in r.passos[1]

def test_eq_render_negativo():
    r = eq_primeiro_grau(3, -15)                 # 3x - 15 = 0
    assert "3x - 15 = 0" in r.passos[0].replace("\\", "")
    assert r.valor == "5"

def test_regra_de_tres():
    assert regra_de_tres(3, 24, 5).valor == 40

def test_catalogo_tem_as_seis():
    assert set(CATALOGO) == {"area_trapezio", "area_triangulo", "area_retangulo",
                             "pitagoras", "eq_primeiro_grau", "regra_de_tres"}
