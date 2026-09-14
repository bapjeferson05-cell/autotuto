"""Compositor procedural: `figura(spec)` -> PNG bytes.

`spec` (todas as chaves opcionais):
  pontos     {nome: [x, y]}
  segmentos  [[a, b], ...]            a/b = nome de ponto ou [x, y] cru
             ou {"de": a, "para": b, "tracejado": bool}   (traço pontilhado)
  poligonos  [{"vs": [nomes/coords], "preenche": bool, "pintado": bool}]
  angulos    [{"vertice", "de", "para", "raio"?}]  arco (ou quadradinho se ~90°)
             "raio" separa arcos de ângulos VIZINHOS: no mesmo raio eles
             viram um arco contínuo e somem um no outro.
  marcas     [{"tipo": "cong"|"par", "de", "para"}]   ticks de congruência/paralelismo
  rotulos    [{"xy": [x, y], "texto": str}]
  circulos   [{"centro": nome ou [x,y], "raio": float,
               "preenche": bool,                 (default False)
               "pintado": bool,                  (preenchimento FORTE — ver abaixo)
               "setor": [ini, fim],              (graus; fatia em vez do círculo todo)
               "tracejado": bool}]

Dois níveis de preenchimento, porque ele tem dois papéis:
  "preenche"  discreto — só diz "é desta figura que eu estou falando".
  "pintado"   forte — o preenchimento É a resposta: a fatia comida da pizza, os
              brigadeiros que você levou. No nível discreto o aluno não distingue
              o pintado do vazio na lousa escura, e o desenho deixa de dizer 3/4.

Depende só de `config` + matplotlib/numpy + stdlib.
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Arc, Circle, Wedge

from autotuto import config
from autotuto.figuras.lousa import nova_figura, para_png


def _resolver(spec, n):
    """nome -> coord via spec['pontos']; lista de coords passa direto."""
    if isinstance(n, str):
        return np.asarray(spec["pontos"][n], dtype=float)
    return np.asarray(n, dtype=float)


def _alpha(item) -> float:
    """Opacidade do preenchimento: forte quando o fill É a mensagem ("pintado"),
    discreta quando ele só marca a figura de que se está falando ("preenche")."""
    return config.ALPHA_PINTADO if item.get("pintado", False) else config.ALPHA_FIGURA


def _desenha_poligono(ax, spec, pol):
    pts = [_resolver(spec, v) for v in pol.get("vs", [])]
    if len(pts) < 2:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    # o `alpha` de um patch dilui a face E a borda — então o preenchimento vai
    # sem borda e o contorno de giz é desenhado à parte, opacidade cheia (F4).
    if pol.get("preenche", False) or pol.get("pintado", False):
        ax.fill(xs, ys, facecolor=config.COR_AZUL, alpha=_alpha(pol),
                edgecolor="none", zorder=2)
    ax.plot(xs + [xs[0]], ys + [ys[0]], color=config.COR_GIZ, lw=2, zorder=3)


def _desenha_segmento(ax, spec, seg):
    if isinstance(seg, dict):
        a, b = _resolver(spec, seg["de"]), _resolver(spec, seg["para"])
        ls = "--" if seg.get("tracejado") else "-"
    else:
        a, b = _resolver(spec, seg[0]), _resolver(spec, seg[1])
        ls = "-"
    ax.plot([a[0], b[0]], [a[1], b[1]], color=config.COR_GIZ, lw=2, ls=ls, zorder=3)


def _desenha_angulo(ax, spec, ang):
    v = _resolver(spec, ang["vertice"])
    a = _resolver(spec, ang["de"])
    c = _resolver(spec, ang["para"])
    va, vc = a - v, c - v
    ang_a = np.degrees(np.arctan2(va[1], va[0]))
    ang_c = np.degrees(np.arctan2(vc[1], vc[0]))
    dif = abs((ang_c - ang_a + 180) % 360 - 180)
    r = float(ang.get("raio", config.RAIO_ARCO))
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
        # O Arc varre SEMPRE no anti-horário de theta1 a theta2. Com min/max,
        # um ângulo que cruza a fronteira dos ±180° (ex.: lados em 170° e -170°,
        # que são 20° de abertura) virava theta1=-170, theta2=170 → desenhava o
        # arco REFLEXO de 340°, o de fora. Escolher a ordem que varre o menor.
        t1, t2 = (ang_a, ang_c) if (ang_c - ang_a) % 360 <= 180 else (ang_c, ang_a)
        arco = Arc((v[0], v[1]), 2 * r, 2 * r, angle=0.0,
                   theta1=t1, theta2=t2,
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


def _desenha_circulo(ax, spec, circ):
    """Círculo inteiro, ou uma FATIA se vier 'setor': [ini, fim] em graus.

    A fatia é o que destrava fração na lousa (a pizza): 3/4 é um setor de 270°.
    O preenchimento vai sem borda e o contorno de giz por cima, mesma razão do
    polígono — o alpha de um patch dilui face E borda juntas."""
    c = _resolver(spec, circ["centro"])
    r = float(circ["raio"])
    # raio <=0 não é círculo: falha alto. O tocador pega a exceção e o professor
    # ADMITE que não desenhou (LIMITACAO_VISUAL) — melhor que um borrão mudo.
    if r <= 0:
        raise ValueError(f"circulo: raio tem que ser positivo (recebeu {circ['raio']!r})")
    setor = circ.get("setor")
    ls = "--" if circ.get("tracejado") else "-"

    if setor is not None:
        ini, fim = float(setor[0]), float(setor[1])
        if circ.get("preenche", False) or circ.get("pintado", False):
            ax.add_patch(Wedge(tuple(c), r, ini, fim, facecolor=config.COR_AZUL,
                               alpha=_alpha(circ), edgecolor="none", zorder=2))
        # contorno da fatia: os dois raios + o arco
        for a in (ini, fim):
            ponta = c + r * np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
            ax.plot([c[0], ponta[0]], [c[1], ponta[1]],
                    color=config.COR_GIZ, lw=2, ls=ls, zorder=3)
        ax.add_patch(Arc(tuple(c), 2 * r, 2 * r, angle=0.0, theta1=ini, theta2=fim,
                         color=config.COR_GIZ, lw=2, linestyle=ls, zorder=3))
    else:
        if circ.get("preenche", False) or circ.get("pintado", False):
            ax.add_patch(Circle(tuple(c), r, facecolor=config.COR_AZUL,
                                alpha=_alpha(circ), edgecolor="none", zorder=2))
        ax.add_patch(Circle(tuple(c), r, facecolor="none", edgecolor=config.COR_GIZ,
                            lw=2, linestyle=ls, zorder=3))

    # patch não mexe no autoscale sozinho: entrega a caixa do círculo pro datalim
    ax.update_datalim([(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)])


def figura(spec: dict) -> bytes:
    spec = dict(spec or {})
    spec.setdefault("pontos", {})
    fig, ax = nova_figura()

    for circ in spec.get("circulos", []):
        _desenha_circulo(ax, spec, circ)
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
