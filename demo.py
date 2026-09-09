"""demo.py — o Ciclo do Trapézio, ponta a ponta, sem áudio.

    .venv/bin/python demo.py                 # aluno responde a pergunta + interrompe
    .venv/bin/python demo.py "não entendi" 3 # fala isso no 3º "diz"

Dublês de `falar`/`ouvir`: no beat 'pergunta' o aluno "responde" (RESP); num
outro ponto ele "interrompe" a fala (FALA @ QUANDO). Mesma máquina do pipeline de voz.
out/demo/*.png + out/demo-tira.png
"""
from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageDraw

from professor.aulas import carregar
from professor.tocador import Tocador

OUT = pathlib.Path("out/demo")
RESP = "acho que vira um triângulo"        # resposta à pergunta do beat 'pergunta'


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
    fala = sys.argv[1] if len(sys.argv) > 1 else "peraí, por que que divide por dois?"
    quando = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.png"):
        f.unlink()

    n = [0]

    def falar(texto: str):
        n[0] += 1
        print(f"  🔊 {texto}")
        if n[0] == quando:
            print(f'  🎤 aluno (interrompe): "{fala}"')
            return fala
        return None

    def ouvir(_seg: float):
        print(f'  🎤 aluno (responde): "{RESP}"')
        return RESP

    t = Tocador(falar=falar, ouvir=ouvir, out_dir=str(OUT), pausas=False)
    est = t.toca(carregar("trapezio"))
    print(f"\nestado final: {est.resumo()}")
    tira(f"Ciclo do Trapézio — pergunta respondida + interrupção “{fala}”")


if __name__ == "__main__":
    main()
