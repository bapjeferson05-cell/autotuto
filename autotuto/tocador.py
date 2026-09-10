"""tocador.py — o loop. Orquestra uma aula e roda a interrupção de 3 camadas.

É o único módulo que "sabe" da sequência: `falar` / `ouvir` / `desenhar` são
callbacks injetados (Task 14 os liga na voz e no visor). Aqui só decide O QUE
acontece e em que ordem.

A regra única (SPEC §2): **nunca mentir pro aluno**. Se a interrupção não casa
com nenhum ramo preparado, o professor ADMITE (`HONESTO`) e segue de onde parou
— não força um gatilho inexistente, não finge que respondeu.

Interrupção (SPEC §7):
  camada 1  classificador (regex, offline)   -> gatilho existente ou nada
  camada 2  cerebro (LLM curto, opcional)     -> gatilho existente ou nada
  camada 3  fallback honesto                  -> fala HONESTO, não toca o estado

Dependências: `config, estado, classificador, cerebro, figuras.catalogo,
figuras.lousa, calc`. NÃO importa `aulas` (a aula já chega com os ramos
genéricos mergeados por `carregar`/`planeja`).
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from autotuto import calc, cerebro as _cerebro, classificador, config
from autotuto.classificador import classificar
from autotuto.estado import EstadoAula
from autotuto.figuras import lousa
from autotuto.figuras.catalogo import GERADORES

# camada 3: a frase que o professor fala quando não preparou aquilo.
HONESTO = "Essa eu não preparei agora — sigo daqui, e a gente volta nisso."

# beat de pergunta: o aluno diz que não sabe -> a gente acolhe e vai pro `senao`
# (que ENSINA), não trata como erro silencioso.
_NAO_SABE = re.compile(
    r"\b(?:nao sei|sei la|sla|nao faco ideia|nem ideia|nao lembro|"
    r"(?:pode|deve|acho que e) ser|talvez|sei nao|nao manjo)\b"
)

# frase curta de transição ao entrar num ramo (só quando faz sentido — ver
# `filler` em `_entra_ramo`). Banco pequeno, default genérico.
_FILLER = {
    "por_que": "Boa pergunta.",
    "por_que_div_2": "Boa pergunta.",
    "nao_entendi": "Sem problema.",
    "repete": "Claro.",
    "achar_hipotenusa": "Deixa eu ver.",
    "e_triangulo": "Deixa eu ver.",
    "outro_numero": "Deixa eu ver.",
}
_FILLER_DEFAULT = "Deixa eu ver."

_ACOLHE = "Tranquilo não saber — é pra isso que a gente tá aqui. Olha:"
_VOLTA = "Voltando de onde a gente parou."


class Tocador:
    """Toca uma aula, injetando fala/escuta/desenho.

    falar(txt)   -> None se falou e seguiu; str = o aluno interrompeu com isso.
    ouvir(seg)   -> str | None: escuta até `seg`s por uma resposta a `pergunta`.
    desenhar(png, rotulo) -> None.
    cerebro      -> roteador da camada 2 (ou None p/ modo determinístico).
    pausas       -> False zera todos os sleeps (testes / modo texto rápido).
    """

    def __init__(self, falar=None, ouvir=None, desenhar=None, *,
                 cerebro=_cerebro.roteia_interrupcao, pausas=True):
        self.falar = falar or self._falar_padrao
        self.ouvir = ouvir or (lambda seg: None)
        self.desenhar = desenhar or self._desenhar_padrao
        self.cerebro = cerebro
        self.pausas = pausas
        self._falas: list[str] = []   # últimos 3 `diz` — contexto da camada 2
        self._n_png = 0

    # ───────────────────────────────────────────── stubs (quando nada é injetado)
    def _falar_padrao(self, txt: str):
        print(f"[falar] {txt}")
        return None

    def _desenhar_padrao(self, png: bytes, rotulo: str) -> None:
        d = Path("out/tocador")
        d.mkdir(parents=True, exist_ok=True)
        self._n_png += 1
        (d / f"{self._n_png:02d}_{rotulo}.png").write_bytes(png)

    # ───────────────────────────────────────────────────────────────── um beat
    def _toca_bloco(self, bloco: dict):
        """Toca um beat. Devolve:
        ("barge", fala)      -> o aluno interrompeu
        ("resposta", fala|None) -> resposta a um beat de pergunta
        None                 -> seguiu normal
        """
        fig = bloco.get("figura")
        if fig:
            gerador = fig["gerador"]
            if gerador == "figura":
                png = GERADORES["figura"](fig["spec"])
            else:
                png = GERADORES[gerador](**(fig.get("params") or {}))
            self.desenhar(png, gerador)

        if bloco.get("diz"):
            self._falas.append(bloco["diz"])
            del self._falas[:-3]
            # a figura aparece ANTES da fala (SETTLE_S)
            if fig and self.pausas and config.SETTLE_S:
                time.sleep(config.SETTLE_S)
            fala = self.falar(bloco["diz"])
            if fala:
                # responder DURANTE a pergunta conta como a resposta, não interrupção
                return ("resposta" if bloco.get("pergunta") else "barge", fala)

        if bloco.get("pergunta"):
            if "_resp_scriptada" in bloco:
                return ("resposta", bloco["_resp_scriptada"])
            seg = int(bloco["pergunta"].get("escuta_s", 12))
            return ("resposta", self.ouvir(seg))

        if bloco.get("calc"):
            c = bloco["calc"]
            r = calc.CATALOGO[c["gerador"]](**(c.get("params") or {}))
            passos = r.passos if bloco.get("mostra_passos") else r.passos[-1:]
            diz_passos = bloco.get("diz_passos") or []
            for i, latex in enumerate(passos):
                self.desenhar(lousa.passo_latex(latex), f"passo{i + 1}")
                if diz_passos and i < len(diz_passos) and diz_passos[i]:
                    fala = self.falar(diz_passos[i])
                    if fala:
                        return ("barge", fala)
                elif self.pausas:
                    time.sleep(1.1 if i < len(passos) - 1 else 0.7)

        if self.pausas:
            time.sleep(config.PAUSA.get(bloco.get("espera")))
        return None

    # ─────────────────────────────────────────────── as 3 camadas da interrupção
    def _resolve_interrupcao(self, fala: str, est: EstadoAula) -> str | None:
        ramos = est.aula.ramos
        gat = classificar(fala, ramos)                       # camada 1
        if gat or self.cerebro is None:
            return gat
        gat = self.cerebro(fala, " / ".join(self._falas), ramos)   # camada 2
        return gat if gat in ramos else None

    # ─────────────────────────────────────────────────────────────── entra/sai
    def _entra_ramo(self, est: EstadoAula, gat: str, *, filler: bool = True) -> None:
        if filler:
            self.falar(_FILLER.get(gat, _FILLER_DEFAULT))
        if not est.entra_ramo(gat):          # rede de segurança (não deve disparar)
            self.falar(HONESTO)
            return
        for rb in est.drena_ramo():
            r = self._toca_bloco(rb)
            if r and r[0] == "barge":
                g2 = classificar(r[1], est.aula.ramos)
                if g2 and g2 != gat:
                    est.sai_ramo()
                    self._entra_ramo(est, g2)
                    return
        self.falar(_VOLTA)

    # ──────────────────────────────────────────────────────────────────── o loop
    def toca(self, aula, *, interrupcoes: dict[int, str] | None = None,
             respostas: dict[int, str] | None = None) -> EstadoAula:
        est = EstadoAula(aula)
        self._falas = []
        script = dict(interrupcoes or {})       # modo gravação: interrupção por beat
        resp_script = dict(respostas or {})     # modo gravação: resposta por beat
        n_princ = 0

        while (bloco := est.proximo()) is not None:
            if est.na_principal:
                n_princ += 1
            if bloco.get("pergunta") and est.na_principal and n_princ in resp_script:
                bloco = {**bloco, "_resp_scriptada": resp_script.pop(n_princ)}

            r = self._toca_bloco(bloco)
            gat = None

            if r and r[0] == "barge":
                gat = self._resolve_interrupcao(r[1], est)
                if gat is None:                 # camada 3: honesto, sem tocar o estado
                    self.falar(HONESTO)
                    print(f"[tocador] honesto: {r[1]!r} não casou com ramo nenhum")
                else:
                    print(f"[tocador] interrupção {r[1]!r} -> ramo {gat!r}")

            elif r and r[0] == "resposta":
                pg = bloco["pergunta"]
                senao = pg.get("senao")
                dita = r[1]
                if dita and _NAO_SABE.search(classificador._norm(dita)):
                    self.falar(_ACOLHE)         # acolhe e vai pro `senao` (que ensina)
                    gat = senao
                elif dita:
                    achou = classificar(dita, est.aula.ramos)
                    d = classificador._norm(dita)
                    eco = "nao sei" in d or (
                        dita.rstrip().endswith("?")
                        and (" ou " in f" {d} " or "por que" in d or "porque" in d)
                    )
                    acerta = pg.get("acerta") or []
                    if isinstance(acerta, str):
                        acerta = [acerta]
                    acertou = not eco and any(classificador._norm(k) in d for k in acerta)
                    if acertou and pg.get("confirma"):
                        self.falar(pg["confirma"])   # fading: pula a derivação
                        gat = None
                    else:
                        gat = achou or senao
                else:
                    gat = senao                 # calou -> `senao`

            elif est.na_principal and n_princ in script:
                gat = script.pop(n_princ)       # interrupção scriptada (modo gravação)

            if gat:
                self._entra_ramo(est, gat, filler=(not r or r[0] == "barge"))

        return est
