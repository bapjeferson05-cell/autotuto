"""formas.py — geradores de formas 2D em cima de primitivas.figura() (e matplotlib
direto pras curvas paramétricas).

A lista de ~65 figuras planas colapsa em ~7 tipos: "pentágono ... megágono" é UMA
função `poligono_regular(n)`; "pentagrama ... decagrama" é `estrela(n, k)`;
"elipse ... espiral" é `curva(nome)`; "setor ... coroa" é `parte_circulo(nome)`.
"""
from __future__ import annotations

import math
from math import gcd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from professor.figuras.primitivas import CORES, FUNDO, GIZ, GIZ_FRACO, _png, figura


def _ax(w=5.6, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=140)
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _legenda(ax, r, txt):
    ax.text(0, -r - 1.15, txt, color=GIZ_FRACO, ha="center", va="top", fontsize=13)


# ───────────────────────────────────────────────────────────── TRIÂNGULOS
_TRI = {
    "equilatero":  {"A": [0, 0], "B": [4, 0], "C": [2, 3.4641]},
    "isosceles":   {"A": [0, 0], "B": [4, 0], "C": [2, 4.2]},
    "escaleno":    {"A": [0, 0], "B": [5.2, 0], "C": [1.1, 3.0]},
    "retangulo":   {"A": [0, 0], "B": [4.4, 0], "C": [0, 3.2]},
    "acutangulo":  {"A": [0, 0], "B": [4.2, 0], "C": [2.7, 3.1]},
    "obtusangulo": {"A": [0, 0], "B": [5.4, 0], "C": [-1.4, 2.1]},
}


def triangulo(tipo="escaleno") -> bytes:
    P = _TRI[tipo]
    spec = {"pontos": P, "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}]}
    if tipo == "retangulo":
        spec["angulos"] = [{"em": "A", "de": "B", "para": "C", "reto": True}]
    elif tipo == "equilatero":
        spec["marcas"] = [{"tipo": "cong", "de": a, "para": b, "n": 1}
                          for a, b in (("A", "B"), ("B", "C"), ("C", "A"))]
        spec["angulos"] = [{"em": v, "de": d, "para": p, "rotulo": r"60^\circ", "raio": 0.7}
                           for v, d, p in (("A", "B", "C"), ("B", "A", "C"), ("C", "A", "B"))]
    elif tipo == "isosceles":
        spec["marcas"] = [{"tipo": "cong", "de": "A", "para": "C", "n": 1},
                          {"tipo": "cong", "de": "B", "para": "C", "n": 1}]
    elif tipo == "obtusangulo":
        spec["angulos"] = [{"em": "A", "de": "B", "para": "C", "n": 1}]
    return figura(spec)


# ──────────────────────────────────────────────────────── QUADRILÁTEROS
def _quad_pts(tipo):
    return {
        "quadrado":           {"A": [0, 0], "B": [4, 0], "C": [4, 4], "D": [0, 4]},
        "retangulo":          {"A": [0, 0], "B": [6, 0], "C": [6, 3.6], "D": [0, 3.6]},
        "losango":            {"A": [0, -3], "B": [2.3, 0], "C": [0, 3], "D": [-2.3, 0]},
        "paralelogramo":      {"A": [0, 0], "B": [5, 0], "C": [6.6, 3.4], "D": [1.6, 3.4]},
        "trapezio_isosceles": {"A": [0, 0], "B": [7, 0], "C": [5, 4], "D": [2, 4]},
        "trapezio_retangulo": {"A": [0, 0], "B": [6, 0], "C": [3.6, 4], "D": [0, 4]},
        "trapezio_escaleno":  {"A": [0, 0], "B": [7, 0], "C": [4.6, 3.4], "D": [1.2, 3.4]},
        "deltoide":           {"A": [0, 4], "B": [2.6, 1], "C": [0, -3.2], "D": [-2.6, 1]},
    }[tipo]


def quadrilatero(tipo="paralelogramo") -> bytes:
    P = _quad_pts(tipo)
    spec = {"pontos": P, "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}]}
    lados = (("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"))
    if tipo in ("quadrado", "retangulo"):
        spec["angulos"] = [{"em": "A", "de": "B", "para": "D", "reto": True},
                           {"em": "C", "de": "B", "para": "D", "reto": True}]
    elif tipo == "trapezio_retangulo":
        spec["angulos"] = [{"em": "A", "de": "B", "para": "D", "reto": True},
                           {"em": "D", "de": "A", "para": "C", "reto": True}]
    if tipo in ("quadrado", "losango"):
        spec["marcas"] = [{"tipo": "cong", "de": a, "para": b, "n": 1} for a, b in lados]
    elif tipo in ("paralelogramo", "retangulo"):
        spec["marcas"] = [{"tipo": "par", "de": "A", "para": "B", "n": 1},
                          {"tipo": "par", "de": "D", "para": "C", "n": 1},
                          {"tipo": "par", "de": "A", "para": "D", "n": 2},
                          {"tipo": "par", "de": "B", "para": "C", "n": 2}]
    elif tipo == "trapezio_isosceles":
        spec["marcas"] = [{"tipo": "cong", "de": "A", "para": "D", "n": 1},
                          {"tipo": "cong", "de": "B", "para": "C", "n": 1},
                          {"tipo": "par", "de": "A", "para": "B", "n": 1},
                          {"tipo": "par", "de": "D", "para": "C", "n": 1}]
    elif tipo in ("trapezio_retangulo", "trapezio_escaleno"):
        spec["marcas"] = [{"tipo": "par", "de": "A", "para": "B", "n": 1},
                          {"tipo": "par", "de": "D", "para": "C", "n": 1}]
    elif tipo == "deltoide":
        spec["marcas"] = [{"tipo": "cong", "de": "A", "para": "B", "n": 1},
                          {"tipo": "cong", "de": "A", "para": "D", "n": 1},
                          {"tipo": "cong", "de": "C", "para": "B", "n": 2},
                          {"tipo": "cong", "de": "C", "para": "D", "n": 2}]
    return figura(spec)


# ─────────────────────────────────────── POLÍGONO REGULAR (5 … 1 000 000 lados)
def poligono_regular(n=6, *, r=4.0, rotulo=True) -> bytes:
    n = max(3, int(n))
    m = min(n, 4000)                       # acima de ~4000 lados é sub-pixel
    a = np.pi / 2 + np.linspace(0, 2 * np.pi, m, endpoint=False)
    pts = {f"P{i}": [r * math.cos(t), r * math.sin(t)] for i, t in enumerate(a)}
    spec = {
        "pontos": pts,
        "mostrar_pontos": n <= 16,
        "nomear_pontos": False,
        "poligonos": [{"vs": list(pts), "preenche": True, "lw": 2.4 if n < 40 else 1.4}],
    }
    if rotulo:
        etq = r"\text{n = %s}" % f"{n:,}".replace(",", ".")
        if n >= 60:
            etq += r"\;\approx\;\text{círculo}"
        spec["rotulos"] = [{"xy": [0, -r - 1.15], "texto": etq, "tam": 14}]
    return figura(spec, w=5.6, h=6.0)


# ───────────────────────────────────────── ESTRELA / POLÍGONO ESTRELADO {n/k}
def estrela(n=5, k=2, *, r=4.0) -> bytes:
    fig, ax = _ax()
    a0 = math.pi / 2
    g = gcd(n, k)
    if g == 1:
        comps = [[(i * k) % n for i in range(n)] + [0]]
    else:                                  # composto (ex.: hexagrama {6/2} = 2 triângulos)
        comps = [[(s + i * g) % n for i in range(n // g)] + [s] for s in range(g)]
    for comp in comps:
        pts = [(r * math.cos(a0 + 2 * math.pi * i / n),
                r * math.sin(a0 + 2 * math.pi * i / n)) for i in comp]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        ax.fill(xs, ys, color=GIZ, alpha=0.05, zorder=1)
        ax.plot(xs, ys, color=GIZ, lw=2.6, zorder=3, solid_joinstyle="round")
    _legenda(ax, r, f"{{{n}/{k}}}")
    ax.set_xlim(-r - 1.3, r + 1.3)
    ax.set_ylim(-r - 1.7, r + 1.3)
    return _png(fig)


# ───────────────────────────────────────── CURVAS (equação paramétrica)
def curva(nome="elipse") -> bytes:
    fig, ax = _ax(6.2, 5.8)
    ax.axhline(0, color=GIZ_FRACO, lw=0.8, zorder=1)
    ax.axvline(0, color=GIZ_FRACO, lw=0.8, zorder=1)
    C = CORES["destaque"]
    t = np.linspace(0, 2 * np.pi, 1200)

    if nome == "elipse":
        A, B = 4.2, 2.6
        ax.plot(A * np.cos(t), B * np.sin(t), color=C, lw=2.8)
        f = math.sqrt(A * A - B * B)
        ax.plot([f, -f], [0, 0], "o", color=CORES["verm"], ms=7)
        lim = A + 1
    elif nome == "parabola":
        x = np.linspace(-3.2, 3.2, 400)
        ax.plot(x, 0.55 * x * x - 2, color=C, lw=2.8)
        ax.plot([0], [-2], "o", color=CORES["verm"], ms=7)
        lim = 5
    elif nome == "hiperbole":
        x = np.linspace(1.15, 4.6, 300)
        y = 1.7 * np.sqrt(x * x - 1)
        for sx in (1, -1):
            for sy in (1, -1):
                ax.plot(sx * x, sy * y, color=C, lw=2.8)
        for s in (1, -1):
            ax.plot([-6, 6], [s * 1.7 * 6, -s * 1.7 * 6], color=GIZ_FRACO, lw=1, ls=(0, (4, 4)))
        lim = 6
    elif nome == "cardioide":
        rr = 2.2 * (1 - np.cos(t))
        ax.plot(rr * np.cos(t), rr * np.sin(t), color=C, lw=2.8)
        lim = 5
    elif nome == "lemniscata":
        tt = np.linspace(-np.pi / 4 + 1e-3, np.pi / 4 - 1e-3, 500)
        rr = 4.0 * np.sqrt(np.cos(2 * tt))
        for s in (1, -1):
            ax.plot(s * rr * np.cos(tt), s * rr * np.sin(tt), color=C, lw=2.8)
        lim = 5
    elif nome == "espiral":
        th = np.linspace(0, 6.5 * np.pi, 1400)
        ax.plot(0.24 * th * np.cos(th), 0.24 * th * np.sin(th), color=C, lw=2.4)
        lim = 6
    elif nome == "cassini":
        c, aa = 2.0, 2.55                  # aa > c  → um único óvalo
        disc = c**4 * np.cos(2 * t) ** 2 - c**4 + aa**4
        r2 = c**2 * np.cos(2 * t) + np.sqrt(np.maximum(disc, 0))
        rr = np.sqrt(np.maximum(r2, 0))
        ax.plot(rr * np.cos(t), rr * np.sin(t), color=C, lw=2.8)
        lim = 4
    else:
        raise ValueError(nome)

    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.text(0, -lim, nome, color=GIZ_FRACO, ha="center", va="bottom", fontsize=13)
    return _png(fig)


# ───────────────────────────────────────── PARTES DO CÍRCULO
def parte_circulo(nome="setor", *, r=4.0, ang=75.0) -> bytes:
    fig, ax = _ax()
    t = np.linspace(0, 2 * np.pi, 400)
    a = math.radians(ang)
    C = CORES["destaque"]

    if nome == "circulo":
        ax.fill(r * np.cos(t), r * np.sin(t), color=C, alpha=0.16)
        ax.plot(r * np.cos(t), r * np.sin(t), color=GIZ, lw=2.6)
        ax.plot([0], [0], "o", color=GIZ, ms=4)
    elif nome == "circunferencia":
        ax.plot(r * np.cos(t), r * np.sin(t), color=GIZ, lw=2.6)
    elif nome == "semicirculo":
        tt = np.linspace(0, np.pi, 200)
        ax.fill(np.r_[r * np.cos(tt), -r], np.r_[r * np.sin(tt), 0], color=C, alpha=0.18)
        ax.plot(r * np.cos(tt), r * np.sin(tt), color=GIZ, lw=2.6)
        ax.plot([-r, r], [0, 0], color=GIZ, lw=2.6)
    elif nome == "setor":
        tt = np.linspace(0, a, 160)
        ax.plot(r * np.cos(t), r * np.sin(t), color=GIZ_FRACO, lw=1.3, ls=(0, (3, 3)))
        ax.fill(np.r_[0, r * np.cos(tt), 0], np.r_[0, r * np.sin(tt), 0], color=C, alpha=0.22)
        ax.plot(np.r_[0, r * np.cos(tt), 0], np.r_[0, r * np.sin(tt), 0], color=GIZ, lw=2.6)
    elif nome == "segmento":
        tt = np.linspace(-a, a, 160)
        ax.plot(r * np.cos(t), r * np.sin(t), color=GIZ, lw=2.6)
        ax.fill(r * np.cos(tt), r * np.sin(tt), color=C, alpha=0.22)
        ax.plot([r * math.cos(a), r * math.cos(-a)], [r * math.sin(a), r * math.sin(-a)],
                color=GIZ, lw=2.6)
    elif nome == "coroa":
        ri = r * 0.55
        ax.fill(np.r_[r * np.cos(t), ri * np.cos(t[::-1])],
                np.r_[r * np.sin(t), ri * np.sin(t[::-1])], color=C, alpha=0.20)
        ax.plot(r * np.cos(t), r * np.sin(t), color=GIZ, lw=2.6)
        ax.plot(ri * np.cos(t), ri * np.sin(t), color=GIZ, lw=2.6)
    else:
        raise ValueError(nome)

    _legenda(ax, r, nome)
    ax.set_xlim(-r - 1.2, r + 1.2)
    ax.set_ylim(-r - 1.7, r + 1.2)
    return _png(fig)


CATALOGO_2D = {
    "triangulo": triangulo, "quadrilatero": quadrilatero,
    "poligono_regular": poligono_regular, "estrela": estrela,
    "curva": curva, "parte_circulo": parte_circulo,
}
