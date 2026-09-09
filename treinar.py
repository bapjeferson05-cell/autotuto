"""treinar.py — bate o renderizador contra a lista das ~100 figuras geométricas
(planas + espaciais) e diz o que a ferramenta cobre.

    .venv/bin/python treinar.py

Gera:
  out/treinar/2d/*.png, out/treinar/3d/*.png   — todas as figuras
  out/treinar/mosaico-2d.png, mosaico-3d.png   — panorama
  COBERTURA.md                                  — relatório ✅ / ⚠️ / ❌
"""
from __future__ import annotations

import pathlib
import traceback

from PIL import Image, ImageDraw

from professor.figuras import formas as F
from professor.figuras import primitivas as P
from professor.figuras import solidos as S

OUT = pathlib.Path("out/treinar")
(OUT / "2d").mkdir(parents=True, exist_ok=True)
(OUT / "3d").mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────── 2D
# (categoria, rótulo, função-sem-argumento, entra_no_mosaico)
PLANAS: list[tuple] = []


def _2d(cat, rot, fn, mosaico=False):
    PLANAS.append((cat, rot, fn, mosaico))


for t in ["equilatero", "isosceles", "escaleno", "retangulo", "acutangulo", "obtusangulo"]:
    _2d("triângulos", t, lambda t=t: F.triangulo(t), t in ("equilatero", "retangulo", "obtusangulo"))

for t in ["quadrado", "retangulo", "losango", "paralelogramo", "trapezio_isosceles",
          "trapezio_retangulo", "trapezio_escaleno", "deltoide"]:
    _2d("quadriláteros", t, lambda t=t: F.quadrilatero(t),
        t in ("quadrado", "losango", "trapezio_isosceles", "deltoide"))

_NOMES_N = {5: "pentágono", 6: "hexágono", 7: "heptágono", 8: "octógono", 9: "eneágono",
           10: "decágono", 11: "hendecágono", 12: "dodecágono", 15: "pentadecágono",
           20: "icoságono", 30: "triacontágono"}
for n in list(range(5, 31)):
    nome = _NOMES_N.get(n, f"{n}-ágono")
    _2d("polígonos regulares", f"{nome} (n={n})", lambda n=n: F.poligono_regular(n),
        n in (5, 6, 8, 10, 12))
for n, nome in [(40, "tetracontágono"), (50, "pentacontágono"), (100, "hectágono"),
                (1000, "chiliágono"), (10000, "miriágono"), (1000000, "megágono")]:
    _2d("polígonos de muitos lados", f"{nome} (n={n:,})".replace(",", "."),
        lambda n=n: F.poligono_regular(n), n in (50, 1000))

for nome in ["circulo", "circunferencia", "semicirculo", "setor", "segmento", "coroa"]:
    _2d("círculo e partes", nome, lambda nome=nome: F.parte_circulo(nome),
        nome in ("setor", "segmento", "coroa", "semicirculo"))
for nome in ["elipse", "parabola", "hiperbole", "cardioide", "lemniscata", "espiral", "cassini"]:
    _2d("curvas", nome, lambda nome=nome: F.curva(nome), True)

for nome, n, k in [("pentagrama", 5, 2), ("hexagrama", 6, 2), ("heptagrama", 7, 3),
                   ("octagrama", 8, 3), ("eneagrama", 9, 4), ("decagrama", 10, 3)]:
    _2d("estrelas", nome, lambda n=n, k=k: F.estrela(n, k), nome in ("pentagrama", "hexagrama", "octagrama"))

# ────────────────────────────────────────────────────────────────── 3D
ESPACIAIS: list[tuple] = []


def _3d(cat, rot, fn, mosaico=False):
    ESPACIAIS.append((cat, rot, fn, mosaico))


for nome in ["tetraedro", "cubo", "octaedro", "dodecaedro", "icosaedro"]:
    _3d("sólidos platônicos", nome, lambda nome=nome: S.solido(nome), True)

for nome in ["esfera", "hemisferio", "cilindro", "cone", "tronco_cone", "toro",
             "elipsoide", "paraboloide", "hiperboloide"]:
    _3d("corpos redondos", nome, lambda nome=nome: S.solido(nome),
        nome in ("esfera", "cilindro", "cone", "toro", "hiperboloide"))

_3d("prismas", "prisma triangular", lambda: S.prisma(3), True)
_3d("prismas", "paralelepípedo", lambda: S.solido("paralelepipedo"), True)
_3d("prismas", "prisma pentagonal", lambda: S.prisma(5), False)
_3d("prismas", "prisma hexagonal", lambda: S.prisma(6), True)
_3d("prismas", "prisma octogonal", lambda: S.prisma(8), False)
_3d("pirâmides", "pirâmide quadrangular", lambda: S.piramide(4), True)
_3d("pirâmides", "pirâmide pentagonal", lambda: S.piramide(5), False)
_3d("pirâmides", "tronco de pirâmide", lambda: S.solido("tronco_piramide", n=4), True)

for nome in ["tetraedro_truncado", "cuboctaedro", "cubo_truncado", "octaedro_truncado",
             "icosidodecaedro", "icosaedro_truncado"]:
    _3d("sólidos de Arquimedes", nome, lambda nome=nome: S.solido(nome),
        nome in ("cuboctaedro", "octaedro_truncado", "icosaedro_truncado"))

_3d("outros", "prisma oblíquo", lambda: S.solido("prisma", n=4, obliquo=True), True)
_3d("outros", "antiprisma triangular", lambda: S.solido("antiprisma", n=3), True)
_3d("outros", "cilindro oblíquo", lambda: S.solido("cilindro", obliquo=True), True)
_3d("outros", "bipirâmide quadrada", lambda: S.solido("bipiramide", n=4), True)
_3d("outros", "Kepler-Poinsot (poliedro estrelado)", None, False)


# ────────────────────────────────────────────────────────────────── run
def roda(itens, subdir):
    res = []
    for cat, rot, fn, mos in itens:
        slug = rot.split(" (")[0].replace(" ", "_").replace("/", "-")
        if fn is None:
            res.append((cat, rot, "faltando", None, mos))
            continue
        try:
            png = fn()
            path = OUT / subdir / f"{slug}.png"
            path.write_bytes(png)
            res.append((cat, rot, "ok", path, mos))
        except Exception as e:  # noqa: BLE001
            res.append((cat, rot, f"erro: {e}", None, mos))
            traceback.print_exc()
    return res


def mosaico(res, dest, cols=5, th=250):
    tiles = [(rot, Image.open(p).convert("RGB")) for _, rot, st, p, mos in res if mos and p]
    tiles = [(r, im.resize((int(im.width * th / im.height), th))) for r, im in tiles]
    if not tiles:
        return
    cw = max(t.width for _, t in tiles) + 12
    rows = (len(tiles) + cols - 1) // cols
    m = Image.new("RGB", (cw * cols, (th + 26) * rows), (8, 20, 16))
    d = ImageDraw.Draw(m)
    for i, (rot, t) in enumerate(tiles):
        r, c = divmod(i, cols)
        x = c * cw + (cw - t.width) // 2
        m.paste(t, (x, r * (th + 26) + 22))
        d.text((c * cw + 6, r * (th + 26) + 5), rot[:34], fill=(200, 210, 205))
    m.save(dest)
    print(f"  mosaico → {dest}  {m.size}")


_INTRO = """\
# Cobertura do renderizador — lista das ~100 figuras

As ~100 figuras da lista NÃO viram ~100 funções. Elas colapsam em **~13 geradores
paramétricos** — é isso que faz a ferramenta ser "universal":

| gerador | cobre | como |
|---|---|---|
| `figura(spec)` | trapézios, triângulos, qualquer polígono nomeado, marcações | composição de primitivas (pontos/segmentos/ângulos/marcas/cotas) |
| `formas.triangulo(tipo)` | os 6 triângulos | 6 conjuntos de 3 pontos + marcas |
| `formas.quadrilatero(tipo)` | os 8 quadriláteros | idem, 4 pontos |
| `formas.poligono_regular(n)` | pentágono … **megágono (n=10⁶)** | 1 fórmula: n vértices no círculo (acima de ~60 lados é um círculo, e essa é a lição) |
| `formas.estrela(n, k)` | pentagrama … decagrama | símbolo de Schläfli {n/k}; gcd(n,k)≠1 vira composto (hexagrama = 2 triângulos) |
| `formas.curva(nome)` | elipse, parábola, hipérbole, cardioide, lemniscata, espiral, óvalo de Cassini | equação paramétrica |
| `formas.parte_circulo(nome)` | círculo, circunferência, semicírculo, setor, segmento, coroa | recorte de arco/anel |
| `solidos.solido(nome)` | 5 platônicos + 6 arquimedianos | vértices → arestas por distância → projeção trimétrica |
| `solidos._truncar(V, t)` | os 6 sólidos de Arquimedes da lista | corta os vértices de um platônico (t=⅓ trunca, t=½ retifica) |
| corpos redondos | esfera, cilindro, cone, tronco, toro, elipsoide, paraboloide, hiperboloide | elipse achatada = "circunferência vista de lado" |
| `solidos._prisma/_piramide/...` | prismas, pirâmides, troncos, antiprisma, bipirâmide (qualquer nº de lados) | polígono base extrudado / com ápice |

Ressalvas visuais conhecidas (renderiza, mas dá pra caprichar): **toro** (leitura de
volume fraca), **cuboctaedro / octaedro truncado** (aresta oculta pela heurística de
profundidade, não por faces). **Kepler-Poinsot** exige lógica de auto-interseção —
único item ainda não coberto.

"""


def relatorio(r2d, r3d):
    linhas: list[str] = []
    tot_ok = 0
    tot = 0
    for titulo, res in [("I. Figuras planas (2D)", r2d), ("II. Figuras espaciais (3D)", r3d)]:
        linhas += [f"## {titulo}", ""]
        cat_atual = None
        for cat, rot, st, _p, _m in res:
            if cat != cat_atual:
                linhas += ["", f"### {cat}", ""]
                cat_atual = cat
            tot += 1
            if st == "ok":
                tot_ok += 1
                mark = "✅"
            elif st == "faltando":
                mark = "❌"
            else:
                mark = "⚠️"
            extra = "" if st in ("ok", "faltando") else f" — `{st}`"
            linhas.append(f"- {mark} {rot}{extra}")
        linhas.append("")
    cab = [_INTRO,
           f"**{tot_ok}/{tot} figuras renderizam.**  "
           "✅ sai da ferramenta hoje · ⚠️ renderiza com ressalva · ❌ ainda não coberto",
           ""]
    pathlib.Path("COBERTURA.md").write_text("\n".join(cab + linhas))
    print(f"\n=== {tot_ok}/{tot} figuras OK ===  → COBERTURA.md")


if __name__ == "__main__":
    print("=== 2D ===")
    r2d = roda(PLANAS, "2d")
    print("=== 3D ===")
    r3d = roda(ESPACIAIS, "3d")
    mosaico(r2d, OUT / "mosaico-2d.png", cols=5)
    mosaico(r3d, OUT / "mosaico-3d.png", cols=5)
    relatorio(r2d, r3d)
    ruins = [(rot, st) for res in (r2d, r3d) for _c, rot, st, _p, _m in res
             if st not in ("ok", "faltando")]
    if ruins:
        print("\nressalvas:")
        for rot, st in ruins:
            print(f"  ⚠️  {rot}: {st}")
