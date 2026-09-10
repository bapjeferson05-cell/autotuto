"""calc.py — motor de cálculos. Cada função devolve (resultado, passos em LaTeX).

Não é o LLM fazendo conta (o bench mostrou que 8B erra aritmética e data). É
Python fazendo, e devolvendo os PASSOS pra o professor mostrar na lousa.

    r = area_trapezio(B=18, b=10, h=6)
    r.valor      -> 84.0
    r.unidade    -> "u²"
    r.passos     -> ["A = \\frac{(B+b)\\,h}{2}",
                     "A = \\frac{(18+10)\\cdot 6}{2}",
                     "A = \\frac{168}{2} = 84"]
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction


@dataclass
class Resultado:
    valor: float | str
    passos: list[str]
    unidade: str = ""

    def como_beats(self) -> list[dict]:
        return [{"lousa": {"fn": "figura",
                           "pontos": {}, "rotulos": [{"xy": [0, 0], "texto": p, "tam": 26}]}}
                if False else {"lousa": {"fn": "passo_latex", "latex": p}}
                for p in self.passos]


def _n(x):
    """18.0 -> '18',  3.5 -> '3.5',  Fraction -> '\\frac{}{}'."""
    if isinstance(x, Fraction):
        return f"\\tfrac{{{x.numerator}}}{{{x.denominator}}}" if x.denominator != 1 else str(x.numerator)
    xf = float(x)
    return str(int(xf)) if xf == int(xf) else f"{xf:g}"


# ─────────────────────────────────────────────────────────── ÁREAS
def area_trapezio(B, b, h) -> Resultado:
    v = (B + b) * h / 2
    return Resultado(v, [
        r"A = \dfrac{(B + b)\cdot h}{2}",
        rf"A = \dfrac{{({_n(B)} + {_n(b)})\cdot {_n(h)}}}{{2}}",
        rf"A = \dfrac{{{_n((B + b) * h)}}}{{2}} = {_n(v)}",
    ], "u²")


def area_triangulo(base, altura) -> Resultado:
    v = base * altura / 2
    return Resultado(v, [
        r"A = \dfrac{b \cdot h}{2}",
        rf"A = \dfrac{{{_n(base)} \cdot {_n(altura)}}}{{2}} = {_n(v)}",
    ], "u²")


def area_circulo(r) -> Resultado:
    v = math.pi * r * r
    return Resultado(round(v, 2), [
        r"A = \pi r^2",
        rf"A = \pi \cdot {_n(r)}^2 = {_n(r * r)}\pi \approx {v:.2f}",
    ], "u²")


def comprimento_circunferencia(r=None, d=None) -> Resultado:
    """A volta do círculo. Passe o raio OU o diâmetro."""
    raio = r if r is not None else d / 2
    v = 2 * math.pi * raio
    return Resultado(round(v, 2), [
        r"C = 2\pi r",
        rf"C = 2\pi \cdot {_n(raio)} = {_n(2 * raio)}\pi \approx {v:.2f}",
    ])


def perimetro_poligono_regular(n, lado) -> Resultado:
    v = n * lado
    return Resultado(v, [
        r"P = n \cdot \ell",
        rf"P = {_n(n)} \cdot {_n(lado)} = {_n(v)}",
    ])


def area_retangulo(base, altura) -> Resultado:
    return Resultado(base * altura, [rf"A = b \cdot h = {_n(base)} \cdot {_n(altura)} = {_n(base * altura)}"], "u²")


# ─────────────────────────────────────────────────────── PITÁGORAS
def pitagoras(a=None, b=None, c=None) -> Resultado:
    """Passe 2 dos 3. c = hipotenusa."""
    if c is None:
        c = math.hypot(a, b)
        return Resultado(round(c, 4), [
            r"c^2 = a^2 + b^2",
            rf"c^2 = {_n(a)}^2 + {_n(b)}^2 = {_n(a*a + b*b)}",
            rf"c = \sqrt{{{_n(a*a + b*b)}}} = {c:.4g}",
        ])
    conhecido, incog = (a, "b") if a is not None else (b, "a")
    cat = math.sqrt(c * c - conhecido ** 2)
    outro = "b" if incog == "a" else "a"
    return Resultado(round(cat, 4), [
        rf"{incog}^2 = c^2 - {outro}^2",
        rf"{incog}^2 = {_n(c)}^2 - {_n(conhecido)}^2 = {_n(c * c - conhecido * conhecido)}",
        rf"{incog} = \sqrt{{{_n(c * c - conhecido * conhecido)}}} = {cat:.4g}",
    ])


# ────────────────────────────────────────────────────── EQUAÇÕES
def eq_primeiro_grau(a, b) -> Resultado:
    """a x + b = 0."""
    if a == 0:
        return Resultado("sem solução" if b else "infinitas", [r"a = 0"])
    x = Fraction(-b).limit_denominator() / Fraction(a).limit_denominator()
    termo_b = f"+ {_n(b)}" if b >= 0 else f"- {_n(-b)}"     # "3x - 15", não "3x + -15"
    return Resultado(_n(x), [
        rf"{_n(a)}x {termo_b} = 0",
        rf"{_n(a)}x = {_n(-b)}",
        rf"x = \dfrac{{{_n(-b)}}}{{{_n(a)}}} = {_n(x)}",
    ])


def bhaskara(a, b, c) -> Resultado:
    d = b * b - 4 * a * c
    passos = [r"x = \dfrac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
              rf"\Delta = {_n(b)}^2 - 4\cdot{_n(a)}\cdot{_n(c)} = {_n(d)}"]
    if d < 0:
        return Resultado("sem raízes reais", passos + [r"\Delta < 0"])
    r = math.sqrt(d)
    x1, x2 = (-b + r) / (2 * a), (-b - r) / (2 * a)
    passos.append(rf"x = \dfrac{{{_n(-b)} \pm {r:g}}}{{{_n(2*a)}}}")
    passos.append(rf"x_1 = {x1:g} \qquad x_2 = {x2:g}")
    return Resultado((round(x1, 4), round(x2, 4)), passos)


# ─────────────────────────────────────────────── PROPORÇÃO / %
def porcentagem(parte=None, todo=None, pct=None) -> Resultado:
    if pct is None:
        p = parte / todo * 100
        return Resultado(round(p, 2), [
            rf"\% = \dfrac{{{_n(parte)}}}{{{_n(todo)}}}\cdot 100 = {p:g}\%"])
    v = todo * pct / 100
    return Resultado(round(v, 4), [
        rf"{_n(pct)}\% \text{{ de }} {_n(todo)} = \dfrac{{{_n(pct)}}}{{100}}\cdot {_n(todo)} = {v:g}"])


def regra_de_tres(a, b, c) -> Resultado:
    """a está para b assim como c está para x."""
    x = b * c / a
    return Resultado(round(x, 4), [
        rf"\dfrac{{{_n(a)}}}{{{_n(b)}}} = \dfrac{{{_n(c)}}}{{x}}",
        rf"x = \dfrac{{{_n(b)} \cdot {_n(c)}}}{{{_n(a)}}} = {x:g}",
    ])


# ──────────────────────────────────────────────── MMC / MDC
def mdc(a, b) -> Resultado:
    g = math.gcd(int(a), int(b))
    return Resultado(g, [rf"\mathrm{{mdc}}({_n(a)},\,{_n(b)}) = {g}"])


def mmc(a, b) -> Resultado:
    m = abs(int(a) * int(b)) // math.gcd(int(a), int(b))
    return Resultado(m, [rf"\mathrm{{mmc}}({_n(a)},\,{_n(b)}) = \dfrac{{{_n(a)}\cdot{_n(b)}}}{{\mathrm{{mdc}}}} = {m}"])


# ──────────────────────────────────────────────── cálculos simples do dia a dia
def media(valores) -> Resultado:
    vs = [float(v) for v in valores]
    s, n = sum(vs), len(vs)
    return Resultado(round(s / n, 4), [
        r"\bar{x} = \dfrac{\text{soma}}{\text{quantidade}}",
        rf"\bar{{x}} = \dfrac{{{' + '.join(_n(v) for v in vs)}}}{{{n}}} = \dfrac{{{_n(s)}}}{{{n}}} = {_n(s / n)}",
    ])


def velocidade_media(distancia, tempo) -> Resultado:
    v = distancia / tempo
    return Resultado(round(v, 4), [
        r"v = \dfrac{\text{distância}}{\text{tempo}}",
        rf"v = \dfrac{{{_n(distancia)}}}{{{_n(tempo)}}} = {_n(v)}",
    ], "u/t")


def juros_simples(capital, taxa, tempo) -> Resultado:
    """taxa em % ao período."""
    j = capital * (taxa / 100) * tempo
    return Resultado(round(j, 2), [
        r"J = C \cdot i \cdot t",
        rf"J = {_n(capital)} \cdot \dfrac{{{_n(taxa)}}}{{100}} \cdot {_n(tempo)} = {_n(j)}",
        rf"\text{{montante}} = {_n(capital)} + {_n(j)} = {_n(capital + j)}",
    ])


CATALOGO = {
    "area_trapezio": area_trapezio, "area_triangulo": area_triangulo,
    "area_circulo": area_circulo, "area_retangulo": area_retangulo,
    "pitagoras": pitagoras, "eq_primeiro_grau": eq_primeiro_grau,
    "bhaskara": bhaskara, "porcentagem": porcentagem, "regra_de_tres": regra_de_tres,
    "mdc": mdc, "mmc": mmc,
    "media": media, "velocidade_media": velocidade_media, "juros_simples": juros_simples,
    "comprimento_circunferencia": comprimento_circunferencia,
    "perimetro_poligono_regular": perimetro_poligono_regular,
}
