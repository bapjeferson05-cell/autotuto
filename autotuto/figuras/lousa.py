"""Tema visual da lousa + render de uma linha LaTeX pra PNG.

Depende só de `config` + matplotlib/numpy + stdlib (regra de dependência de figuras/).
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")  # backend sem display, antes de importar pyplot

import matplotlib.pyplot as plt  # noqa: E402

from autotuto import config  # noqa: E402

# mathtext puro (sem TeX de sistema); serif combina com a lousa
matplotlib.rcParams["mathtext.fontset"] = "cm"
matplotlib.rcParams["font.family"] = "serif"

DPI = 130


def nova_figura(largura=6.0, altura=4.5):
    """(fig, ax) com o tema lousa: fundo escuro, eixos off, aspecto 1:1."""
    fig = plt.figure(figsize=(largura, altura), facecolor=config.COR_FUNDO)
    ax = fig.add_subplot(111)
    ax.set_facecolor(config.COR_FUNDO)
    ax.set_axis_off()
    ax.set_aspect("equal")
    return fig, ax


def para_png(fig) -> bytes:
    """Serializa a figura em PNG e fecha ela."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(),
                bbox_inches="tight", dpi=DPI)
    plt.close(fig)
    return buf.getvalue()


def passo_latex(latex: str) -> bytes:
    """PNG de uma linha de LaTeX (mathtext), giz sobre a lousa."""
    fig = plt.figure(figsize=(7.0, 1.6), facecolor=config.COR_FUNDO)
    ax = fig.add_subplot(111)
    ax.set_facecolor(config.COR_FUNDO)
    ax.set_axis_off()
    ax.text(0.5, 0.5, f"${latex}$", color=config.COR_GIZ, fontsize=28,
            ha="center", va="center", transform=ax.transAxes)
    return para_png(fig)
