"""tocador.py — executa uma Aula. É a "orquestração": LLM ≠ renderizador ≠ voz.

    falar(texto) -> str | None   injetado. Fala. Se o aluno interromper, devolve a
                                 fala dele (transcrita); senão, None.
    desenhar(png, rotulo)        injetado. Mostra a figura.

    t = Tocador(falar=..., desenhar=...)
    t.toca(aula)                              # interrupção real, via retorno do falar
    t.toca(aula, interrupcoes={4: "por_que_div_2"})   # demo scriptada (sem voz)

O Tocador não sabe geometria nem aritmética. Lê o gerador do bloco, pede pro
`esquema.GERADORES` renderizar/calcular, toca. O estado (onde parou, que figura está
na tela, os dados) mora no `EstadoAula`. Quem interpreta a fala do aluno é o
`classificador`; quem dá o "estou aqui" imediato é o `fillers`.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from professor.classificador import classificar
from professor.esquema import GERADORES, Aula
from professor.estado import EstadoAula
from professor.fillers import filler_para
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
        return None

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

    def _toca_bloco(self, bloco: dict) -> str | None:
        """Toca um bloco. Devolve a fala do aluno se ele interrompeu, senão None."""
        if bloco.get("figura"):
            png, rot = self._figura_bytes(bloco["figura"])
            self.desenhar(png, rot)
        if bloco.get("diz"):
            fala = self.falar(bloco["diz"])
            if fala:
                return fala
        if bloco.get("calc"):
            c = bloco["calc"]
            r = GERADORES[c["gerador"]].fn(**(c.get("params") or {}))
            passos = r.passos if bloco.get("mostra_passos") else r.passos[-1:]
            for i, latex in enumerate(passos):
                self.desenhar(primitivas.passo(latex), f"passo{i + 1}")
                if self.pausas:
                    time.sleep(0.5)
            bloco["_resultado"] = r.valor
        if self.pausas:
            time.sleep(_ESPERA.get(bloco.get("espera"), 0.55))
        return None

    # ---------------------------------------------------------------- topo
    def toca(self, aula: Aula, *, interrupcoes: dict[int, str] | None = None) -> EstadoAula:
        est = EstadoAula(aula)
        script = dict(interrupcoes or {})
        print(f"\n═══ {aula.titulo} ═══")
        n_princ = 0
        while (bloco := est.proximo()) is not None:
            if est.na_principal:
                n_princ += 1
            print(f"{'│' if est.na_principal else '└'} bloco {est.trilha.posicao}")
            fala = self._toca_bloco(bloco)

            gat = None
            if fala:                                   # interrupção real (voz)
                gat = classificar(fala, est.aula.ramos) or "por_que"
                print(f'  ✋ "{fala}"  →  {gat}')
            elif est.na_principal and n_princ in script:   # interrupção scriptada
                gat = script.pop(n_princ)
                print(f"  ✋ (script) → {gat}")

            if gat:
                self._entra_ramo(est, gat)
        print(f"\n■ fim — {est.resumo()}")
        return est

    def _entra_ramo(self, est: EstadoAula, gat: str) -> None:
        self.falar(filler_para(gat))                    # "estou aqui" imediato
        if not est.entra_ramo(gat):
            self.falar("Boa pergunta. Deixa eu achar um jeito melhor de mostrar isso.")
            return
        for rb in est.drena_ramo():
            print(f"  └ ramo {est.trilha.posicao}")
            nova = self._toca_bloco(rb)
            if nova:                                    # aluno interrompe DENTRO do ramo
                g2 = classificar(nova, est.aula.ramos)
                print(f'    ✋ "{nova}"  →  {g2}')
                if g2 and g2 != gat:
                    est.sai_ramo()
                    self._entra_ramo(est, g2)
                    return
        self.falar("Voltando de onde a gente parou.")
        print(f"  ↩  {est.resumo()}")


if __name__ == "__main__":
    from professor.aulas import carregar

    Tocador(pausas=False).toca(carregar("trapezio"), interrupcoes={4: "por_que_div_2"})
