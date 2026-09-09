"""primitivas.py — o renderizador UNIVERSAL do professor.

Em vez de uma função por figura (trapezio, triangulo...), aqui tem um conjunto de
primitivas — pontos, segmentos, polígonos, círculos, ângulos, marcas, rótulos —
e QUALQUER figura de geometria plana é uma composição delas, descrita como dados:

    figura({
      "pontos":    {"A": [0,0], "B": [18,0], "C": [14,6], "D": [4,6]},
      "poligonos": [{"vs": ["A","B","C","D"], "preenche": true}],
      "segmentos": [{"de": "A", "para": "B", "rotulo": "18", "cor": "destaque"}],
      "angulos":   [{"em": "A", "de": "D", "para": "B", "reto": true}],
      "marcas":    [{"tipo": "cong", "de": "A", "para": "D", "n": 1}],
      "rotulos":   [{"em": "C", "texto": "C", "desloca": [0.4, 0.4]}],
      "cotas":     [{"de": "A", "para": "B", "texto": "18", "lado": -1}],
    })

O LLM produz esse dicionário. Nada de código de desenho na resposta dele.
Também tem `funcao(...)` (gráfico de y=f(x)) e `reta_numerica(...)`.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, FancyArrow

FUNDO = "#0E2A22"
GIZ = "#EAEAEA"
GIZ_FRACO = "#8FA79C"
CORES = {
    "giz": GIZ, "fraco": GIZ_FRACO,
    "destaque": "#F2B134", "azul": "#5AB1E0", "verm": "#E0625E",
    "verde": "#7BD88F", "roxo": "#B98AE0",
}

plt.rcParams.update({
    "figure.facecolor": FUNDO, "axes.facecolor": FUNDO,
    "text.color": GIZ, "font.family": "DejaVu Sans", "font.size": 15,
    "mathtext.fontset": "cm",
})


def _cor(nome):
    return CORES.get(nome, nome or GIZ)


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=FUNDO, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return buf.getvalue()


def _V(p):
    return np.asarray(p, dtype=float)


def _unit(v):
    n = np.hypot(*v)
    return v / n if n > 1e-9 else v


def _perp(v):
    return np.array([-v[1], v[0]])


# ═══════════════════════════════════════════════════════ FIGURA (composição)
def figura(spec: dict, *, w=6.6, h=6.6) -> bytes:
    P = {k: _V(v) for k, v in spec.get("pontos", {}).items()}
    fig, ax = plt.subplots(figsize=(w, h), dpi=140)
    ax.set_aspect("equal")
    ax.axis("off")

    # polígonos primeiro (ficam atrás)
    for pg in spec.get("poligonos", []):
        vs = [P[n] for n in pg["vs"]]
        xs = [p[0] for p in vs] + [vs[0][0]]
        ys = [p[1] for p in vs] + [vs[0][1]]
        c = _cor(pg.get("cor", "giz"))
        ax.plot(xs, ys, color=c, lw=pg.get("lw", 2.5), zorder=2)
        if pg.get("preenche"):
            ax.fill(xs, ys, color=c, alpha=pg.get("alpha", 0.07), zorder=1)

    for cir in spec.get("circulos", []):
        ctr = P[cir["centro"]] if isinstance(cir["centro"], str) else _V(cir["centro"])
        r = float(cir["r"])
        t = np.linspace(0, 2 * np.pi, 240)
        ax.plot(ctr[0] + r * np.cos(t), ctr[1] + r * np.sin(t),
                color=_cor(cir.get("cor", "giz")), lw=cir.get("lw", 2.5), zorder=2)
        if cir.get("centro_ponto", True):
            ax.plot(*ctr, "o", color=GIZ, ms=4, zorder=3)

    for s in spec.get("segmentos", []):
        a, b = P[s["de"]], P[s["para"]]
        c = _cor(s.get("cor", "giz"))
        ax.plot([a[0], b[0]], [a[1], b[1]], color=c,
                lw=s.get("lw", 4 if s.get("cor") not in (None, "giz") else 2.5),
                ls=s.get("ls", "-"), solid_capstyle="round", zorder=3)
        if s.get("rotulo"):
            m = (a + b) / 2
            d = _perp(_unit(b - a)) * s.get("desloca", 0.55)
            ax.text(m[0] + d[0], m[1] + d[1], f"${s['rotulo']}$", color=c,
                    fontsize=16, ha="center", va="center", zorder=6, fontweight="bold")

    for mk in spec.get("marcas", []):
        a, b = P[mk["de"]], P[mk["para"]]
        m, u, pp = (a + b) / 2, _unit(b - a), _perp(_unit(b - a))
        if mk["tipo"] in ("cong", "congruencia"):
            for k in range(mk.get("n", 1)):
                off = (k - (mk.get("n", 1) - 1) / 2) * 0.28 * u
                ax.plot([m[0] + off[0] - pp[0] * 0.3, m[0] + off[0] + pp[0] * 0.3],
                        [m[1] + off[1] - pp[1] * 0.3, m[1] + off[1] + pp[1] * 0.3],
                        color=GIZ, lw=2.2, zorder=5)
        elif mk["tipo"] in ("par", "paralela"):
            for k in range(mk.get("n", 1)):
                base = m + (k - (mk.get("n", 1) - 1) / 2) * 0.34 * u
                ax.add_patch(FancyArrow(base[0] - u[0] * 0.28, base[1] - u[1] * 0.28,
                                        u[0] * 0.5, u[1] * 0.5, width=0, head_width=0.34,
                                        head_length=0.34, color=GIZ, zorder=5))

    for an in spec.get("angulos", []):
        v = P[an["em"]]
        r1 = _unit(P[an["de"]] - v)
        r2 = _unit(P[an["para"]] - v)
        c = _cor(an.get("cor", "destaque"))
        if an.get("reto"):
            s = an.get("tam", 0.6)
            p1, p2 = v + r1 * s, v + r2 * s
            ax.plot([p1[0], (p1 + p2 - v)[0], p2[0]], [p1[1], (p1 + p2 - v)[1], p2[1]],
                    color=c, lw=2, zorder=5)
        else:
            a1 = np.degrees(np.arctan2(r1[1], r1[0]))
            a2 = np.degrees(np.arctan2(r2[1], r2[0]))
            if (a2 - a1) % 360 > 180:
                a1, a2 = a2, a1
            rad = an.get("raio", 0.9)
            for k in range(an.get("n", 1)):
                ax.add_patch(Arc(v, 2 * (rad + k * 0.18), 2 * (rad + k * 0.18),
                                 theta1=a1, theta2=a2, color=c, lw=2, zorder=5))
            if an.get("rotulo"):
                mid = np.radians((a1 + a2) / 2)
                lp = v + (rad + 0.55) * np.array([np.cos(mid), np.sin(mid)])
                ax.text(lp[0], lp[1], f"${an['rotulo']}$", color=c, fontsize=14,
                        ha="center", va="center", zorder=6)

    # cotas (dimension lines):  |←—— 18 ——→|
    for ct in spec.get("cotas", []):
        a, b = P[ct["de"]], P[ct["para"]]
        u, pp = _unit(b - a), _perp(_unit(b - a))
        d = pp * ct.get("lado", -1) * ct.get("desloca", 1.1)
        A, B = a + d, b + d
        ax.annotate("", xy=B, xytext=A,
                    arrowprops=dict(arrowstyle="<|-|>", color=GIZ_FRACO, lw=1.6))
        for P0 in (a, b):
            ax.plot([P0[0], (P0 + d)[0]], [P0[1], (P0 + d)[1]], color=GIZ_FRACO, lw=1)
        m = (A + B) / 2 + pp * ct.get("lado", -1) * 0.45
        ax.text(m[0], m[1], f"${ct['texto']}$", color=GIZ, fontsize=15,
                ha="center", va="center", zorder=6)

    for n, p in P.items():
        if spec.get("mostrar_pontos", True):
            ax.plot(*p, "o", color=GIZ, ms=5, zorder=4)
        rot = next((r for r in spec.get("rotulos", []) if r.get("em") == n), None)
        txt = rot["texto"] if rot else (n if spec.get("nomear_pontos", True) else None)
        if txt:
            ds = _V(rot["desloca"]) if rot and "desloca" in rot else _V([0.4, 0.4])
            ax.text(p[0] + ds[0], p[1] + ds[1], f"${txt}$", color=GIZ, fontsize=15,
                    ha="center", va="center", zorder=6)

    for r in spec.get("rotulos", []):
        if "em" in r and r["em"] in P:
            continue
        if "xy" in r:
            ax.text(r["xy"][0], r["xy"][1], f"${r['texto']}$", color=_cor(r.get("cor", "giz")),
                    fontsize=r.get("tam", 15), ha="center", va="center", zorder=6)

    if P:
        allp = np.array(list(P.values()))
        for cir in spec.get("circulos", []):
            ctr = P[cir["centro"]] if isinstance(cir["centro"], str) else _V(cir["centro"])
            allp = np.vstack([allp, ctr + cir["r"], ctr - cir["r"]])
        lo, hi = allp.min(0), allp.max(0)
        pad = max((hi - lo).max() * 0.18, 1.2)
        ax.set_xlim(lo[0] - pad, hi[0] + pad)
        ax.set_ylim(lo[1] - pad, hi[1] + pad)
    return _png(fig)


# ═══════════════════════════════════════════════════════ FUNÇÃO
_ENV = {"sin": np.sin, "cos": np.cos, "tan": np.tan, "sqrt": np.sqrt,
        "exp": np.exp, "log": np.log, "pi": np.pi, "abs": np.abs, "e": np.e}


def funcao(expr="x**2", x0=-5.0, x1=5.0, *, raiz=False, vertice=False,
           area=None, ponto=None, titulo=None) -> bytes:
    x = np.linspace(x0, x1, 600)
    y = eval(expr, {"__builtins__": {}}, {**_ENV, "x": x})  # noqa: S307
    fig, ax = plt.subplots(figsize=(7, 6), dpi=140)
    ax.axhline(0, color=GIZ_FRACO, lw=1)
    ax.axvline(0, color=GIZ_FRACO, lw=1)
    ax.plot(x, y, color=CORES["destaque"], lw=3, zorder=3)
    if area:
        xa = np.linspace(area[0], area[1], 200)
        ya = eval(expr, {"__builtins__": {}}, {**_ENV, "x": xa})  # noqa: S307
        ax.fill_between(xa, 0, ya, color=CORES["azul"], alpha=0.28, zorder=2)
    if raiz:
        r = x[np.where(np.diff(np.sign(y)))[0]]
        ax.plot(r, r * 0, "o", color=CORES["verm"], ms=9, zorder=4)
    if vertice and "x**2" in expr.replace(" ", ""):
        i = int(np.argmin(y)) if y[0] > y[len(y) // 2] else int(np.argmax(y))
        ax.plot([x[i]], [y[i]], "s", color=CORES["verde"], ms=9, zorder=4)
    if ponto is not None:
        py = float(eval(expr, {"__builtins__": {}}, {**_ENV, "x": float(ponto)}))  # noqa: S307
        ax.plot([ponto], [py], "o", color=CORES["roxo"], ms=9, zorder=4)
    ax.set_title(titulo or f"y = {expr}", color=GIZ, fontsize=17)
    ax.grid(True, color=GIZ_FRACO, alpha=0.16)
    ax.tick_params(colors=GIZ_FRACO)
    for s in ax.spines.values():
        s.set_visible(False)
    return _png(fig)


# ═══════════════════════════════════════════════════════ RETA NUMÉRICA
def reta_numerica(x0=-5, x1=5, *, pontos=None, intervalo=None) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 1.8), dpi=140)
    ax.axis("off")
    ax.annotate("", xy=(x1 + 0.5, 0), xytext=(x0 - 0.5, 0),
                arrowprops=dict(arrowstyle="<|-|>", color=GIZ, lw=1.8))
    for k in range(int(np.ceil(x0)), int(np.floor(x1)) + 1):
        ax.plot([k, k], [-0.12, 0.12], color=GIZ_FRACO, lw=1.5)
        ax.text(k, -0.4, str(k), color=GIZ_FRACO, ha="center", fontsize=12)
    if intervalo:
        a, b = intervalo["de"], intervalo["para"]
        ax.plot([a, b], [0, 0], color=CORES["destaque"], lw=5, solid_capstyle="round", zorder=3)
        for x, fill in ((a, intervalo.get("fechado_esq", True)), (b, intervalo.get("fechado_dir", True))):
            ax.plot([x], [0], "o", ms=12, mfc=CORES["destaque"] if fill else FUNDO,
                    mec=CORES["destaque"], mew=2.5, zorder=4)
    for p in pontos or []:
        ax.plot([p["x"]], [0], "o", color=CORES["verm"], ms=10, zorder=4)
        ax.text(p["x"], 0.4, f"${p.get('rotulo', p['x'])}$", color=CORES["verm"],
                ha="center", fontsize=14)
    ax.set_xlim(x0 - 1, x1 + 1)
    ax.set_ylim(-0.8, 0.8)
    return _png(fig)


# ═══════════════════════════════════════════════════════ PASSO (uma linha de conta)
def passo(latex: str, *, tam=30, cor="giz") -> bytes:
    fig, ax = plt.subplots(figsize=(7.4, 2.0), dpi=140)
    ax.axis("off")
    ax.text(0.5, 0.5, f"${latex}$", color=_cor(cor), fontsize=tam,
            ha="center", va="center", transform=ax.transAxes)
    return _png(fig)


CATALOGO = {"figura": figura, "funcao": funcao, "reta_numerica": reta_numerica, "passo": passo}
