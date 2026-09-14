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

# Círculo e fração: as figuras existem agora (catalogo.circulo / catalogo.fracao),
# e ferramenta de desenho sem ferramenta de conta é exatamente o que fez o LLM
# improvisar na autópsia. Entram juntas ou não entram.
def _raio_valido(nome, raio):
    if raio <= 0:
        raise ValueError(f"{nome}: raio tem que ser positivo (recebeu {raio!r})")

def area_circulo(raio) -> Resultado:
    # raio negativo dá área POSITIVA e ninguém percebe — falha em vez de mentir.
    _raio_valido("area_circulo", raio)
    v = math.pi * raio ** 2
    return Resultado(round(v, 4), [
        r"A = \pi r^2",
        rf"A = \pi \cdot {_n(raio)}^2 = \pi \cdot {_n(raio ** 2)}",
        rf"A \approx {v:.4g}"], "u²")

def comprimento_circunferencia(raio) -> Resultado:
    _raio_valido("comprimento_circunferencia", raio)
    v = 2 * math.pi * raio
    return Resultado(round(v, 4), [
        r"C = 2\pi r",
        rf"C = 2\pi \cdot {_n(raio)} \approx {v:.4g}"], "u")

def fracao_de(num, den, todo) -> Resultado:
    """`num`/`den` de `todo`. Devolve fração exata (3/4 de 10 = 15/2, não 7,5)."""
    if den == 0:
        raise ValueError("fracao_de: denominador não pode ser zero")
    v = (Fraction(num).limit_denominator() * Fraction(todo).limit_denominator()
         / Fraction(den).limit_denominator())
    txt = _n(v) if v.denominator == 1 else rf"\dfrac{{{v.numerator}}}{{{v.denominator}}}"
    return Resultado(_n(v) if v.denominator == 1 else f"{v.numerator}/{v.denominator}", [
        rf"\dfrac{{{_n(num)}}}{{{_n(den)}}} \text{{ de }} {_n(todo)}",
        rf"= \dfrac{{{_n(num)} \cdot {_n(todo)}}}{{{_n(den)}}} = {txt}"])

# Complemento e suplemento. Vieram de uma prova real de 7º ano: era a questão
# mais barata da folha e a que mais gente deixa em branco. O 145° do enunciado
# era pegadinha — ângulo de 90° ou mais NÃO TEM complemento, e responder
# "90 - 145 = -55" é inventar um ângulo que não existe. Aqui isso é RESPOSTA,
# não erro: levantar faria o tocador dizer "não tenho essa conta pronta", o que
# seria mentira — a gente tem a conta, e a conta diz que não existe.
def complemento(angulo) -> Resultado:
    """O que falta pra 90°."""
    if angulo >= 90:
        return Resultado("não existe", [
            rf"90^\circ - {_n(angulo)}^\circ < 0",
            r"\text{não existe complemento}"])
    v = 90 - angulo
    return Resultado(v, [
        r"C = 90^\circ - \text{ângulo}",
        rf"C = 90^\circ - {_n(angulo)}^\circ = {_n(v)}^\circ"], "°")

def suplemento(angulo) -> Resultado:
    """O que falta pra 180°."""
    if angulo >= 180:
        return Resultado("não existe", [
            rf"180^\circ - {_n(angulo)}^\circ < 0",
            r"\text{não existe suplemento}"])
    v = 180 - angulo
    return Resultado(v, [
        r"S = 180^\circ - \text{ângulo}",
        rf"S = 180^\circ - {_n(angulo)}^\circ = {_n(v)}^\circ"], "°")


CATALOGO = {"area_trapezio": area_trapezio, "area_triangulo": area_triangulo,
            "area_retangulo": area_retangulo, "pitagoras": pitagoras,
            "eq_primeiro_grau": eq_primeiro_grau, "regra_de_tres": regra_de_tres,
            "porcentagem": porcentagem, "mdc": mdc, "mmc": mmc,
            "area_circulo": area_circulo,
            "comprimento_circunferencia": comprimento_circunferencia,
            "fracao_de": fracao_de,
            "complemento": complemento, "suplemento": suplemento}
