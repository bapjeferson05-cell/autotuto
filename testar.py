"""testar.py — bate o renderizador universal contra vários tipos de figura,
e roda os cálculos. Serve pra ver se a ferramenta é mesmo universal.

  .venv/bin/python testar.py
"""
import pathlib

from PIL import Image, ImageDraw

from professor import calc
from professor.figuras import primitivas as P

OUT = pathlib.Path("out/testar")
OUT.mkdir(parents=True, exist_ok=True)

# ─────────────────────── 12 figuras de tipos diferentes (o "banco de referência")
FIGS = {
    "trapezio_terreno": P.figura({
        "pontos": {"A": [0, 0], "B": [18, 0], "C": [14, 6], "D": [4, 6]},
        "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
        "cotas": [{"de": "A", "para": "B", "texto": "18", "lado": -1},
                  {"de": "D", "para": "C", "texto": "10", "lado": 1}],
        "angulos": [{"em": "A", "de": "B", "para": "D", "reto": True}],
    }),
    "triangulo_retangulo_345": P.figura({
        "pontos": {"A": [0, 0], "B": [4, 0], "C": [0, 3]},
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}],
        "segmentos": [{"de": "A", "para": "B", "rotulo": "3", "cor": "azul"},
                      {"de": "A", "para": "C", "rotulo": "4", "cor": "verde"},
                      {"de": "B", "para": "C", "rotulo": "5", "cor": "destaque"}],
        "angulos": [{"em": "A", "de": "B", "para": "C", "reto": True}],
    }),
    "paralelogramo_marcas": P.figura({
        "pontos": {"A": [0, 0], "B": [6, 0], "C": [8, 4], "D": [2, 4]},
        "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
        "marcas": [{"tipo": "par", "de": "A", "para": "B", "n": 1},
                   {"tipo": "par", "de": "D", "para": "C", "n": 1},
                   {"tipo": "par", "de": "A", "para": "D", "n": 2},
                   {"tipo": "par", "de": "B", "para": "C", "n": 2},
                   {"tipo": "cong", "de": "A", "para": "B", "n": 1},
                   {"tipo": "cong", "de": "D", "para": "C", "n": 1}],
    }),
    "circulo_raio_diametro": P.figura({
        "pontos": {"O": [0, 0], "A": [4, 0], "B": [-4, 0]},
        "circulos": [{"centro": "O", "r": 4}],
        "segmentos": [{"de": "O", "para": "A", "rotulo": "r", "cor": "destaque"}],
    }),
    "angulos_congruentes": P.figura({
        "pontos": {"O": [0, 0], "A": [4, 0], "B": [3, 3], "C": [-1, 4]},
        "segmentos": [{"de": "O", "para": "A"}, {"de": "O", "para": "B"}, {"de": "O", "para": "C"}],
        "angulos": [{"em": "O", "de": "A", "para": "B", "rotulo": r"\alpha", "n": 1},
                    {"em": "O", "de": "B", "para": "C", "rotulo": r"\alpha", "n": 1}],
    }),
    "quadrado_diagonal": P.figura({
        "pontos": {"A": [0, 0], "B": [5, 0], "C": [5, 5], "D": [0, 5]},
        "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
        "segmentos": [{"de": "A", "para": "C", "rotulo": "d", "cor": "destaque", "ls": (0, (4, 3))}],
        "angulos": [{"em": "A", "de": "B", "para": "D", "reto": True}],
    }),
    "pentagono": P.figura({
        "pontos": {f"P{i}": [4 * __import__("math").cos(__import__("math").radians(90 + 72 * i)),
                             4 * __import__("math").sin(__import__("math").radians(90 + 72 * i))]
                   for i in range(5)},
        "poligonos": [{"vs": [f"P{i}" for i in range(5)], "preenche": True}],
        "nomear_pontos": False,
    }),
    "reta_transversal": P.figura({
        "pontos": {"A": [-5, 1], "B": [5, 1], "C": [-5, -2], "D": [5, -2], "E": [-2, 3], "F": [2, -4]},
        "segmentos": [{"de": "A", "para": "B"}, {"de": "C", "para": "D"}, {"de": "E", "para": "F", "cor": "azul"}],
        "marcas": [{"tipo": "par", "de": "A", "para": "B"}, {"tipo": "par", "de": "C", "para": "D"}],
        "mostrar_pontos": False, "nomear_pontos": False,
    }),
    "grafico_parabola": P.funcao("x**2 - 2*x - 3", raiz=True, vertice=True, titulo="y = x² - 2x - 3"),
    "grafico_area": P.funcao("x**2", x0=-1, x1=3, area=[0, 2], titulo="área sob y = x²  de 0 a 2"),
    "seno": P.funcao("sin(x)", x0=-6.5, x1=6.5, titulo="y = sen(x)"),
    "reta_num_intervalo": P.reta_numerica(-5, 5, intervalo={"de": -1, "para": 3, "fechado_dir": False},
                                          pontos=[{"x": -1, "rotulo": "-1"}, {"x": 3, "rotulo": "3"}]),
}

# ─────────────────────── 8 cálculos
CALCS = [
    ("área do trapézio 18/10/6", calc.area_trapezio(18, 10, 6)),
    ("área do triângulo 8/5", calc.area_triangulo(8, 5)),
    ("área do círculo r=4", calc.area_circulo(4)),
    ("Pitágoras a=3 b=4", calc.pitagoras(a=3, b=4)),
    ("Pitágoras cateto c=13 b=5", calc.pitagoras(b=5, c=13)),
    ("eq 1º grau 2x-10=0", calc.eq_primeiro_grau(2, -10)),
    ("Bhaskara x²-2x-3", calc.bhaskara(1, -2, -3)),
    ("15% de 240", calc.porcentagem(todo=240, pct=15)),
    ("regra de três 3:12 = 5:x", calc.regra_de_tres(3, 12, 5)),
    ("mmc(4,6)", calc.mmc(4, 6)),
]


def main():
    print(f"=== {len(FIGS)} figuras ===")
    for nome, png in FIGS.items():
        (OUT / f"{nome}.png").write_bytes(png)
        print(f"  ✅ {nome}.png  ({len(png)//1024} KB)")

    print(f"\n=== {len(CALCS)} cálculos ===")
    for desc, r in CALCS:
        print(f"  {desc}: {r.valor} {r.unidade}")
        for p in r.passos:
            print(f"       {p}")

    # mosaico das figuras
    files = sorted(OUT.glob("*.png"))
    th = 280
    tiles = []
    for f in files:
        im = Image.open(f).convert("RGB")
        tiles.append(im.resize((int(im.width * th / im.height), th)))
    per = 4
    W = max(t.width for t in tiles) * per + 20
    rows = (len(tiles) + per - 1) // per
    m = Image.new("RGB", (W, (th + 28) * rows), (8, 20, 16))
    d = ImageDraw.Draw(m)
    for i, (t, f) in enumerate(zip(tiles, files)):
        r, c = divmod(i, per)
        x = c * (W // per) + ((W // per) - t.width) // 2
        m.paste(t, (x, r * (th + 28) + 24))
        d.text((c * (W // per) + 8, r * (th + 28) + 4), f.stem, fill=(200, 210, 205))
    m.save("out/testar-mosaico.png")
    print(f"\nmosaico: out/testar-mosaico.png {m.size}")


if __name__ == "__main__":
    main()
