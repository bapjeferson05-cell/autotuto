"""demo_voz.py — o Ciclo do Trapézio COM VOZ. Precisa do stack de áudio do jarvis.

    ~/jarvis/.venv/bin/python -m pip install matplotlib        # se faltar
    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python demo_voz.py
    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python demo_voz.py pitagoras

Abre o visor (http://localhost:8080), fala a aula pelo Piper, ouve o mic.
Durante a fórmula, fale "por que que divide por dois?" e o professor entra no ramo.

USE FONE DE OUVIDO. Sem fone, o mic capta o próprio Piper e o barge-in dispara
sozinho. Se não tiver fone: JARVIS_BARGE_IN=0 desliga a interrupção (mas aí não dá
pra testar o ciclo — só a fala).
"""
from __future__ import annotations

import sys
import time

from professor.aulas import carregar, disponiveis
from professor.tocador import Tocador
from professor.visor import Visor
from professor.voz import Voz


def main():
    qual = sys.argv[1] if len(sys.argv) > 1 else "trapezio"
    if qual not in disponiveis():
        print(f"aulas: {disponiveis()}")
        return

    visor = Visor(ritmo=0).start()
    visor.estado("pensando")
    print("[voz] carregando Piper + faster-whisper… (~15s na 1ª vez)")
    voz = Voz()

    # instrumentação: mede a latência do barge-in e mostra a transcrição
    falar_cru = voz.falar

    def falar(texto: str):
        visor.mostrar_fala(texto)
        print(f"\n  🔊 {texto}")
        t0 = time.monotonic()
        fala = falar_cru(texto)
        if fala:
            dt = time.monotonic() - t0
            print(f"  ✋ barge-in em ~{dt:.1f}s  ·  transcrição: “{fala}”")
            visor.aluno(fala)
        return fala

    voz.falar = falar
    visor.estado("pronto")
    print("\naula em 3s — fale à vontade pra interromper (Ctrl+C encerra)")
    time.sleep(3)

    est = Tocador(falar=voz.falar, desenhar=visor.desenhar, pausas=True).toca(carregar(qual))

    visor.estado("pronto")
    visor.resumo(est.resumo())
    print(f"\n■ {est.resumo()}")
    print("o visor segue no ar. Ctrl+C encerra.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        visor.stop()


if __name__ == "__main__":
    main()
