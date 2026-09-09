"""demo.py — o Ciclo do Trapézio, ponta a ponta, sem voz (ainda).

    .venv/bin/python demo.py                 # aluno pergunta "por que /2" no bloco 4
    .venv/bin/python demo.py e_triangulo 3   # outro ramo, em outro ponto

Mostra: aula de ouro → tocador → figuras. O aluno "fala" (texto), o classificador
escolhe o ramo, o EstadoAula empilha/desempilha, a trilha principal retoma.
out/demo/*.png  +  out/demo-tira.png (a sequência)
"""
from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageDraw

from professor.aulas import carregar
from professor.classificador import classificar
from professor.tocador import Tocador

FALAS = {
    "por_que_div_2": "Peraí… por que que divide por dois?",
    "nao_entendi": "Calma, não entendi essa parte.",
    "e_triangulo": "E se fosse um triângulo?",
    "decompor": "Tem outro jeito? Não decorei essa fórmula.",
}

OUT = pathlib.Path("out/demo")


def tira(titulo: str):
    files = sorted(OUT.glob("*.png"))
    if not files:
        return
    th = 300
    tiles = [Image.open(f).convert("RGB") for f in files]
    tiles = [t.resize((int(t.width * th / t.height), th)) for t in tiles]
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
    gat = sys.argv[1] if len(sys.argv) > 1 else "por_que_div_2"
    onde = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    aula = carregar("trapezio")
    fala = FALAS.get(gat, "por quê?")
    classificado = classificar(fala, aula.ramos)
    print(f'aluno (no bloco {onde}): "{fala}"')
    print(f"classificador → {classificado}\n")

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.png"):
        f.unlink()

    t = Tocador(out_dir=str(OUT), pausas=False)
    est = t.toca(aula, interrupcoes={onde: classificado})
    print(f"\nestado final: {est.resumo()}")
    tira(f"Ciclo do Trapézio — aluno interrompe no bloco {onde}: {classificado}")


if __name__ == "__main__":
    main()
