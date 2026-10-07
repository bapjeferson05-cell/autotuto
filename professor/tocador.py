"""tocador.py — executa uma Aula. É a "orquestração": LLM ≠ renderizador ≠ voz.

    falar(texto) -> str | None   Fala. Se o aluno interromper, devolve a fala dele.
    ouvir(seg)   -> str | None   Escuta até `seg` s. Devolve a fala, ou None se calou.
    desenhar(png, rotulo)        Mostra a figura.

    t = Tocador(falar=..., ouvir=..., desenhar=...)
    t.toca(aula)
    t.toca(aula, interrupcoes={4: "por_que_div_2"})   # demo scriptada
    t.toca(aula, respostas={3: "vira um triângulo"})  # respostas scriptadas p/ beats 'pergunta'

Tipos de beat:
  - fala/figura/calc: o professor expõe (worked example).
  - "pergunta": {"escuta_s": 12, "senao": "<ramo>"} — o professor faz uma pergunta e
    ESPERA. A resposta do aluno é classificada nos ramos da aula; sem resposta (ou sem
    classificar) → ramo "senao". (self-explanation: o ganho está no aluno explicando.)
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
    def __init__(self, falar: Callable | None = None, ouvir: Callable | None = None,
                 desenhar: Callable | None = None, out_dir="out/tocador", pausas=True,
                 settle: float = 0.4):
        self.falar = falar or self._falar_stub
        self.ouvir = ouvir or (lambda _s: None)
        self.desenhar = desenhar or self._desenhar_stub
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.pausas = pausas
        self.settle = settle          # s entre a figura aparecer e a fala começar
        self._n = 0
        # Interrupção que chegou numa fala onde não dá pra agir na hora (filler,
        # "voltando de onde a gente parou", confirma). Antes o retorno era jogado
        # fora e a tecla do aluno morria ali; aqui ela espera o próximo ponto de
        # decisão em vez de sumir.
        self._pendente: str | None = None

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

    def _fala_guardando(self, texto: str) -> None:
        """Fala onde quem chama não tem como tratar uma interrupção na hora.
        Se o aluno falar durante essa fala, guarda em vez de descartar."""
        fala = self.falar(texto)
        if fala:
            self._pendente = fala

    def _pega_pendente(self) -> str | None:
        t, self._pendente = self._pendente, None
        return t

    def _toca_bloco(self, bloco: dict) -> tuple[str, str | None] | None:
        """Toca um beat. Devolve:
          ("barge", <fala>)      — aluno cortou a fala
          ("resposta", <fala>?)  — era um beat 'pergunta'; eis a resposta (None = calou)
          None                   — beat normal, seguiu
        """
        tem_figura = bool(bloco.get("figura"))
        if tem_figura:
            png, rot = self._figura_bytes(bloco["figura"])
            self.desenhar(png, rot)
        falado = None
        if bloco.get("diz"):
            if tem_figura and self.settle and self.pausas:   # figura entra ANTES da fala
                time.sleep(self.settle)
            falado = self.falar(bloco["diz"])
            # num beat de PERGUNTA, falar enquanto a pergunta é lida é RESPONDER, não
            # interromper: a tela manda apertar 0 pra responder, e tratar isso como
            # barge consumia o beat, pulava o `confirma` e mandava quem acertou pro
            # ramo de quem errou — sem nunca fazer a pergunta.
            if falado and not bloco.get("pergunta"):
                return ("barge", falado)
        if bloco.get("pergunta"):
            if "_resp_scriptada" in bloco:
                return ("resposta", bloco["_resp_scriptada"])
            if falado:
                print(f'  🎤 (respondeu durante a pergunta) "{falado}"')
                return ("resposta", falado)
            seg = int(bloco["pergunta"].get("escuta_s", 12))
            print(f"  ⏳ esperando resposta ({seg}s)…")
            return ("resposta", self.ouvir(seg))
        if bloco.get("calc"):
            c = bloco["calc"]
            r = GERADORES[c["gerador"]].fn(**(c.get("params") or {}))
            passos = r.passos if bloco.get("mostra_passos") else r.passos[-1:]
            narra = bloco.get("diz_passos") or []        # 1 frase curta por passo (opcional)
            for i, latex in enumerate(passos):
                self.desenhar(primitivas.passo(latex), f"passo{i + 1}")
                if i < len(narra) and narra[i]:          # worked example: vê o passo E ouve o porquê
                    fala = self.falar(narra[i])
                    if fala:
                        return ("barge", fala)
                elif self.pausas:                        # sem narração: pausa pra o passo assentar
                    time.sleep(1.1 if i < len(passos) - 1 else 0.7)
            bloco["_resultado"] = r.valor
        if self.pausas:
            time.sleep(_ESPERA.get(bloco.get("espera"), 0.55))
        return None

    # ---------------------------------------------------------------- topo
    def toca(self, aula: Aula, *, interrupcoes: dict[int, str] | None = None,
             respostas: dict[int, str] | None = None) -> EstadoAula:
        est = EstadoAula(aula)
        script = dict(interrupcoes or {})
        resp_script = dict(respostas or {})
        print(f"\n═══ {aula.titulo} ═══")
        n_princ = 0
        while (bloco := est.proximo()) is not None:
            if est.na_principal:
                n_princ += 1
            print(f"{'│' if est.na_principal else '└'} bloco {est.trilha.posicao}")

            if bloco.get("pergunta") and est.na_principal and n_princ in resp_script:
                bloco = {**bloco, "_resp_scriptada": resp_script.pop(n_princ)}
            r = self._toca_bloco(bloco)
            if r is None:
                guardada = self._pega_pendente()
                if guardada:          # falou numa fala de transição; não se perde
                    r = ("barge", guardada)

            gat = None
            if r and r[0] == "barge":
                # F(regra de ouro): sem classificar() bater em ramo nenhum, cair em
                # "por_que" era FINGIR que entendeu — o aluno pode ter dito qualquer
                # coisa. Admitir e seguir é a mentira que a regra única proíbe evitar.
                gat = classificar(r[1], est.aula.ramos)
                print(f'  ✋ "{r[1]}"  →  {gat or "(não reconhecido)"}')
                if not gat:
                    self._fala_guardando("Essa eu não preparei agora — sigo daqui.")
            elif r and r[0] == "resposta":
                dita = r[1]
                pg = bloco["pergunta"]
                senao = pg.get("senao")
                if dita:
                    print(f'  🎤 "{dita}"')
                    achou = classificar(dita, est.aula.ramos)
                    d = dita.lower()
                    acertou = achou == senao or any(k in d for k in pg.get("acerta", []))
                    if acertou and pg.get("confirma"):           # acertou → fading: confirma curto
                        print("  ✓ acertou — pula a derivação (fading)")
                        self._fala_guardando(pg["confirma"])
                        gat = None
                    else:
                        gat = achou or senao
                else:
                    print("  (sem resposta)")
                    gat = senao
                if gat:
                    print(f"  →  {gat}")
            elif est.na_principal and n_princ in script:
                gat = script.pop(n_princ)
                print(f"  ✋ (script) → {gat}")

            if gat:
                self._entra_ramo(est, gat, filler=(not r or r[0] == "barge"))
        print(f"\n■ fim — {est.resumo()}")
        return est

    def _entra_ramo(self, est: EstadoAula, gat: str, *, filler: bool = True) -> None:
        if filler:
            self._fala_guardando(filler_para(gat))
        if not est.entra_ramo(gat):
            self._fala_guardando("Boa pergunta. Deixa eu achar um jeito melhor de mostrar isso.")
            return
        for rb in est.drena_ramo():
            print(f"  └ ramo {est.trilha.posicao}")
            r = self._toca_bloco(rb)
            if r is None:
                guardada = self._pega_pendente()
                if guardada:
                    r = ("barge", guardada)
            if r and r[0] == "barge":
                g2 = classificar(r[1], est.aula.ramos)
                print(f'    ✋ "{r[1]}"  →  {g2 or "(não reconhecido)"}')
                if g2 and g2 != gat:
                    est.sai_ramo()
                    self._entra_ramo(est, g2)
                    return
                if not g2:
                    # mesma regra do toca(): sem classificar, admite em vez de
                    # seguir drenando o ramo como se o aluno não tivesse falado.
                    # Interromper DENTRO de um ramo é o momento mais provável,
                    # porque o ramo é justamente a parte confusa.
                    self._fala_guardando("Essa eu não preparei agora — sigo daqui.")
        self._fala_guardando("Voltando de onde a gente parou.")
        print(f"  ↩  {est.resumo()}")


if __name__ == "__main__":
    from professor.aulas import carregar

    Tocador(pausas=False).toca(carregar("trapezio"),
                               respostas={4: "acho que vira um triângulo"},
                               interrupcoes={6: "por_que_div_2"})
