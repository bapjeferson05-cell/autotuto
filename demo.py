"""demo.py — o Ciclo do Trapézio, ponta a ponta, sem áudio (ainda).

    .venv/bin/python demo.py                          # aluno fala "por que /2" no 4º "diz"
    .venv/bin/python demo.py "e se fosse um triangulo?" 2

O `falar` aqui é um dublê: imprime a fala do professor e, no momento marcado,
"ouve" o aluno (devolve a transcrição). O Tocador classifica, dá o filler, entra no
ramo e retoma — a mesma máquina que o pipeline de voz vai usar.
out/demo/*.png  +  out/demo-tira.png
"""
from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageDraw

from professor.aulas import carregar
from professor.tocador import Tocador

OUT = pathlib.Path("out/demo")


def falar_dubla(quando: int, fala_aluno: str):
    """Devolve um `falar` que, na n-ésima chamada, retorna a fala do aluno."""
    n = [0]

    def falar(texto: str):
        n[0] += 1
        print(f"  🔊 {texto}")
        if n[0] == quando:
            print(f'\n  🎤 aluno: "{fala_aluno}"')
            return fala_aluno
        return None

    return falar


def tira(titulo: str):
    files = sorted(OUT.glob("*.png"))
    if not files:
        return
    th = 300
    tiles = [Image.open(f).convert("RGB").resize(
        (int(Image.open(f).width * th / Image.open(f).height), th)) for f in files]
    cw = max(t.width for t in tiles) + 10
    m = Image.new("RGB", (cw * len(tiles), th + 46), (8, 20, 16))
    d = ImageDraw.Draw(m)
    d.text((8, 8), titulo, fill=(235, 238, 235))
    for i, (t, f) in enumerate(zip(tiles, files)):
        m.paste(t, (i * cw + 5, 34))
        d.text((i * cw + 7, th + 34), f.stem, fill=(150, 175, 165))
    m.save("out/demo-tira.png")
    print(f"\ntira: out/demo-tira.png  {m.size}")


def main():
    fala = sys.argv[1] if len(sys.argv) > 1 else "peraí, por que que divide por dois?"
    quando = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.png"):
        f.unlink()

    aula = carregar("trapezio")
    t = Tocador(falar=falar_dubla(quando, fala), out_dir=str(OUT), pausas=False)
    est = t.toca(aula)
    print(f"\nestado final: {est.resumo()}")
    tira(f"Ciclo do Trapézio — aluno: “{fala}”")


if __name__ == "__main__":
    main()
