"""Geradores nomeados de figuras usados pelas aulas.

Cada gerador monta um `spec` e chama `canvas.figura`. Todos têm defaults
sensatos, então `fn()` sem args já desenha algo.

`GERADORES` inclui a chave `"figura"` -> `canvas.figura` em si: as aulas de
ouro usam `{"gerador": "figura", "spec": {...}}` com specs inline. Os demais
geradores existem pras aulas geradas pelo planejador (LLM).

Depende só de `config` + matplotlib/numpy + stdlib (via canvas/lousa).
"""
from __future__ import annotations

from autotuto.figuras.canvas import figura


def trapezio(B=18, b=10, h=6, **_):
    dx = (B - b) / 2
    return figura({
        "pontos": {"A": [0, 0], "B": [B, 0], "C": [B - dx, h], "D": [dx, h]},
        "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
        "marcas": [{"tipo": "par", "de": "A", "para": "B"},
                   {"tipo": "par", "de": "D", "para": "C"}],
        "rotulos": [{"xy": [B / 2, -0.7], "texto": f"{B}"},
                    {"xy": [B / 2, h + 0.5], "texto": f"{b}"},
                    {"xy": [-0.9, h / 2], "texto": f"{h}"}],
    })


def triangulo(tipo="reto", base=8, altura=6, **_):
    if tipo == "reto":
        pts = {"A": [0, 0], "B": [base, 0], "C": [0, altura]}
        angs = [{"vertice": "A", "de": "B", "para": "C"}]
    elif tipo == "isosceles":
        pts = {"A": [0, 0], "B": [base, 0], "C": [base / 2, altura]}
        angs = []
    else:  # escaleno / qualquer
        pts = {"A": [0, 0], "B": [base, 0], "C": [base * 0.3, altura]}
        angs = []
    return figura({
        "pontos": pts,
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}],
        "angulos": angs,
        "rotulos": [{"xy": [base / 2, -0.7], "texto": f"{base}"},
                    {"xy": [-0.9, altura / 2], "texto": f"{altura}"}],
    })


def retangulo(base=12, altura=7, **_):
    return figura({
        "pontos": {"A": [0, 0], "B": [base, 0], "C": [base, altura], "D": [0, altura]},
        "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
        "angulos": [{"vertice": "A", "de": "B", "para": "D"}],
        "rotulos": [{"xy": [base / 2, -0.7], "texto": f"{base}"},
                    {"xy": [-0.9, altura / 2], "texto": f"{altura}"}],
    })


def dois_retangulos(B=18, b=10, h=6, **_):
    """O trapézio recortado como (retângulo b×h) + (triângulos = retângulo (B-b)×h /2).

    Usado no ramo 'por que divide por dois'.
    """
    gap = max(B, b) * 0.25 + 2
    x2 = B + gap
    return figura({
        "pontos": {
            "A": [0, 0], "B": [b, 0], "C": [b, h], "D": [0, h],
            "E": [x2, 0], "F": [x2 + (B - b), 0],
            "G": [x2 + (B - b), h], "H": [x2, h],
        },
        "poligonos": [
            {"vs": ["A", "B", "C", "D"], "preenche": True},
            {"vs": ["E", "F", "G", "H"], "preenche": True},
        ],
        "rotulos": [
            {"xy": [b / 2, h / 2], "texto": f"{b} x {h}"},
            {"xy": [x2 + (B - b) / 2, h / 2], "texto": f"({B}-{b}) x {h}"},
            {"xy": [(x2 + B) / 2 - gap / 2, h + 1], "texto": "+"},
        ],
    })


def balanca(esq="3x", dir="15", **_):
    """Balança de dois pratos em equilíbrio (equação do 1º grau)."""
    return figura({
        "pontos": {
            "P": [0, 0], "T": [0, 3],
            "L": [-4, 3], "R": [4, 3],
            "L1": [-5, 2.4], "L2": [-3, 2.4],
            "R1": [3, 2.4], "R2": [5, 2.4],
        },
        "segmentos": [["P", "T"], ["L", "R"],
                      ["L", "L1"], ["L", "L2"], ["R", "R1"], ["R", "R2"]],
        "poligonos": [{"vs": [[-1, 0], [1, 0], [0.4, 0], [-0.4, 0]], "preenche": True}],
        "rotulos": [{"xy": [-4, 1.9], "texto": str(esq)},
                    {"xy": [4, 1.9], "texto": str(dir)},
                    {"xy": [0, 3.5], "texto": "="}],
    })


def tabela_prop(a=3, b=24, c=5, x=40, **_):
    """Tabela 2x2 de proporção: a/b = c/x (regra de três)."""
    w, h = 6.0, 2.0
    cols = [0, w / 2, w]
    rows = [0, -h / 2, -h]
    segs = []
    for cx in cols:
        segs.append([[cx, rows[0]], [cx, rows[-1]]])
    for ry in rows:
        segs.append([[cols[0], ry], [cols[-1], ry]])
    cell = lambda ci, ri, txt: {"xy": [(cols[ci] + cols[ci + 1]) / 2,
                                       (rows[ri] + rows[ri + 1]) / 2], "texto": str(txt)}
    return figura({
        "segmentos": segs,
        "rotulos": [cell(0, 0, a), cell(1, 0, b),
                    cell(0, 1, c), cell(1, 1, x)],
    })


def reta_numerica(inicio=0, fim=10, marca=None, passo=1, **_):
    """Reta numérica de `inicio` a `fim` com ticks; destaca `marca` se dado."""
    if passo <= 0:
        raise ValueError(f"reta_numerica: passo tem que ser positivo (recebeu {passo!r})")
    segs = [[[inicio, 0], [fim, 0]]]
    rotulos = []
    n = inicio
    while n <= fim + 1e-9:
        segs.append([[n, -0.15], [n, 0.15]])
        rotulos.append({"xy": [n, -0.6], "texto": f"{int(n) if n == int(n) else n}"})
        n += passo
    marcas = []
    if marca is not None:
        marcas.append({"tipo": "cong", "de": [marca, 0], "para": [marca, 0.01]})
        rotulos.append({"xy": [marca, 0.7], "texto": str(marca)})
    return figura({"segmentos": segs, "marcas": marcas, "rotulos": rotulos})


GERADORES = {
    "figura": figura,
    "trapezio": trapezio,
    "triangulo": triangulo,
    "retangulo": retangulo,
    "dois_retangulos": dois_retangulos,
    "balanca": balanca,
    "tabela_prop": tabela_prop,
    "reta_numerica": reta_numerica,
}
