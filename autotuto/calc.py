from __future__ import annotations
import math
from dataclasses import dataclass
from fractions import Fraction

@dataclass
class Resultado:
    valor: float | str | tuple
    passos: list[str]
    unidade: str = ""

def _n(x) -> str:
    xf = float(x)
    return str(int(xf)) if xf == int(xf) else f"{xf:g}"

def area_trapezio(B, b, h) -> Resultado:
    v = (B + b) * h / 2
    return Resultado(v, [
        r"A = \dfrac{(B + b)\cdot h}{2}",
        rf"A = \dfrac{{({_n(B)} + {_n(b)})\cdot {_n(h)}}}{{2}}",
        rf"A = \dfrac{{{_n((B + b) * h)}}}{{2}} = {_n(v)}"], "u²")

def area_triangulo(base, altura) -> Resultado:
    v = base * altura / 2
    return Resultado(v, [r"A = \dfrac{b \cdot h}{2}",
                         rf"A = \dfrac{{{_n(base)} \cdot {_n(altura)}}}{{2}} = {_n(v)}"], "u²")

def area_retangulo(base, altura) -> Resultado:
    return Resultado(base * altura,
                     [rf"A = b \cdot h = {_n(base)} \cdot {_n(altura)} = {_n(base * altura)}"], "u²")

def pitagoras(a=None, b=None, c=None) -> Resultado:
    if c is None:
        c = math.hypot(a, b)
        return Resultado(round(c, 4), [
            r"c^2 = a^2 + b^2",
            rf"c^2 = {_n(a)}^2 + {_n(b)}^2 = {_n(a*a + b*b)}",
            rf"c = \sqrt{{{_n(a*a + b*b)}}} = {c:.4g}"])
    # F5: rotula a incógnita conforme o cateto que veio na chamada — antes
    # sempre escrevia "b^2 = c^2 - a^2" mesmo quando o conhecido era `b`.
    if a is not None:                        # a conhecido, resolve b
        con, incog, outro = a, "b", "a"
    else:                                    # b conhecido, resolve a
        con, incog, outro = b, "a", "b"
    cat = math.sqrt(c * c - con ** 2)
    return Resultado(round(cat, 4), [
        rf"{incog}^2 = c^2 - {outro}^2",
        rf"{incog}^2 = {_n(c)}^2 - {_n(con)}^2 = {_n(c*c - con*con)}",
        rf"{incog} = \sqrt{{{_n(c*c - con*con)}}} = {cat:.4g}"])

def eq_primeiro_grau(a, b) -> Resultado:
    x = Fraction(-b).limit_denominator() / Fraction(a).limit_denominator()
    termo = f"+ {_n(b)}" if b >= 0 else f"- {_n(-b)}"
    return Resultado(_n(x), [
        rf"{_n(a)}x {termo} = 0",
        rf"{_n(a)}x = {_n(-b)}",
        rf"x = \dfrac{{{_n(-b)}}}{{{_n(a)}}} = {_n(x)}"])

def regra_de_tres(a, b, c) -> Resultado:
    x = b * c / a
    return Resultado(round(x, 4), [
        rf"\dfrac{{{_n(a)}}}{{{_n(b)}}} = \dfrac{{{_n(c)}}}{{x}}",
        rf"x = \dfrac{{{_n(b)} \cdot {_n(c)}}}{{{_n(a)}}} = {x:g}"])

# autópsia de 2026-09-12: porcentagem e MDC apareceram de verdade num tópico
# nunca visto (o LLM não tinha ferramenta e improvisou com eq_primeiro_grau,
# errando os params). As 3 abaixo são as que os dados pediram — nenhuma outra.
def porcentagem(parte, todo) -> Resultado:
    """Que porcentagem `parte` é de `todo`."""
    pct = parte / todo * 100
    return Resultado(round(pct, 2), [
        r"\% = \dfrac{\text{parte}}{\text{todo}}\cdot 100",
        rf"\% = \dfrac{{{_n(parte)}}}{{{_n(todo)}}}\cdot 100 = {pct:.4g}\%"], "%")

def mdc(a, b) -> Resultado:
    g = math.gcd(int(a), int(b))
    return Resultado(g, [rf"\mathrm{{mdc}}({_n(a)}, {_n(b)}) = {g}"])

def mmc(a, b) -> Resultado:
    g = math.gcd(int(a), int(b))
    m = abs(int(a) * int(b)) // g
    return Resultado(m, [
        rf"\mathrm{{mdc}}({_n(a)}, {_n(b)}) = {g}",
        rf"\mathrm{{mmc}}({_n(a)}, {_n(b)}) = \dfrac{{{_n(a)} \cdot {_n(b)}}}{{{g}}} = {m}"])

CATALOGO = {"area_trapezio": area_trapezio, "area_triangulo": area_triangulo,
            "area_retangulo": area_retangulo, "pitagoras": pitagoras,
            "eq_primeiro_grau": eq_primeiro_grau, "regra_de_tres": regra_de_tres,
            "porcentagem": porcentagem, "mdc": mdc, "mmc": mmc}
