"""LaTeX do projeto → fala em português. O passo na lousa não pode ficar mudo,
e a leitura automática nunca pode inventar o que não entendeu."""
import re

import pytest

from autotuto import calc
from autotuto.fala_formula import fala


def test_le_as_construcoes_que_o_projeto_gera():
    casos = [
        # numerador composto ganha ", tudo isso sobre": sem isso, "3 vezes 10
        # sobre 4" no ouvido é (3x10)/4 ou 3x(10/4) — o aluno não tem como saber
        (r"A = \dfrac{(B + b)\cdot h}{2}",
         "A é igual a abre parênteses B mais b fecha parênteses vezes h, "
         "tudo isso sobre 2"),
        (r"c^2 = a^2 + b^2",
         "c ao quadrado é igual a a ao quadrado mais b ao quadrado"),
        (r"c = \sqrt{25} = 5", "c é igual a raiz quadrada de 25 é igual a 5"),
        (r"A = \pi r^2", "A é igual a pi r ao quadrado"),
        (r"A \approx 28.27", "A é aproximadamente 28,27"),
        (r"\mathrm{mdc}(24, 36) = 12",
         "o máximo divisor comum de 24 e 36 é igual a 12"),
    ]
    for latex, esperado in casos:
        assert fala(latex) == esperado, latex


def test_porcentagem_abrindo_a_formula_e_o_nome_da_grandeza():
    # "por cento é igual a parte sobre todo" não é português de professor
    assert fala(r"\% = \dfrac{\text{parte}}{\text{todo}}\cdot 100").startswith(
        "a porcentagem é igual a")
    # mas como UNIDADE, no fim, continua sendo "por cento"
    assert fala(r"= 15\%").endswith("15 por cento")


def test_cobre_todo_passo_que_o_calc_produz():
    # se um gerador de calc novo escrever LaTeX que isto não lê, o passo dele
    # volta a ficar mudo na lousa — este teste é o alarme.
    resultados = [
        calc.area_trapezio(18, 10, 6), calc.area_triangulo(8, 6),
        calc.area_retangulo(12, 7), calc.pitagoras(a=3, b=4),
        calc.pitagoras(a=3, c=5), calc.pitagoras(b=4, c=5),
        calc.eq_primeiro_grau(2, -8), calc.eq_primeiro_grau(3, 1),
        calc.regra_de_tres(3, 24, 5), calc.porcentagem(12, 80),
        calc.mdc(24, 36), calc.mmc(4, 6), calc.area_circulo(3),
        calc.comprimento_circunferencia(5), calc.fracao_de(3, 4, 12),
        calc.fracao_de(3, 4, 10),
    ]
    mudos = [p for r in resultados for p in r.passos if fala(p) is None]
    assert mudos == [], mudos


def test_na_duvida_cala_em_vez_de_inventar():
    # a regra do projeto vale aqui: narrar fórmula errada com voz de professor
    # é pior que não narrar.
    for latex in (r"\int_0^1 x\,dx", r"\sum_{i=1}^{n} i", r"\alpha \beta",
                  r"\dfrac{1}{", r"\comandoInventado{x}", r"x \oplus y"):
        assert fala(latex) is None, latex


def test_nao_devolve_frase_com_barra_ou_chave_sobrando():
    for r in (calc.area_trapezio(18, 10, 6), calc.fracao_de(3, 4, 10)):
        for p in r.passos:
            t = fala(p)
            assert "\\" not in t and "{" not in t and "}" not in t, (p, t)


def test_nao_importa_nada_do_projeto():
    # é folha na árvore de dependências: nem `config` ele importa
    import pathlib
    fonte = pathlib.Path("autotuto/fala_formula.py").read_text()
    assert not re.search(r"^\s*(from|import)\s+autotuto", fonte, re.M)


# ───── ambiguidade de fração no ouvido (achada revisando o próprio diff)

def test_numerador_composto_nao_sai_ambiguo():
    # "3 vezes 10 sobre 4" pode ser (3x10)/4 ou 3x(10/4). Na lousa a barra
    # resolve; no ouvido, não. Professor fala "tudo isso sobre".
    assert fala(r"\dfrac{3 \cdot 10}{4}") == "3 vezes 10, tudo isso sobre 4"
    assert fala(r"\dfrac{a + b}{2}") == "a mais b, tudo isso sobre 2"


def test_numerador_simples_continua_curto():
    # o "tudo isso" só entra quando há ambiguidade — senão vira encheção
    assert fala(r"\dfrac{168}{2}") == "168 sobre 2"
    assert fala(r"\dfrac{15}{2}") == "15 sobre 2"


def test_fracao_seguida_de_multiplicacao_ganha_pausa():
    # o outro lado: "12 sobre 80 vezes 100" é (12/80)x100 ou 12/(80x100)?
    assert fala(r"\dfrac{12}{80}\cdot 100") == "12 sobre 80, vezes 100"
    # mas `+` e `-` são lidos soltos e não confundem — nada de vírgula à toa
    assert fala(r"\dfrac{12}{80} + 3") == "12 sobre 80 mais 3"


def test_parser_aguenta_entrada_torta_sem_estourar():
    # `fala` roda sobre LaTeX que veio do calc, mas um gerador novo pode
    # escrever qualquer coisa. Travar a aula por causa da NARRAÇÃO seria
    # trocar um problema pequeno por um grande.
    for ruim in ("", " ", "\\", "{", "}", "^", "^{", r"\dfrac{1}", r"\sqrt",
                 "a" * 3000, r"\dfrac{" * 150 + "1" + "}" * 150, "=" * 500,
                 r"\mathrm{", "😀", "\x00", r"\cdot" * 300):
        fala(ruim)          # não pode levantar; None é resposta legítima
