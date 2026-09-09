"""exemplos.py — roda o pipeline completo (problema → LLM → validação → aula) em
vários problemas e monta uma folha de contato com as figuras de cada aula.

    .venv/bin/python exemplos.py

out/exemplos/<slug>/*.png  — as figuras da aula na ordem
out/exemplos/<slug>.json   — o plano estruturado
out/exemplos-<slug>.png    — folha de contato
"""
from __future__ import annotations

import json
import pathlib
import sys

from PIL import Image, ImageDraw

from professor import validador
from professor.planejador import planeja
from professor.tocador import Tocador

PROBLEMAS = {
    "circulo_r5": "Quanto é a área de um círculo de raio 5? Explica passo a passo.",
    "bhaskara_x2_5x_6": "Resolva a equação x² - 5x + 6 = 0 pela fórmula de Bhaskara.",
    "trapezio_terreno": ("Um terreno tem forma de trapézio: base maior 20 m, base menor "
                         "12 m e altura 8 m. Qual é a área do terreno?"),
    "hexagono": "O que é um hexágono regular e quantos lados ele tem?",
    "pitagoras_casa": ("Uma escada de 5 m está apoiada numa parede, com a base a 3 m do pé "
                       "da parede. A que altura a escada toca a parede?"),
    "eq_1grau": "Pensei num número, multipliquei por 4 e somei 3, e deu 23. Que número é?",
    "regra3_lapis": "Se 4 lápis custam 12 reais, quanto custam 7 lápis?",
    "velocidade": "Um carro percorreu 240 km em 3 horas. Qual foi a velocidade média?",
}

OUT = pathlib.Path("out/exemplos")
OUT.mkdir(parents=True, exist_ok=True)


def contato(slug: str, pngs: list[pathlib.Path], titulo: str) -> None:
    if not pngs:
        return
    th = 300
    tiles = []
    for p in pngs:
        im = Image.open(p).convert("RGB")
        tiles.append(im.resize((int(im.width * th / im.height), th)))
    cw = max(t.width for t in tiles) + 12
    m = Image.new("RGB", (max(cw * len(tiles), 700), th + 44), (8, 20, 16))
    d = ImageDraw.Draw(m)
    d.text((8, 8), f"{titulo}", fill=(230, 235, 232))
    for i, (t, p) in enumerate(zip(tiles, pngs)):
        m.paste(t, (i * cw + 6, 34))
        d.text((i * cw + 8, th + 34), p.stem, fill=(150, 175, 165))
    m.save(f"out/exemplos-{slug}.png")
    print(f"  folha: out/exemplos-{slug}.png")


def main(quais=None):
    for slug, prob in PROBLEMAS.items():
        if quais and slug not in quais:
            continue
        print(f"\n{'='*70}\n{slug}: {prob}")
        aula, rel = planeja(prob)
        d = OUT / slug
        d.mkdir(exist_ok=True)
        (OUT / f"{slug}.json").write_text(json.dumps(aula.para_json(), ensure_ascii=False, indent=2))
        status = "OK" if rel.ok else "SANEADO"
        print(f"  → {status}  '{aula.titulo}'  {len(aula.blocos)} blocos  ramos={list(aula.ramos)}")
        for a in rel.avisos:
            print(f"    aviso: {a}")
        # toca (sem pausa) só pra gerar as figuras
        t = Tocador(out_dir=str(d), pausas=False)
        for f in d.glob("*.png"):
            f.unlink()
        t._n = 0
        try:
            t.toca(aula, interrupcoes={2: "por_que"} if aula.ramos.get("por_que") else None)
        except Exception as e:  # noqa: BLE001
            print(f"  ERRO ao tocar: {e}")
        contato(slug, sorted(d.glob("*.png")), aula.titulo)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
