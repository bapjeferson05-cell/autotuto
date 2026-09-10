"""Compositor procedural: `figura(spec)` -> PNG bytes.

`spec` (todas as chaves opcionais):
  pontos     {nome: [x, y]}
  segmentos  [[a, b], ...]            a/b = nome de ponto ou [x, y] cru
  poligonos  [{"vs": [nomes/coords], "preenche": bool}]
  angulos    [{"vertice", "de", "para"}]   arco (ou quadradinho se ~90°)
  marcas     [{"tipo": "cong"|"par", "de", "para"}]   ticks de congruência/paralelismo
  rotulos    [{"xy": [x, y], "texto": str}]

Depende só de `config` + matplotlib/numpy + stdlib.
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Arc

from autotuto import config
from autotuto.figuras.lousa import nova_figura, para_png


def _resolver(spec, n):
    """nome -> coord via spec['pontos']; lista de coords passa direto."""
    if isinstance(n, str):
        return np.asarray(spec["pontos"][n], dtype=float)
    return np.asarray(n, dtype=float)


def _desenha_poligono(ax, spec, pol):
    pts = [_resolver(spec, v) for v in pol.get("vs", [])]
    if len(pts) < 2:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    preenche = pol.get("preenche", False)
    ax.fill(xs, ys, color=config.COR_AZUL, alpha=0.12 if preenche else 0.0,
            edgecolor=config.COR_GIZ, lw=2, zorder=2)


def _desenha_segmento(ax, spec, seg):
    a, b = _resolver(spec, seg[0]), _resolver(spec, seg[1])
    ax.plot([a[0], b[0]], [a[1], b[1]], color=config.COR_GIZ, lw=2, zorder=3)


def _desenha_angulo(ax, spec, ang):
    v = _resolver(spec, ang["vertice"])
    a = _resolver(spec, ang["de"])
    c = _resolver(spec, ang["para"])
    va, vc = a - v, c - v
    ang_a = np.degrees(np.arctan2(va[1], va[0]))
    ang_c = np.degrees(np.arctan2(vc[1], vc[0]))
    dif = abs((ang_c - ang_a + 180) % 360 - 180)
    r = 0.6
    if abs(dif - 90) < 1.5:  # quadradinho de ângulo reto
        ua = va / (np.linalg.norm(va) or 1.0)
        uc = vc / (np.linalg.norm(vc) or 1.0)
        s = r * 0.7
        p0 = v + ua * s
        p1 = v + ua * s + uc * s
        p2 = v + uc * s
        ax.plot([p0[0], p1[0], p2[0]], [p0[1], p1[1], p2[1]],
                color=config.COR_GIZ, lw=1.5, zorder=4)
    else:
        arco = Arc((v[0], v[1]), 2 * r, 2 * r, angle=0.0,
                   theta1=min(ang_a, ang_c), theta2=max(ang_a, ang_c),
                   color=config.COR_DESTAQUE, lw=2, zorder=4)
        ax.add_patch(arco)


def _desenha_marca(ax, spec, marca):
    a, b = _resolver(spec, marca["de"]), _resolver(spec, marca["para"])
    mid = (a + b) / 2
    d = b - a
    n = np.linalg.norm(d) or 1.0
    u = d / n                       # ao longo do segmento
    perp = np.array([-u[1], u[0]])  # normal
    tipo = marca.get("tipo", "cong")
    if tipo == "par":  # setinha de paralelismo (V apontando ao longo)
        for s in (-0.10, 0.10):
            base = mid + u * s
            ax.plot([base[0] - u[0] * 0.12 + perp[0] * 0.12, base[0],
                     base[0] - u[0] * 0.12 - perp[0] * 0.12],
                    [base[1] - u[1] * 0.12 + perp[1] * 0.12, base[1],
                     base[1] - u[1] * 0.12 - perp[1] * 0.12],
                    color=config.COR_VERDE, lw=1.5, zorder=4)
    else:  # tick de congruência (traço curto perpendicular)
        p0 = mid + perp * 0.15
        p1 = mid - perp * 0.15
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=config.COR_DESTAQUE,
                lw=2, zorder=4)


def figura(spec: dict) -> bytes:
    spec = dict(spec or {})
    spec.setdefault("pontos", {})
    fig, ax = nova_figura()

    for pol in spec.get("poligonos", []):
        _desenha_poligono(ax, spec, pol)
    for seg in spec.get("segmentos", []):
        _desenha_segmento(ax, spec, seg)
    for ang in spec.get("angulos", []):
        _desenha_angulo(ax, spec, ang)
    for marca in spec.get("marcas", []):
        _desenha_marca(ax, spec, marca)
    for rot in spec.get("rotulos", []):
        x, y = rot["xy"]
        ax.text(x, y, rot["texto"], color=config.COR_GIZ, fontsize=15,
                ha="center", va="center", zorder=5)

    # garante que todo ponto nomeado entre no autoscale (mesmo sem traço)
    if spec["pontos"]:
        pts = np.array([np.asarray(p, dtype=float) for p in spec["pontos"].values()])
        ax.update_datalim(pts)

    ax.autoscale()
    ax.margins(0.15)
    return para_png(fig)
