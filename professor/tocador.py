"""tocador.py — executa uma Aula. É a "orquestração": LLM ≠ renderizador ≠ voz.

    falar     : injetado — no MVP é print; no produto é o Piper.
    desenhar  : injetado — no MVP salva PNG; no produto é a tela.

    t = Tocador()
    t.toca(aula, interrupcoes={2: "por_que"})   # aluno interrompe no bloco 2

O Tocador não sabe geometria nem aritmética. Ele lê o gerador do bloco, pede pro
`esquema.GERADORES` renderizar/calcular, e toca. O estado (onde parou, que figura
está na tela, os dados) mora no `EstadoAula`.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from professor.esquema import GERADORES, Aula
from professor.estado import EstadoAula
from professor.figuras import primitivas

_ESPERA = {"curta": 0.35, "media": 0.9, "longa": 1.8, None: 0.55}


class Tocador:
    def __init__(self, falar: Callable | None = None, desenhar: Callable | None = None,
                 out_dir="out/tocador", pausas=True):
        self.falar = falar or self._falar_stub
        self.desenhar = desenhar or self._desenhar_stub
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.pausas = pausas
        self._n = 0

    # ---------------------------------------------------------------- stubs MVP
    def _falar_stub(self, txt: str) -> None:
        print(f"  🔊 {txt}")

    def _desenhar_stub(self, png: bytes, rotulo: str) -> None:
        self._n += 1
        p = self.out / f"{self._n:02d}_{rotulo}.png"
        p.write_bytes(png)
        print(f"  🖼  {p.name}")

    # ---------------------------------------------------------------- render
    def _figura_bytes(self, spec: dict) -> tuple[bytes, str]:
        nome = spec["gerador"]
        g = GERADORES[nome]
        if nome == "figura":
            return g.fn(spec.get("spec", {})), "figura"
        return g.fn(**(spec.get("params") or {})), nome

    def _toca_bloco(self, bloco: dict) -> None:
        # a figura aparece, o professor fala sobre ela, e a conta se desenrola.
        if bloco.get("figura"):
            png, rot = self._figura_bytes(bloco["figura"])
            self.desenhar(png, rot)
        if bloco.get("diz"):
            self.falar(bloco["diz"])
        if bloco.get("calc"):
            c = bloco["calc"]
            r = GERADORES[c["gerador"]].fn(**(c.get("params") or {}))
            passos = r.passos if bloco.get("mostra_passos") else r.passos[-1:]
            for i, latex in enumerate(passos):
                self.desenhar(primitivas.passo(latex), f"passo{i+1}")
                if self.pausas:
                    time.sleep(0.5)
            bloco["_resultado"] = r.valor
        if self.pausas:
            time.sleep(_ESPERA.get(bloco.get("espera"), 0.55))

    # ---------------------------------------------------------------- topo
    def toca(self, aula: Aula, *, interrupcoes: dict[int, str] | None = None,
             classificador: Callable[[str], str] | None = None) -> EstadoAula:
        """interrupcoes: {n_do_bloco (1-based na principal): gatilho} — demo scriptada."""
        est = EstadoAula(aula)
        interrupcoes = dict(interrupcoes or {})
        print(f"\n═══ {aula.titulo} ═══")
        passo_principal = 0
        while (bloco := est.proximo()) is not None:
            if est.na_principal:
                passo_principal += 1
            marca = "│" if est.na_principal else "└─ramo"
            print(f"{marca} bloco {est.trilha.posicao}")
            self._toca_bloco(bloco)

            gat = interrupcoes.pop(passo_principal, None) if est.na_principal else None
            if gat:
                print(f"\n  ✋ aluno interrompe → '{gat}'")
                if not est.entra_ramo(gat):
                    print(f"     (sem ramo '{gat}' — professor improvisa)")
                    self.falar("Boa pergunta. Deixa eu pensar num jeito melhor de mostrar isso.")
                else:
                    for rb in est.drena_ramo():
                        print(f"└─ramo {est.trilha.posicao}")
                        self._toca_bloco(rb)
                self.falar("Voltando de onde a gente parou.")
                print(f"  ↩  {est.resumo()}\n")
        print(f"\n■ fim — {est.resumo()}")
        return est


if __name__ == "__main__":
    from professor.planejador import planeja_offline

    Tocador(pausas=False).toca(planeja_offline(), interrupcoes={3: "por_que"})
