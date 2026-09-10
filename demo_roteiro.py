"""demo_roteiro.py — MODO GRAVAÇÃO. A aula roda sozinha no visor, com as
interrupções e respostas SCRIPTADAS. Zero STT, zero mic — 100% determinístico,
pra gravar o vídeo da Maratona sem depender do reconhecimento de voz na hora.

    PYTHONPATH=. .venv/bin/python demo_roteiro.py roteiros/trapezio.json

Formato do JSON:
{
  "aula": "trapezio",                       # nome em professor/aulas.py
  "ritmo": 0.06,                            # s por caractere da "fala" no visor
  "espera": 3,                              # s antes de começar (deixa você posicionar a tela)
  "interrupcoes": {"2": "por_que_div_2"},   # DEPOIS do Nº-ésimo beat da trilha principal → dispara esse ramo
  "respostas":    {"4": "acho que vira um triângulo"}   # resposta ao beat 'pergunta' que é o Nº-ésimo da principal
}

Descubra os números rodando `.venv/bin/python demo.py <aula>` uma vez e contando os
`│ bloco X/Y` da trilha principal.
"""
from __future__ import annotations

import json
import sys
import time

from professor.aulas import carregar, disponiveis
from professor.tocador import Tocador
from professor.visor import Visor


def main() -> None:
    caminho = sys.argv[1] if len(sys.argv) > 1 else "roteiros/trapezio.json"
    with open(caminho, encoding="utf-8") as f:
        r = json.load(f)
    if r["aula"] not in disponiveis():
        sys.exit(f"aula '{r['aula']}' não existe. tem: {', '.join(disponiveis())}")

    visor = Visor(ritmo=float(r.get("ritmo", 0.06))).start()
    visor.estado("pensando")
    tocador = Tocador(falar=visor.falar, desenhar=visor.desenhar,
                      pausas=True, settle=0.5, cerebro=None)   # scriptado: sem LLM
    interrup = {int(k): v for k, v in r.get("interrupcoes", {}).items()}
    respost = {int(k): v for k, v in r.get("respostas", {}).items()}

    print(f"\n▶ roteiro: {caminho}  ·  aula: {r['aula']}  ·  visor → http://localhost:8080")
    print(f"  interrupções: {interrup or '—'}   respostas: {respost or '—'}")
    time.sleep(float(r.get("espera", 3)))

    est = tocador.toca(carregar(r["aula"]), interrupcoes=interrup, respostas=respost)
    visor.estado("pronto")
    visor.resumo(est.resumo())
    print(f"\n■ {est.resumo()}\nvisor no ar. Ctrl+C encerra.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        visor.stop()


if __name__ == "__main__":
    main()
