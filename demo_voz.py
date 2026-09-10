"""demo_voz.py — o professor COM VOZ, no visor.

    ~/jarvis/.venv/bin/python demo_voz.py                 # padrão: o ALUNO começa — descreve o
                                                          # problema, o planejador monta a aula
                                                          # na hora (é a proposta do projeto)
    ~/jarvis/.venv/bin/python demo_voz.py trapezio loop   # aula de ouro fixa, só se pedida por nome
    ~/jarvis/.venv/bin/python demo_voz.py pitagoras loop
(sempre com  PYTHONPATH=~/professor-matematica  na frente)

Abre http://localhost:8080. Interrompe por voz ("por que divide por dois?") ou por
tecla na página (1/2/3/0, Espaço) — contingência pra mic ruim.

Áudio: usa o DEFAULT do sistema. Com echo-cancel no default, o barge-in funciona
com caixa de som, sem fone.
"""
from __future__ import annotations

import os
import sys
import time

os.environ.setdefault("JARVIS_TTS_LENGTH_SCALE", "1.1")   # voz calma de professor

from professor.aulas import carregar, disponiveis          # noqa: E402
from professor.fillers import filler_para                  # noqa: E402
from professor.tocador import Tocador                       # noqa: E402
from professor.visor import Visor                           # noqa: E402
from professor.voz import Voz, liga_no_visor                # noqa: E402


def _monta_callbacks(voz: Voz, visor: Visor):
    falar_visor = voz.falar

    def falar(texto: str):
        print(f"\n  🔊 {texto}", flush=True)
        t0 = time.monotonic()
        fala = falar_visor(texto)
        if fala:
            print(f"  ✋ ~{time.monotonic() - t0:.1f}s  ·  “{fala}”", flush=True)
        return fala

    def ouvir(seg: float):
        visor.estado("ouvindo")
        r = voz.ouvir(seg)
        visor.estado("falando")
        if r:
            visor.aluno(r)
            print(f"  🎤 “{r}”", flush=True)
        return r

    return falar, ouvir


def _aula_do_aluno(voz: Voz, visor: Visor):
    """O aluno fala o problema; o planejador monta a aula. Filler cobre a espera."""
    from professor import planejador

    visor.estado("pronto")
    visor.mostrar_fala("Pode perguntar. Descreve o teu problema de matemática.")
    voz.falar("Pode perguntar. Descreve o teu problema.")
    problema = voz.ouvir()                       # bloqueia até o aluno falar
    if not problema:
        return None
    visor.aluno(problema)
    print(f"\n  🎤 problema: “{problema}”", flush=True)

    visor.estado("pensando")
    voz.falar(filler_para("_planejando"))        # "deixa eu montar isso aqui"
    t0 = time.monotonic()
    aula, rel = planejador.planeja(problema, verbose=True)
    print(f"  planejador: {time.monotonic() - t0:.0f}s · '{aula.titulo}' · "
          f"{len(aula.blocos)} blocos · ok={rel.ok}", flush=True)
    return aula


def main() -> None:
    args = sys.argv[1:]
    loop = "loop" in args
    nomeados = [a for a in args if a not in ("aluno", "loop")]
    qual = next((a for a in nomeados if a in disponiveis()), None)
    if nomeados and qual is None:
        print(f"[aviso] '{nomeados[0]}' não é uma aula conhecida "
              f"({', '.join(disponiveis())}) — o aluno vai começar a conversa.", flush=True)
    # por padrão o ALUNO começa (é a proposta do projeto). Só toca uma aula fixa
    # se ela for pedida explicitamente por nome.
    modo_aluno = "aluno" in args or qual is None

    visor = Visor(ritmo=0).start()
    visor.estado("pensando")
    voz = liga_no_visor(Voz(), visor)
    voz.on_injecao = visor.pop_injecao          # contingência: teclas da página

    if modo_aluno:                              # pré-aquece o LLM do planejador
        try:
            from professor.planejador import _llm_json
            print("[llm] pré-aquecendo o planejador…", flush=True)
            _llm_json([{"role": "user", "content": "responda só: ok"}], timeout=90)
        except Exception as e:  # noqa: BLE001
            print(f"[llm] pré-aquecimento pulado ({e})", flush=True)

    visor.estado("pronto")
    falar, ouvir = _monta_callbacks(voz, visor)
    tocador = Tocador(falar=falar, ouvir=ouvir, desenhar=visor.desenhar,
                      pausas=True, settle=0.5)

    espera = int(os.environ.get("DEMO_ESPERA", "3"))
    print(f"\nvisor → http://localhost:8080  ·  "
          f"{'ALUNO começa' if modo_aluno else 'aula ' + qual}"
          f"{'  ·  LOOP' if loop else ''}  ·  começa em {espera}s", flush=True)
    time.sleep(espera)

    try:
        while True:
            aula = _aula_do_aluno(voz, visor) if modo_aluno else carregar(qual)
            if aula is None:
                print("  (não entendi o problema — repetindo)", flush=True)
                continue
            est = tocador.toca(aula)
            visor.estado("pronto")
            visor.resumo(est.resumo())
            print(f"\n■ {est.resumo()}", flush=True)
            if not loop and not modo_aluno:
                print("visor no ar. Ctrl+C encerra.", flush=True)
                while True:
                    time.sleep(1)
            print("\n… de novo em 8s (Ctrl+C encerra) …", flush=True)
            time.sleep(8)
    except KeyboardInterrupt:
        visor.stop()


if __name__ == "__main__":
    main()
