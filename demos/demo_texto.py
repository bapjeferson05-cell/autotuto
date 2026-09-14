"""demo_texto.py — o professor só com teclado. Sem TTS, sem microfone.

É o caminho mais leve: `Visor` desenha a lousa e "fala" dormindo proporcional ao
texto; o aluno digita o assunto na caixa e aperta 1/2/3/0 pra interromper.

    .venv/bin/python demos/demo_texto.py
    # abre http://localhost:8080 — digite a questão, Enter.
"""
from __future__ import annotations

import sys
import threading
import time

from autotuto import config, planejador
from autotuto.tocador import Tocador
from autotuto.visor import Visor

_FILLERS_ESPERA = (
    (7, "Ainda pensando nisso, um instante…"),
    (20, "Essa tá dando um pouco mais de trabalho, já te mostro."),
)


def _planeja_com_filler(problema: str, falar) -> tuple:
    """planejador.planeja roda numa thread; se demorar, o professor avisa em vez
    de ficar mudo (achado ao vivo: local pode levar minutos sem dizer nada)."""
    resultado: dict = {}

    def alvo():
        resultado["r"] = planejador.planeja(problema)

    th = threading.Thread(target=alvo, daemon=True)
    th.start()
    t0 = time.monotonic()
    ditos = set()
    while th.is_alive():
        dt = time.monotonic() - t0
        for limite, frase in _FILLERS_ESPERA:
            if dt >= limite and limite not in ditos:
                ditos.add(limite)
                falar(frase)
        time.sleep(0.5)
    th.join()
    return resultado["r"]


def main() -> None:
    sys.stdout.reconfigure(line_buffering=True)  # senão o print() some até o processo sair
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

    convidou = False
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
            aula, rel = _planeja_com_filler(problema, visor.falar)
            if not rel.ok:
                print(f"[demo_texto] planejador caiu no fallback: {rel.erros}")
                # a própria aula de fallback já diz isso em voz alta
                # (aulas.AULA_SEM_PLANO) — repetir aqui vira desculpa em dobro.
            if not convidou:      # uma vez só — repetir a cada aula irrita
                visor.falar(config.CONVITE_INTERRUPCAO)
                convidou = True
            tocador.toca(aula)
            visor.estado("aguardando")
            visor.mostrar_fala("Pode perguntar outra coisa.")
    except KeyboardInterrupt:
        print("\n[demo_texto] encerrando")
        visor.stop()


if __name__ == "__main__":
    main()
