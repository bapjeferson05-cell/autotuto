"""bateria.py — mede quantos tópicos o planejador consegue planejar de verdade.

Existe por causa de um achado concreto: numa bateria local de 11 tópicos, 7
caíam no fallback. A causa era o prompt ir sem exemplo de JSON quando o tópico
não casava nenhuma pista — isso foi consertado, mas só o SEU hardware, com o
SEU modelo, diz se o conserto pegou. Este script é a régua.

    python demos/bateria.py                    # os 11 tópicos padrão
    python demos/bateria.py topicos.txt        # um problema por linha
    AUTOTUTO_LLM=groq python demos/bateria.py  # compara provedor

Pra decidir o constrained decoding, roda os dois e compara fallback e tempo:

    AUTOTUTO_ESQUEMA_ESTRITO=0 python demos/bateria.py
    AUTOTUTO_ESQUEMA_ESTRITO=1 python demos/bateria.py

Só planeja — não fala, não desenha, não abre visor. Nenhuma dependência nova.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autotuto import config, planejador  # noqa: E402

# Os mesmos 11 da bateria que achou o bug: 4 com aula de ouro, 7 sem.
TOPICOS = [
    "área do trapézio de bases 18 e 10 e altura 6",
    "teorema de pitágoras com catetos 3 e 4",
    "resolva 2x - 8 = 0",
    "se 3 cadernos custam 24 reais, quanto custam 5",
    "quanto é 15 por cento de 80",
    "qual o mmc de 4 e 6",
    "qual o mdc de 24 e 36",
    "área do círculo de raio 3",
    "perímetro de um retângulo de 12 por 7",
    "média aritmética de 7, 8 e 9",
    "o que são números primos",
]


def _carrega(caminho: str) -> list[str]:
    with open(caminho, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def main(argv: list[str] | None = None) -> int:
    # argv explícito: ler `sys.argv` aqui dentro faz a função pegar os
    # argumentos de quem a importa (o pytest, por exemplo) e tentar abrir "-W".
    argv = sys.argv[1:] if argv is None else argv
    topicos = _carrega(argv[0]) if argv else TOPICOS
    estrito = "ON" if config.LLM_ESQUEMA_ESTRITO else "off"
    print(f"provedor={config.LLM_PROVEDOR}  modelo={config.LLM_MODELO or '(default)'}"
          f"  esquema-estrito={estrito}")
    print(f"{len(topicos)} tópicos\n")

    linhas, fallbacks, com_aviso, total_s = [], 0, 0, 0.0
    for i, problema in enumerate(topicos, 1):
        t0 = time.monotonic()
        aula, rel = planejador.planeja(problema)
        dt = time.monotonic() - t0
        total_s += dt
        # fallback = o planejador desistiu (`erros` só é preenchido nesse caminho)
        caiu = bool(rel.erros)
        fallbacks += caiu
        com_aviso += bool(rel.avisos) and not caiu
        estado = "FALLBACK" if caiu else ("avisos  " if rel.avisos else "ok      ")
        print(f"{i:2}. {estado} {dt:6.1f}s  {problema[:46]:46}  {aula.titulo[:34]}")
        for a in (rel.erros or rel.avisos)[:3]:
            print(f"                     · {a[:100]}")
        linhas.append((problema, caiu, rel))

    n = len(topicos)
    print(f"\nplanejou: {n - fallbacks}/{n}   fallback: {fallbacks}/{n}   "
          f"com avisos: {com_aviso}/{n}")
    print(f"tempo: {total_s:.0f}s total, {total_s / max(n, 1):.1f}s por tópico")
    if fallbacks:
        print("\nos que caíram:")
        for problema, caiu, rel in linhas:
            if caiu:
                print(f"  · {problema}\n      {'; '.join(rel.erros)[:160]}")
    return 1 if fallbacks else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
