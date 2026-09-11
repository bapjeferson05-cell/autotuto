"""demo_voz.py — o professor com voz (Piper) + escuta (faster-whisper).

O teclado continua sendo o 1º caminho de interrupção: `AUTOTUTO_BARGE_IN` entra
como "0" por padrão (mic NÃO abre durante a fala). Pra deixar o mic cortar:

    AUTOTUTO_BARGE_IN=1 .venv/bin/python demos/demo_voz.py

Uso:
    .venv/bin/python demos/demo_voz.py              # o ALUNO começa (fala a questão)
    .venv/bin/python demos/demo_voz.py aluno        # idem
    .venv/bin/python demos/demo_voz.py trapezio     # toca uma aula de ouro em loop
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("AUTOTUTO_BARGE_IN", "0")  # ANTES de importar config/voz

_MIN_LETRAS = 4  # abaixo disso, é ruído/silêncio "transcrito" (ex.: ". . . ."), não pergunta


def _parece_pergunta(txt: str) -> bool:
    # isalpha() por caractere (Unicode de verdade) — o range Latin-1 usado antes
    # deixava símbolos como × e ÷ passarem como "letra".
    return sum(1 for c in txt if c.isalpha()) >= _MIN_LETRAS

from autotuto import planejador  # noqa: E402
from autotuto.aulas import carregar, disponiveis  # noqa: E402
from autotuto.tocador import Tocador  # noqa: E402
from autotuto.visor import Visor  # noqa: E402
from autotuto.voz import Voz  # noqa: E402


def main() -> None:
    alvo = sys.argv[1] if len(sys.argv) > 1 else "aluno"

    visor = Visor(ritmo=0).start()  # ritmo 0 → visor.falar não dorme; a Voz manda no tempo
    visor.estado("pensando")
    visor.mostrar_fala("Carregando a voz…")

    voz = Voz()
    voz.on_injecao = visor.pop_injecao
    voz.on_inicio_fala = visor.mostrar_fala

    def falar(txt: str) -> str | None:
        r = voz.falar(txt)
        if isinstance(r, str):
            visor.aluno(r)
        return r

    def ouvir(seg: float) -> str | None:
        visor.estado("ouvindo")
        r = voz.ouvir(seg)
        visor.estado("falando")
        if r:
            visor.aluno(r)
        return r

    tocador = Tocador(falar=falar, ouvir=ouvir, desenhar=visor.desenhar, pausas=True)

    try:
        if alvo in disponiveis():
            while True:
                print(f"[demo_voz] tocando aula de ouro: {alvo}")
                tocador.toca(carregar(alvo))
                visor.estado("aguardando")
        else:
            while True:
                visor.estado("ouvindo")
                visor.mostrar_fala("Pode falar o assunto ou a questão.")
                problema = voz.ouvir(20)
                if not problema or not _parece_pergunta(problema):
                    if problema:
                        print(f"[demo_voz] ruído/silêncio, ignorando: {problema!r}")
                    continue
                print(f"[demo_voz] questão: {problema!r}")
                visor.aluno(problema)
                visor.estado("pensando")
                visor.mostrar_fala("Deixa eu montar isso aqui…")
                aula, rel = planejador.planeja(problema)
                if not rel.ok:
                    print(f"[demo_voz] planejador caiu no fallback: {rel.erros}")
                tocador.toca(aula)
                visor.estado("aguardando")
    except KeyboardInterrupt:
        print("\n[demo_voz] encerrando")
        visor.stop()


if __name__ == "__main__":
    main()
