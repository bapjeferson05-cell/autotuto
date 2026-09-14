"""demo_roteiro.py — MODO GRAVAÇÃO. Determinístico, pra gravar o vídeo.

Lê um roteiro JSON (aula de ouro + interrupções/respostas por beat principal) e
toca sem LLM (`cerebro=None`) e sem microfone. Tudo scriptado → a mesma gravação
toda vez.

    .venv/bin/python demos/demo_roteiro.py [roteiros/trapezio.json]

Convenção do LEDGER: as chaves de `interrupcoes`/`respostas` são o número do beat
PRINCIPAL (`n_princ`), contando o beat de pergunta. No trapézio a pergunta é o
3º beat principal — por isso `"respostas": {"3": ...}`.
"""
from __future__ import annotations

import json
import sys
import time

from autotuto.aulas import carregar
from autotuto.tocador import Tocador
from autotuto.visor import Visor


def main() -> None:
    sys.stdout.reconfigure(line_buffering=True)  # senão o print() some até o processo sair
    caminho = sys.argv[1] if len(sys.argv) > 1 else "roteiros/trapezio.json"
    with open(caminho, encoding="utf-8") as f:
        r = json.load(f)

    visor = Visor(ritmo=float(r.get("ritmo", 0.06))).start()
    time.sleep(float(r.get("espera", 3)))  # tempo pra começar a gravar a tela

    tocador = Tocador(falar=visor.falar, desenhar=visor.desenhar, pausas=True,
                      cerebro=None, avaliador=None)
    est = tocador.toca(
        carregar(r["aula"]),
        interrupcoes={int(k): v for k, v in r.get("interrupcoes", {}).items()},
        respostas={int(k): v for k, v in r.get("respostas", {}).items()},
    )

    visor.estado("pronto")
    visor.resumo(est.resumo())
    print(f"[demo_roteiro] fim — {est.resumo()}")
    try:
        while True:
            # a caixa de texto E as teclas de contingência do visor ficam ativas
            # (estado "pronto"), mas esse modo é 100% scriptado — sem drenar os
            # dois, uma pergunta digitada OU uma tecla apertada ficava presa em
            # "pensando"/"ouvindo" pra sempre (achado ao vivo nesta sessão).
            pergunta = visor.pop_pergunta() or visor.pop_injecao()
            if pergunta:
                visor.mostrar_fala("Esse é o modo gravação (scriptado) — não respondo "
                                   "pergunta ao vivo aqui. Roda o demo_texto.py ou o "
                                   "demo_voz.py pra isso.")
                visor.estado("pronto")
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\n[demo_roteiro] encerrando")
        visor.stop()


if __name__ == "__main__":
    main()
