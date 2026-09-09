"""demo_visor.py — o Ciclo do Trapézio na tela do professor (navegador).

    .venv/bin/python demo_visor.py
    # abre http://localhost:8080, roda a aula, aluno interrompe no 4º "diz"

    .venv/bin/python demo_visor.py "e se fosse um triangulo?" 3
"""
from __future__ import annotations

import sys
import time

from professor.aulas import carregar
from professor.tocador import Tocador
from professor.visor import Visor


def main():
    fala = sys.argv[1] if len(sys.argv) > 1 else "peraí, por que que divide por dois?"
    quando = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    v = Visor(ritmo=0.05).start()
    print("abre o navegador; a aula começa em 4s")
    time.sleep(4)

    n = [0]

    def falar(texto: str):
        n[0] += 1
        r = v.falar(texto)
        if n[0] == quando:
            v.aluno(fala)
            time.sleep(0.8)
            return fala
        return r

    aula = carregar("trapezio")
    t = Tocador(falar=falar, desenhar=v.desenhar, pausas=True)
    est = t.toca(aula)
    v.estado("pronto")
    v.resumo(est.resumo())
    print("\nfim. o visor segue no ar (Ctrl+C pra sair).")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        v.stop()


if __name__ == "__main__":
    main()
