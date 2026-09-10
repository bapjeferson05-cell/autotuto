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
RESP = {"trapezio": "acho que vira um triângulo",
        "eq_primeiro_grau": "tenho que fazer nos dois lados",
        "regra_de_tres": "vai ficar maior",
        "pitagoras": "a escada"}                # resposta certa à pergunta (dispara o fading)


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
    aula = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in (
        "trapezio", "pitagoras", "eq_primeiro_grau", "regra_de_tres") else "trapezio"
    fala = next((a for a in sys.argv[1:] if a not in
                 ("trapezio", "pitagoras", "eq_primeiro_grau", "regra_de_tres")),
                "peraí, por que que divide por dois?")
    quando = 99   # sem interrupção por padrão — o foco é o beat pergunta + fading

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
        r = RESP.get(aula, "")
        print(f'  🎤 aluno (responde): "{r}"')
        return r

    t = Tocador(falar=falar, ouvir=ouvir, out_dir=str(OUT), pausas=False)
    est = t.toca(carregar(aula))
    print(f"\nestado final: {est.resumo()}")
    tira(f"{aula} — beat pergunta respondido")


if __name__ == "__main__":
    main()
