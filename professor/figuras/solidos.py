"""solidos.py — figuras espaciais 3D em wireframe.

Duas máquinas:
  • poliedros (platônicos + arquimedianos): lista de vértices → arestas por
    distância mínima → projeção ortográfica trimétrica → arestas de trás tracejadas.
    Os 6 sólidos de Arquimedes da lista saem TODOS de _truncar() de um platônico.
  • corpos redondos (esfera, cilindro, cone, toro...): construção 2D direta com
    elipses achatadas (a "circunferência vista de lado") — o desenho de livro.
"""
from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from professor.figuras.primitivas import CORES, FUNDO, GIZ, GIZ_FRACO, _png

PHI = (1 + math.sqrt(5)) / 2
_AZ, _EL = math.radians(27), math.radians(20)
_K = 0.34                       # achatamento de um círculo horizontal visto de cima


# ═══════════════════════════════════════════════════ infra
def _fig(legenda=None):
    fig, ax = plt.subplots(figsize=(5.4, 5.4), dpi=140)
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    ax.set_aspect("equal")
    ax.axis("off")
    if legenda:
        ax.text(0.5, 0.015, legenda, transform=ax.transAxes, color=GIZ_FRACO,
                ha="center", va="bottom", fontsize=12)
    return fig, ax


def _proj(V):
    V = np.asarray(V, float).reshape(-1, 3)
    ca, sa = math.cos(_AZ), math.sin(_AZ)
    x = ca * V[:, 0] + sa * V[:, 1]
    d = -sa * V[:, 0] + ca * V[:, 1]
    ce, se = math.cos(_EL), math.sin(_EL)
    y = ce * V[:, 2] + se * d
    dep = ce * d - se * V[:, 2]          # >0 = mais longe
    return x, y, dep


def _arestas(V, tol=0.16):
    V = np.asarray(V, float)
    n = len(V)
    D = np.linalg.norm(V[:, None, :] - V[None, :, :], axis=2)
    iu = np.triu_indices(n, 1)
    d = D[iu]
    dmin = d[d > 0.05].min()
    return [(int(i), int(j)) for i, j in zip(*iu) if 0.05 < D[i, j] <= dmin * (1 + tol)]


def _arestas_caixa(V):
    """Vértices na ordem product((-1,1)^3): adjacentes = diferem em 1 coordenada."""
    return [(i, j) for i in range(8) for j in range(i + 1, 8)
            if bin(i ^ j).count("1") == 1]


def _dedupe(V, q=3):
    seen, out = set(), []
    for p in np.asarray(V, float):
        key = tuple(np.round(p, q))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return np.array(out)


def _truncar(V, t=1 / 3):
    """Corta cada vértice: cada aresta vira 2 pontos a fração t das pontas.
    t = 1/2 → sólido retificado (cuboctaedro, icosidodecaedro)."""
    V = np.asarray(V, float)
    nv = []
    for i, j in _arestas(V):
        nv.append(V[i] + (V[j] - V[i]) * t)
        nv.append(V[j] + (V[i] - V[j]) * t)
    return _dedupe(nv)


def _poliedro(ax, V, E):
    sx, sy, dep = _proj(V)
    thr = np.quantile(dep, 0.62)
    for i, j in E:
        back = dep[i] > thr and dep[j] > thr
        ax.plot([sx[i], sx[j]], [sy[i], sy[j]], color=GIZ,
                lw=1.6 if back else 2.4, alpha=0.42 if back else 1.0,
                ls=(0, (3, 3)) if back else "-", solid_capstyle="round",
                zorder=2 if back else 3)
    if len(V) <= 12:
        for i in range(len(V)):
            ax.plot([sx[i]], [sy[i]], "o", color=GIZ, ms=2.6, zorder=4)
    m = 0.7 + 0.05 * (sx.max() - sx.min())
    ax.set_xlim(sx.min() - m, sx.max() + m)
    ax.set_ylim(sy.min() - m, sy.max() + m)


# ═══════════════════════════════════════════════════ vértices dos platônicos
def _v_tetraedro():
    return [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]


def _v_cubo():
    return [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]


def _v_octaedro():
    return [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def _v_icosaedro():
    v = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            v += [(0, s1, s2 * PHI), (s1, s2 * PHI, 0), (s2 * PHI, 0, s1)]
    return v


def _v_dodecaedro():
    v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    ip = 1 / PHI
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            v += [(0, s1 * ip, s2 * PHI), (s1 * ip, s2 * PHI, 0), (s2 * PHI, 0, s1 * ip)]
    return v


_POLIEDROS = {
    "tetraedro": (_v_tetraedro, 0.16), "cubo": (_v_cubo, 0.16),
    "hexaedro": (_v_cubo, 0.16), "octaedro": (_v_octaedro, 0.16),
    "dodecaedro": (_v_dodecaedro, 0.14), "icosaedro": (_v_icosaedro, 0.14),
    "tetraedro_truncado": (lambda: _truncar(_v_tetraedro(), 1 / 3), 0.28),
    "cuboctaedro": (lambda: _truncar(_v_cubo(), 0.5), 0.22),
    "cubo_truncado": (lambda: _truncar(_v_cubo(), 1 / 3), 0.3),
    "octaedro_truncado": (lambda: _truncar(_v_octaedro(), 1 / 3), 0.28),
    "icosidodecaedro": (lambda: _truncar(_v_icosaedro(), 0.5), 0.22),
    "icosaedro_truncado": (lambda: _truncar(_v_icosaedro(), 1 / 3), 0.3),
}


# ═══════════════════════════════════════════════════ corpos redondos (2D)
def _elipse(cx, cy, r, n=220):
    a = np.linspace(0, 2 * np.pi, n)
    return cx + r * np.cos(a), cy + _K * r * np.sin(a), a


def _anel(ax, cx, cy, r, *, tampa=False, lw=2.3):
    x, y, a = _elipse(cx, cy, r)
    if tampa:
        ax.plot(x, y, color=GIZ, lw=lw)
        return
    frente = np.sin(a) <= 0
    ax.plot(np.where(frente, x, np.nan), np.where(frente, y, np.nan), color=GIZ, lw=lw)
    ax.plot(np.where(~frente, x, np.nan), np.where(~frente, y, np.nan), color=GIZ,
            lw=lw * 0.8, ls=(0, (3, 3)), alpha=0.4)


def _lim(ax, xr, yr):
    ax.set_xlim(*xr)
    ax.set_ylim(*yr)


def _esfera(ax):
    R = 3.4
    t = np.linspace(0, 2 * np.pi, 240)
    ax.plot(R * np.cos(t), R * np.sin(t), color=GIZ, lw=2.4)
    _anel(ax, 0, 0, R)
    _lim(ax, (-R - 1, R + 1), (-R - 1, R + 1))


def _hemisferio(ax):
    R = 3.6
    t = np.linspace(0, np.pi, 160)
    ax.plot(R * np.cos(t), R * np.sin(t), color=GIZ, lw=2.4)
    _anel(ax, 0, 0, R, tampa=True)
    _lim(ax, (-R - 1, R + 1), (-R * _K - 1, R + 1))


def _elipsoide(ax):
    a, b = 3.9, 2.7
    t = np.linspace(0, 2 * np.pi, 240)
    ax.plot(a * np.cos(t), b * np.sin(t), color=GIZ, lw=2.4)
    _anel(ax, 0, 0, a * 0.98)
    _lim(ax, (-a - 1, a + 1), (-b - 1.4, b + 1.4))


def _cilindro(ax, obliquo=False):
    r, h = 2.3, 4.8
    dx = 1.7 if obliquo else 0.0
    _anel(ax, 0, 0, r)
    _anel(ax, dx, h, r, tampa=True)
    ax.plot([-r, -r + dx], [0, h], color=GIZ, lw=2.3)
    ax.plot([r, r + dx], [0, h], color=GIZ, lw=2.3)
    _lim(ax, (-r - 1.3 + min(0, dx), r + 1.3 + max(0, dx)), (-r * _K - 1.2, h + r * _K + 1.2))


def _cone(ax):
    r, h = 2.7, 5.2
    _anel(ax, 0, 0, r)
    ax.plot([-r, 0], [0, h], color=GIZ, lw=2.3)
    ax.plot([r, 0], [0, h], color=GIZ, lw=2.3)
    _lim(ax, (-r - 1.2, r + 1.2), (-r * _K - 1.2, h + 1.2))


def _tronco_cone(ax):
    r0, r1, h = 2.9, 1.6, 4.4
    _anel(ax, 0, 0, r0)
    _anel(ax, 0, h, r1, tampa=True)
    ax.plot([-r0, -r1], [0, h], color=GIZ, lw=2.3)
    ax.plot([r0, r1], [0, h], color=GIZ, lw=2.3)
    _lim(ax, (-r0 - 1.2, r0 + 1.2), (-r0 * _K - 1.2, h + r1 * _K + 1.2))


def _toro(ax):
    R, r = 2.6, 1.25
    t = np.linspace(0, 2 * np.pi, 240)
    # contorno externo e interno da "rosquinha" (elipses achatadas)
    ax.plot((R + r) * np.cos(t), _K * (R + r) * np.sin(t), color=GIZ, lw=2.4)
    ax.plot((R - r) * np.cos(t), _K * (R - r) * np.sin(t), color=GIZ, lw=2.4)
    # borda do furo, levantada (dá o volume do tubo): arco perto sólido, longe tracejado
    xh = (R - r) * np.cos(t)
    yh = _K * (R - r) * np.sin(t) + 2 * _K * r
    perto = np.sin(t) < 0
    ax.plot(np.where(perto, xh, np.nan), np.where(perto, yh, np.nan), color=GIZ, lw=2.2)
    ax.plot(np.where(~perto, xh, np.nan), np.where(~perto, yh, np.nan), color=GIZ,
            lw=1.6, ls=(0, (3, 3)), alpha=0.45)
    _lim(ax, (-R - r - 1, R + r + 1), (-_K * (R + r) - 1.6, _K * (R + r) + 1.6))


def _paraboloide(ax):
    r, h = 3.0, 4.6
    x = np.linspace(-r, r, 120)
    ax.plot(x, h * (x / r) ** 2, color=GIZ, lw=2.4)
    _anel(ax, 0, h, r)
    _lim(ax, (-r - 1.2, r + 1.2), (-1.2, h + r * _K + 1.2))


def _hiperboloide(ax):
    rw, rt, h = 1.6, 2.9, 5.4
    z = np.linspace(0, h, 120)
    x = np.sqrt(rw**2 + (rt**2 - rw**2) * (2 * z / h - 1) ** 2)
    ax.plot(x, z, color=GIZ, lw=2.4)
    ax.plot(-x, z, color=GIZ, lw=2.4)
    _anel(ax, 0, 0, rt)
    _anel(ax, 0, h / 2, rw, tampa=True)
    _anel(ax, 0, h, rt, tampa=True)
    _lim(ax, (-rt - 1.2, rt + 1.2), (-rt * _K - 1.2, h + rt * _K + 1.2))


_REDONDOS = {
    "esfera": _esfera, "hemisferio": _hemisferio, "elipsoide": _elipsoide,
    "cilindro": _cilindro, "cone": _cone, "tronco_cone": _tronco_cone,
    "toro": _toro, "paraboloide": _paraboloide, "hiperboloide": _hiperboloide,
}


# ═══════════════════════════════════════════════════ prismas / pirâmides
def _ngon(n, r, z, rot=0.0):
    return [(r * math.cos(rot + 2 * math.pi * i / n),
             r * math.sin(rot + 2 * math.pi * i / n), z) for i in range(n)]


def _prisma(n=6, *, obliquo=False):
    r, h = 1.7, 2.6
    b = _ngon(n, r, -h)
    sh = np.array([1.5, 0.5, 0.0]) if obliquo else np.zeros(3)
    t = [tuple(np.array(p) + [0, 0, 2 * h] + sh) for p in b]
    V = b + t
    E = [(i, (i + 1) % n) for i in range(n)]
    E += [(n + i, n + (i + 1) % n) for i in range(n)]
    E += [(i, n + i) for i in range(n)]
    return V, E


def _piramide(n=4):
    r, h = 1.9, 3.4
    b = _ngon(n, r, -1.4)
    V = b + [(0, 0, h)]
    E = [(i, (i + 1) % n) for i in range(n)] + [(i, n) for i in range(n)]
    return V, E


def _tronco_piramide(n=4):
    r0, r1, h = 2.1, 1.15, 1.9
    b, t = _ngon(n, r0, -h), _ngon(n, r1, h)
    V = b + t
    E = [(i, (i + 1) % n) for i in range(n)]
    E += [(n + i, n + (i + 1) % n) for i in range(n)]
    E += [(i, n + i) for i in range(n)]
    return V, E


def _antiprisma(n=3):
    r, h = 1.8, 1.9
    b = _ngon(n, r, -h, 0.0)
    t = _ngon(n, r, h, math.pi / n)
    V = b + t
    E = [(i, (i + 1) % n) for i in range(n)]
    E += [(n + i, n + (i + 1) % n) for i in range(n)]
    for i in range(n):
        E += [(i, n + i), (i, n + ((i - 1) % n))]
    return V, E


def _bipiramide(n=4):
    r, h = 1.9, 2.8
    ring = _ngon(n, r, 0.0)
    V = ring + [(0, 0, h), (0, 0, -h)]
    E = [(i, (i + 1) % n) for i in range(n)]
    E += [(i, n) for i in range(n)] + [(i, n + 1) for i in range(n)]
    return V, E


# ═══════════════════════════════════════════════════ API
def solido(nome="cubo", *, legenda=None, **kw) -> bytes:
    fig, ax = _fig(legenda or nome.replace("_", " "))
    if nome in _POLIEDROS:
        fn, tol = _POLIEDROS[nome]
        V = np.asarray(fn(), float)
        _poliedro(ax, V, _arestas(V, tol))
    elif nome in _REDONDOS:
        _REDONDOS[nome](ax, **kw) if kw else _REDONDOS[nome](ax)
    elif nome == "prisma":
        _poliedro(ax, *_map(_prisma(**kw)))
    elif nome == "piramide":
        _poliedro(ax, *_map(_piramide(**kw)))
    elif nome == "tronco_piramide":
        _poliedro(ax, *_map(_tronco_piramide(**kw)))
    elif nome == "antiprisma":
        _poliedro(ax, *_map(_antiprisma(**kw)))
    elif nome == "bipiramide":
        _poliedro(ax, *_map(_bipiramide(**kw)))
    elif nome == "paralelepipedo":
        V = np.asarray([(x * 1.7, y * 1.15, z * 0.8) for x, y, z in _v_cubo()], float)
        _poliedro(ax, V, _arestas_caixa(V))
    else:
        raise ValueError(nome)
    return _png(fig)


def _map(ve):
    V, E = ve
    return np.asarray(V, float), E


def prisma(n=6, **kw): return solido("prisma", n=n, legenda=f"prisma ({n} lados)", **kw)
def piramide(n=4, **kw): return solido("piramide", n=n, legenda=f"pirâmide ({n} lados)", **kw)


CATALOGO_3D = {"solido": solido}
