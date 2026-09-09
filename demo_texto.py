"""demo_texto.py — o professor SEM voz: o aluno DIGITA o assunto ou cola a questão.

    .venv/bin/python demo_texto.py

Modo leve (não carrega faster-whisper nem Piper — ~1 GB a menos de RAM). Serve pra:
  - máquina fraca / sem mic
  - contingência quando o áudio do local falha
  - a "porta 2" do produto: o aluno escreve "quero entender trapézio" ou cola uma
    questão inteira, e o professor monta a aula.

Abre http://localhost:8080. Digite na caixa. Interrompa com as teclas 1/2/3/0.
Cérebro: PROF_LLM=claude (rápido) ou o qwen2.5:7b local (default, mais lento).
"""
from __future__ import annotations

import os
import sys
import time

from professor import planejador
from professor.tocador import Tocador
from professor.visor import Visor


def main() -> None:
    ritmo = float(os.environ.get("DEMO_RITMO", "0.05"))   # s/char da "fala" no visor
    visor = Visor(ritmo=ritmo).start()
    visor.estado("aguardando")
    cerebro = planejador.MODELO if planejador.PROVEDOR == "ollama" else planejador.CLAUDE_MODELO
    print(f"visor → http://localhost:8080  ·  digite o assunto / a questão na caixa\n"
          f"cérebro: {planejador.PROVEDOR} ({cerebro})", flush=True)

    def ouvir(seg: float):                       # no modo texto, "ouvir" = esperar tecla
        fim = time.monotonic() + min(seg, 8.0)
        while time.monotonic() < fim:
            t = visor.pop_injecao()
            if t:
                return t
            time.sleep(0.15)
        return None

    tocador = Tocador(falar=visor.falar, ouvir=ouvir,
                      desenhar=visor.desenhar, pausas=True, settle=0.45)

    try:
        while True:
            problema = None
            while not problema:
                problema = visor.pop_pergunta()
                time.sleep(0.15)
            print(f"\n🎤 “{problema}”", flush=True)
            visor.estado("pensando")
            visor.mostrar_fala("Deixa eu montar isso aqui…")

            t0 = time.monotonic()
            aula, rel = planejador.planeja(problema, verbose=True)
            print(f"planejador: {time.monotonic()-t0:.0f}s · '{aula.titulo}' · "
                  f"{len(aula.blocos)} blocos · ok={rel.ok}", flush=True)
            if rel.avisos:
                print("  avisos:", rel.avisos, flush=True)

            est = tocador.toca(aula)
            visor.resumo(est.resumo())
            visor.estado("aguardando")
            visor.mostrar_fala("Pode perguntar outra coisa.")
            print(f"\n■ {est.resumo()}\n", flush=True)
    except KeyboardInterrupt:
        visor.stop()


if __name__ == "__main__":
    main()
