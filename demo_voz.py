"""demo_voz.py — o Ciclo do Trapézio COM VOZ, no visor.

Roda com o Python do jarvis (Piper + faster-whisper; matplotlib+pillow já estão lá):

    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python demo_voz.py
    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python demo_voz.py pitagoras

Abre http://localhost:8080. Fale "por que que divide por dois?" durante a fórmula,
ou responda a pergunta ("vira um triângulo") — o professor reage.

Áudio: usa o DEFAULT do sistema. Se o default tiver echo-cancel (recomendado com
caixa de som), o barge-in funciona sem fone. Sem AEC e sem fone, o mic ouve o
próprio Piper — aí rode com JARVIS_BARGE_IN=0 (só a fala, sem interrupção).
"""
from __future__ import annotations

import os
import sys
import time

# voz calma de professor (o default 1.0 sai meio atropelado)
os.environ.setdefault("JARVIS_TTS_LENGTH_SCALE", "1.1")

from professor.aulas import carregar, disponiveis          # noqa: E402
from professor.tocador import Tocador                       # noqa: E402
from professor.visor import Visor                           # noqa: E402
from professor.voz import Voz, liga_no_visor                # noqa: E402


def main() -> None:
    qual = sys.argv[1] if len(sys.argv) > 1 else "trapezio"
    if qual not in disponiveis():
        print(f"aulas: {disponiveis()}")
        return

    visor = Visor(ritmo=0).start()
    visor.estado("pensando")
    voz = liga_no_visor(Voz(), visor)          # carrega Piper + faster-whisper
    voz.on_injecao = visor.pop_injecao         # contingência: teclas da página = fala do aluno
    visor.estado("pronto")

    # instrumentação: mede a latência do barge-in e mostra a transcrição
    falar_visor = voz.falar

    def falar(texto: str):
        print(f"\n  🔊 {texto}", flush=True)
        t0 = time.monotonic()
        fala = falar_visor(texto)
        if fala:
            print(f"  ✋ barge-in ~{time.monotonic() - t0:.1f}s  ·  “{fala}”", flush=True)
        return fala

    def ouvir(seg: float):
        visor.estado("ouvindo")
        r = voz.ouvir(seg)
        visor.estado("falando")
        if r:
            visor.aluno(r)
            print(f"  🎤 “{r}”", flush=True)
        return r

    loop = "loop" in sys.argv[1:]
    espera = int(os.environ.get("DEMO_ESPERA", "3"))
    print(f"\nvisor pronto em http://localhost:8080 — a aula começa em {espera}s"
          + ("  ·  modo LOOP (repete até Ctrl+C)" if loop else "  ·  Ctrl+C encerra"), flush=True)
    time.sleep(espera)

    # settle=0.5: a figura aparece e o visor pega no polling ANTES da fala
    tocador = Tocador(falar=falar, ouvir=ouvir, desenhar=visor.desenhar,
                      pausas=True, settle=0.5)
    try:
        while True:
            est = tocador.toca(carregar(qual))
            visor.estado("pronto")
            visor.resumo(est.resumo())
            print(f"\n■ {est.resumo()}", flush=True)
            if not loop:
                print("o visor segue no ar. Ctrl+C encerra.", flush=True)
                while True:
                    time.sleep(1)
            print("\n… reinicia em 8s (Ctrl+C encerra) …", flush=True)
            time.sleep(8)
    except KeyboardInterrupt:
        visor.stop()


if __name__ == "__main__":
    main()
