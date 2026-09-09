"""Lousa — o renderizador do professor. Figuras paramétricas, rápidas (<0,3 s).

Não usa Manim (que renderiza pra vídeo, lento). Cada figura é uma função que
desenha num Axes matplotlib e devolve um PNG. O agente chama estas funções como
ferramentas enquanto explica.

Estilo: fundo de lousa (verde-escuro), traço branco/giz, um destaque âmbar.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ─────────────────────────────────────────────────────────── paleta "lousa"
FUNDO = "#0E2A22"       # verde-escuro de quadro
GIZ = "#EAEAEA"
GIZ_FRACO = "#8FA79C"
DESTAQUE = "#F2B134"     # âmbar — o "olha aqui"
AZUL = "#5AB1E0"
VERM = "#E0625E"

plt.rcParams.update({
    "figure.facecolor": FUNDO, "axes.facecolor": FUNDO,
    "text.color": GIZ, "axes.edgecolor": GIZ_FRACO,
    "xtick.color": GIZ_FRACO, "ytick.color": GIZ_FRACO,
    "font.family": "DejaVu Sans", "font.size": 15,
    "mathtext.fontset": "cm",
})


def _novo(w=6.4, h=6.4):
    fig, ax = plt.subplots(figsize=(w, h), dpi=140)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=FUNDO, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return buf.getvalue()


def _rotulo(ax, x, y, txt, cor=GIZ, tam=16, **kw):
    ax.text(x, y, txt, color=cor, fontsize=tam, ha="center", va="center",
            zorder=5, **kw)


# ═══════════════════════════════════════════════════════════ FIGURAS
def trapezio(B=6.0, b=3.5, h=4.0, *, destacar=None, fechar=0.0) -> bytes:
    """Trapézio isósceles. `destacar`: 'B'|'b'|'h'|'bases'. `fechar` 0..1 fecha
    num triângulo (b -> 0), pra mostrar 'triângulo é trapézio com base menor 0'."""
    b_ef = b * (1 - fechar)
    off = (B - b_ef) / 2
    xs = [0, B, B - off, off, 0]
    ys = [0, 0, h, h, 0]
    fig, ax = _novo()
    ax.plot(xs, ys, color=GIZ, lw=2.5)
    ax.fill(xs, ys, color=GIZ, alpha=0.06)

    def linha(x0, x1, y, cor, rot):
        ax.plot([x0, x1], [y, y], color=cor, lw=5, solid_capstyle="round", zorder=4)
        _rotulo(ax, (x0 + x1) / 2, y + (0.5 if y == 0 else -0.5) * np.sign(h - y or 1),
                rot, cor=cor, tam=17, fontweight="bold")

    if destacar in ("B", "bases"):
        linha(0, B, 0, DESTAQUE, "B")
    if destacar in ("b", "bases") and b_ef > 0.1:
        linha(off, B - off, h, AZUL, "b")
    if destacar == "h":
        ax.plot([B / 2, B / 2], [0, h], color=DESTAQUE, lw=3, ls=(0, (4, 3)), zorder=4)
        _rotulo(ax, B / 2 + 0.5, h / 2, "h", cor=DESTAQUE, tam=17, fontweight="bold")

    ax.set_xlim(-1.5, B + 1.5)
    ax.set_ylim(-1.5, h + 1.8)
    return _png(fig)


def trapezio_como_media(B=6.0, b=3.5, h=4.0) -> bytes:
    """Os dois retângulos (B·h e b·h) empilhados — a área do trapézio é a MÉDIA.
    É a resposta visual pro 'por que dividido por dois?'."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 5), dpi=140)
    for ax, base, cor, rot in ((a1, B, DESTAQUE, "B·h"), (a2, b, AZUL, "b·h")):
        ax.set_aspect("equal"); ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), base, h, fill=True, color=cor, alpha=0.18,
                                   ec=cor, lw=2.5))
        _rotulo(ax, base / 2, h / 2, rot, cor=cor, tam=20, fontweight="bold")
        ax.set_xlim(-1, max(B, b) + 1); ax.set_ylim(-1, h + 1)
    fig.suptitle("a área real fica no meio  →  (B·h + b·h) ÷ 2", color=GIZ, fontsize=17)
    return _png(fig)


def triangulo(base=6.0, altura=4.0, *, destacar=None) -> bytes:
    xs, ys = [0, base, base * 0.35, 0], [0, 0, altura, 0]
    fig, ax = _novo()
    ax.plot(xs, ys, color=GIZ, lw=2.5)
    ax.fill(xs, ys, color=GIZ, alpha=0.06)
    if destacar in ("base", "tudo"):
        ax.plot([0, base], [0, 0], color=DESTAQUE, lw=5, solid_capstyle="round")
        _rotulo(ax, base / 2, -0.6, "base", cor=DESTAQUE, tam=16, fontweight="bold")
    if destacar in ("altura", "tudo"):
        ax.plot([base * 0.35, base * 0.35], [0, altura], color=AZUL, lw=3, ls=(0, (4, 3)))
        _rotulo(ax, base * 0.35 + 0.5, altura / 2, "altura", cor=AZUL, tam=16, fontweight="bold")
    ax.set_xlim(-1.5, base + 1.5); ax.set_ylim(-1.5, altura + 1.5)
    return _png(fig)


def grafico(expr="x**2", x0=-4.0, x1=4.0, *, ponto=None) -> bytes:
    """Gráfico de y = f(x). `expr` em sintaxe Python (x**2, 2*x+1, sin(x))."""
    x = np.linspace(x0, x1, 400)
    env = {"x": x, "sin": np.sin, "cos": np.cos, "tan": np.tan, "sqrt": np.sqrt,
           "exp": np.exp, "log": np.log, "pi": np.pi, "abs": np.abs}
    try:
        y = eval(expr, {"__builtins__": {}}, env)  # noqa: S307 — expr controlada
    except Exception:
        y = x * 0
    fig, ax = plt.subplots(figsize=(6.8, 6.0), dpi=140)
    ax.axhline(0, color=GIZ_FRACO, lw=1); ax.axvline(0, color=GIZ_FRACO, lw=1)
    ax.plot(x, y, color=DESTAQUE, lw=3)
    if ponto is not None:
        px = float(ponto)
        py = float(eval(expr, {"__builtins__": {}}, {**env, "x": px}))
        ax.plot([px], [py], "o", color=VERM, ms=10)
        _rotulo(ax, px, py + (y.max() - y.min()) * 0.06, f"({px:g}, {py:g})", cor=VERM, tam=14)
    ax.set_title(f"y = {expr}", color=GIZ, fontsize=17)
    ax.grid(True, color=GIZ_FRACO, alpha=0.18)
    ax.tick_params(colors=GIZ_FRACO)
    for s in ax.spines.values():
        s.set_visible(False)
    return _png(fig)


def circulo(r=3.0, *, mostrar="raio") -> bytes:
    fig, ax = _novo()
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(r * np.cos(t), r * np.sin(t), color=GIZ, lw=2.5)
    if mostrar in ("raio", "tudo"):
        ax.plot([0, r], [0, 0], color=DESTAQUE, lw=4)
        _rotulo(ax, r / 2, 0.5, "r", cor=DESTAQUE, tam=17, fontweight="bold")
    if mostrar in ("diametro", "tudo"):
        ax.plot([-r, r], [0, 0], color=AZUL, lw=3, ls=(0, (4, 3)))
    ax.plot([0], [0], "o", color=GIZ, ms=5)
    ax.set_xlim(-r - 1, r + 1); ax.set_ylim(-r - 1, r + 1)
    return _png(fig)


def passo(latex: str, tam=30) -> bytes:
    """Uma linha de equação — o formato `conta`. `latex` sem os $ $."""
    fig, ax = _novo(8, 2.2)
    _rotulo(ax, 0.5, 0.5, f"${latex}$", tam=tam)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return _png(fig)


# catálogo pro agente (nome -> função)
CATALOGO = {
    "trapezio": trapezio,
    "trapezio_como_media": trapezio_como_media,
    "triangulo": triangulo,
    "grafico": grafico,
    "circulo": circulo,
    "passo": passo,
}
