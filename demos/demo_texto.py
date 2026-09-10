"""demo_texto.py — o professor só com teclado. Sem TTS, sem microfone.

É o caminho mais leve: `Visor` desenha a lousa e "fala" dormindo proporcional ao
texto; o aluno digita o assunto na caixa e aperta 1/2/3/0 pra interromper.

    .venv/bin/python demos/demo_texto.py
    # abre http://localhost:8080 — digite a questão, Enter.
"""
from __future__ import annotations

import time

from autotuto import config, planejador
from autotuto.tocador import Tocador
from autotuto.visor import Visor


def main() -> None:
    visor = Visor(ritmo=config.RITMO_S_POR_CHAR).start()
    visor.estado("aguardando")

    def ouvir(seg: float) -> str | None:
        """Escuta = poll do teclado por até min(seg, 8) s (resposta a uma pergunta)."""
        fim = time.monotonic() + min(seg, 8)
        while time.monotonic() < fim:
            t = visor.pop_injecao()
            if t:
                return t
            time.sleep(0.05)
        return None

    tocador = Tocador(
        falar=visor.falar,
        ouvir=ouvir,
        desenhar=visor.desenhar,
        pausas=True,
    )

    try:
        while True:
            problema = None
            while not problema:
                problema = visor.pop_pergunta()
                if not problema:
                    time.sleep(0.15)
            print(f"[demo_texto] questão: {problema!r}")
            visor.estado("pensando")
            visor.mostrar_fala("Deixa eu montar isso aqui…")
            aula, rel = planejador.planeja(problema)
            if not rel.ok:
                print(f"[demo_texto] planejador caiu no fallback: {rel.erros}")
            tocador.toca(aula)
            visor.estado("aguardando")
            visor.mostrar_fala("Pode perguntar outra coisa.")
    except KeyboardInterrupt:
        print("\n[demo_texto] encerrando")
        visor.stop()


if __name__ == "__main__":
    main()
