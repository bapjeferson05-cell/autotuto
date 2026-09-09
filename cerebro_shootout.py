"""cerebro_shootout.py — qual LLM local escolhe o MÉTODO certo?

O 8B acerta quando a palavra está no enunciado ("área do trapézio"). O teste é o
problema em que o método está ESCONDIDO ("escada na parede" → Pitágoras).

    .venv/bin/python cerebro_shootout.py            # todos os modelos
    .venv/bin/python cerebro_shootout.py hermes3:8b mistral-small:24b
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

MODELOS = ["hermes3:8b", "qwen2.5:7b", "llama3.1:8b", "mistral-small:24b"]

CATALOGO = ["area_trapezio", "area_triangulo", "area_circulo", "area_retangulo",
            "pitagoras", "eq_primeiro_grau", "bhaskara", "porcentagem",
            "regra_de_tres", "mdc", "mmc"]

# (enunciado, método esperado, método esconde a palavra?)
PROBLEMAS = [
    ("Uma escada de 5 m está encostada numa parede, com a base a 3 m do pé da "
     "parede. Que altura ela alcança?", "pitagoras", True),
    ("Um pátio retangular tem 8 m de comprimento por 5 m de largura. Quantos "
     "metros quadrados de grama para cobrir?", "area_retangulo", True),
    ("Comprei 3 cadernos por 24 reais. Quanto vou pagar por 5 cadernos iguais?",
     "regra_de_tres", True),
    ("Pensei num número, somei 7 e deu 22. Que número é?", "eq_primeiro_grau", True),
    ("Um tênis de 200 reais está com 30 por cento de desconto. Quanto vou pagar?",
     "porcentagem", True),
    ("Qual a área de um terreno triangular de base 12 m e altura 9 m?",
     "area_triangulo", False),   # controle: a palavra está lá
    ("A diagonal de um portão retangular de 6 m por 8 m mede quanto?",
     "pitagoras", True),
    ("Um muro de 12 m² de tijolos. Cada m² leva 3 tijolos de um tipo e 4 de "
     "outro. Qual o menor número que serve pros dois?", "mmc", True),
]

PROMPT = """Você resolve problemas de matemática escolhendo UMA ferramenta de um catálogo.
NÃO faça a conta. Só diga qual ferramenta usar e com quais números.

Catálogo (nome — quando usar):
  area_trapezio (B, b, h) — área de trapézio
  area_triangulo (base, altura) — área de triângulo
  area_circulo (r) — área de círculo
  area_retangulo (base, altura) — área de retângulo / quadrado
  pitagoras (a, b, c) — triângulo retângulo: lados, diagonal, altura de escada/rampa. c = hipotenusa, passe 2 dos 3.
  eq_primeiro_grau (a, b) — resolve a·x + b = 0 (ex.: "pensei num número...")
  bhaskara (a, b, c) — resolve a·x² + b·x + c = 0
  porcentagem (parte, todo, pct) — desconto, acréscimo, "x% de y"
  regra_de_tres (a, b, c) — proporção: "se A custa B, quanto custa C"
  mdc (a, b) — máximo divisor comum
  mmc (a, b) — mínimo múltiplo comum

Responda SÓ com JSON: {"metodo": "<nome>", "params": {...}}

Problema: <<P>>"""


def _ollama(model, prompt, timeout=200):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "format": "json", "options": {"temperature": 0, "num_ctx": 2048}}).encode()
    t = time.time()
    r = urllib.request.urlopen(urllib.request.Request(
        "http://localhost:11434/api/generate", data=body,
        headers={"Content-Type": "application/json"}), timeout=timeout)
    return json.loads(r.read())["response"], time.time() - t


def _metodo(txt):
    try:
        i, j = txt.find("{"), txt.rfind("}")
        return str(json.loads(txt[i:j + 1]).get("metodo", "")).strip()
    except Exception:  # noqa: BLE001
        for c in CATALOGO:
            if c in txt:
                return c
        return "?"


def main():
    modelos = sys.argv[1:] or MODELOS
    linhas = {m: [] for m in modelos}
    tempos = {m: 0.0 for m in modelos}
    for m in modelos:
        print(f"\n=== {m} ===")
        for enun, esp, escondido in PROBLEMAS:
            try:
                out, dt = _ollama(m, PROMPT.replace("<<P>>", enun))
                got = _metodo(out)
            except Exception as e:  # noqa: BLE001
                got, dt = f"ERRO", 0.0
                print(f"  {e}")
            tempos[m] += dt
            ok = got == esp
            linhas[m].append(ok)
            flag = "ok " if ok else "XX "
            tag = "" if escondido else "  (controle)"
            print(f"  {flag} {esp:16} <- got {got:16} {dt:5.0f}s  {enun[:44]}…{tag}")

    print("\n" + "=" * 60)
    print(f"{'modelo':22} acertos   tempo médio")
    for m in modelos:
        acc = sum(linhas[m])
        print(f"{m:22} {acc}/{len(PROBLEMAS)}      {tempos[m]/len(PROBLEMAS):.0f}s")


if __name__ == "__main__":
    main()
