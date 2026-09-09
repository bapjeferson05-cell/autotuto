"""demo_voz.py — o Ciclo do Trapézio COM VOZ. Precisa do stack de áudio do jarvis.

    ~/jarvis/.venv/bin/python -m pip install matplotlib      # se faltar
    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python demo_voz.py

Abre o visor (http://localhost:8080), fala a aula pelo Piper, ouve o mic. Fale
"por que que divide por dois?" durante a fórmula e o professor entra no ramo.
"""
from __future__ import annotations

import time

from professor.aulas import carregar
from professor.tocador import Tocador
from professor.visor import Visor
from professor.voz import Voz, liga_no_visor


def main():
    visor = Visor(ritmo=0).start()
    visor.estado("pensando")
    voz = liga_no_visor(Voz(), visor)      # carrega Piper + faster-whisper
    visor.estado("pronto")

    print("\naula em 3s — fale à vontade pra interromper")
    time.sleep(3)

    aula = carregar("trapezio")
    est = Tocador(falar=voz.falar, desenhar=visor.desenhar, pausas=True).toca(aula)

    visor.estado("pronto")
    visor.resumo(est.resumo())
    print("\nfim. Ctrl+C encerra.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        visor.stop()


if __name__ == "__main__":
    main()
