import math
from autotuto.calc import (Resultado, area_trapezio, area_triangulo, area_retangulo,
                           pitagoras, eq_primeiro_grau, regra_de_tres,
                           porcentagem, mdc, mmc, area_circulo, complemento,
                           suplemento,
                           comprimento_circunferencia, fracao_de, CATALOGO)

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
                             "pitagoras", "eq_primeiro_grau", "regra_de_tres",
                             "porcentagem", "mdc", "mmc", "area_circulo",
                             "comprimento_circunferencia", "fracao_de",
                             "complemento", "suplemento"}


def test_porcentagem():
    # 15% de desconto em 80: o desconto em si é 15% de 80 -> parte=12, todo=80
    r = porcentagem(12, 80)
    assert r.valor == 15.0
    assert "%" in r.passos[-1]


def test_mdc():
    assert mdc(24, 36).valor == 12


def test_mmc():
    r = mmc(4, 6)
    assert r.valor == 12
    assert "mdc" in r.passos[0] and "mmc" in r.passos[1]


def test_area_circulo():
    r = area_circulo(raio=3)
    assert abs(r.valor - math.pi * 9) < 1e-3
    assert r.unidade == "u²"
    assert r.passos[0] == r"A = \pi r^2"          # a fórmula antes do número


def test_comprimento_circunferencia():
    r = comprimento_circunferencia(raio=5)
    assert abs(r.valor - 2 * math.pi * 5) < 1e-3
    assert r.unidade == "u"


def test_fracao_de_exata_nao_vira_decimal():
    # 3/4 de 10 é 15/2. Numa aula de fração, mostrar "7.5" desmonta a ideia.
    r = fracao_de(3, 4, 10)
    assert r.valor == "15/2"
    assert r"\dfrac{15}{2}" in r.passos[-1]


def test_fracao_de_inteira_sai_inteira():
    assert fracao_de(3, 4, 12).valor == "9"


def test_fracao_de_denominador_zero_falha_rapido():
    import pytest
    with pytest.raises(ValueError):
        fracao_de(1, 0, 10)


def test_circulo_com_raio_negativo_falha_em_vez_de_mentir():
    # pi*(-3)^2 dá 28.27: área POSITIVA de um raio impossível. Sem o guard o
    # professor narraria um número errado com toda a confiança do mundo.
    import pytest
    for fn in (area_circulo, comprimento_circunferencia):
        with pytest.raises(ValueError):
            fn(raio=-3)
        with pytest.raises(ValueError):
            fn(raio=0)


# ───── complemento e suplemento (vieram de uma prova de 7º ano de verdade)

def test_complemento_e_suplemento_batem_com_a_prova():
    # os quatro itens exatos da Questão 2, com o gabarito conferido à mão
    esperado = {43: (47, 137), 67: (23, 113), 39: (51, 141)}
    for ang, (c, s) in esperado.items():
        assert complemento(ang).valor == c, ang
        assert suplemento(ang).valor == s, ang


def test_angulo_maior_que_90_nao_tem_complemento():
    # A PEGADINHA da questão. Responder 90-145 = -55 é inventar um ângulo que
    # não existe — e é o tipo de mentira que a regra única do projeto proíbe.
    r = complemento(145)
    assert r.valor == "não existe"
    assert "não existe complemento" in " ".join(r.passos)
    # mas o suplemento existe, porque 145 ainda é menor que 180
    assert suplemento(145).valor == 35


def test_o_caso_limite_de_90_e_180():
    assert complemento(90).valor == "não existe"     # 90 já fechou o canto
    assert complemento(89).valor == 1
    assert suplemento(180).valor == "não existe"
    assert suplemento(179).valor == 1


def test_nao_levanta_no_caso_impossivel():
    # se levantasse, o tocador diria "não tenho essa conta pronta" — mentira,
    # a gente TEM a conta, e a conta diz que não existe. É resposta, não erro.
    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [{"diz": "olha",
                         "calc": {"gerador": "complemento", "params": {"angulo": 145}}}]}
    assert avisos_graves(checar_matematica(plano)) == []
