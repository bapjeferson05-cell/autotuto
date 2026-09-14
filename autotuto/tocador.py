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

import os
import random
import re
import sys
import time
from pathlib import Path

from autotuto import (avaliador as _avaliador, calc, cerebro as _cerebro,
                      classificador, config, fala_formula)
from autotuto.classificador import classificar
from autotuto.estado import EstadoAula
from autotuto.figuras import lousa
from autotuto.figuras.catalogo import GERADORES

# log de debug pro stdout só quando AUTOTUTO_LOG=1 (senão polui a gravação/os testes).
_LOG = os.environ.get("AUTOTUTO_LOG") == "1"


def _log(msg: str) -> None:
    if _LOG:
        print(msg)


# camada 3: a frase que o professor fala quando não preparou aquilo.
HONESTO = "Essa eu não preparei agora — sigo daqui, e a gente volta nisso."

# quando uma FERRAMENTA falta (gerador inexistente) ou quebra com os params
# que o plano mandou: a etapa correspondente simplesmente não acontece — o
# aluno não pode ficar ouvindo o professor descrever uma figura que nunca
# aparece, ou ficar sem saber que um número não foi calculado. Falado, não só
# logado (autópsia de 2026-09-12: hoje isso só ia pro stderr, em silêncio).
LIMITACAO_VISUAL = "Entendi o que você quer, mas ainda não consigo desenhar essa parte — sigo explicando sem a figura."
LIMITACAO_CALC = "Entendi o que você quer calcular, mas ainda não tenho essa conta pronta — sigo sem o número exato."

# beat de pergunta: o aluno diz que não sabe -> a gente acolhe e vai pro `senao`
# (que ENSINA), não trata como erro silencioso.
_NAO_SABE = re.compile(
    r"\b(?:nao sei|sei la|sla|nao faco ideia|nem ideia|nao lembro|"
    r"(?:pode|deve|acho que e) ser|talvez|sei nao|nao manjo)\b"
)

# frase curta de transição ao entrar num ramo (só quando faz sentido — ver
# `filler` em `_entra_ramo`). Banco pequeno, default genérico.
# 2-3 variações por gatilho — sorteadas (não a mesma frase toda vez que o aluno
# interrompe com o mesmo tipo de dúvida).
_FILLER = {
    "por_que": ("Boa pergunta.", "Ótima pergunta.", "Show, vamos nessa."),
    "por_que_div_2": ("Boa pergunta.", "Ótima pergunta.", "Faz sentido perguntar isso."),
    "nao_entendi": ("Sem problema.", "Tranquilo.", "Calma, vamos de novo."),
    "repete": ("Claro.", "Sem problema, de novo.", "Pode deixar."),
    "achar_hipotenusa": ("Deixa eu ver.", "Boa.", "Olha só."),
    "e_triangulo": ("Deixa eu ver.", "Boa.", "Olha só."),
    "outro_numero": ("Deixa eu ver.", "Boa.", "Olha só."),
    "comeca_pelo_de_baixo": ("Boa.", "Olha só.", "Deixa eu mostrar."),
    "e_se_outro_corte": ("Boa pergunta.", "Olha só.", "Ótima ideia."),
    "e_se_metade": ("Claro.", "Boa.", "Olha só."),
}
_FILLER_DEFAULT = ("Deixa eu ver.", "Um instante.", "Peraí.")


def _filler(gat: str, evitar: str | None = None) -> str:
    """Frase curta de transição, sorteada — mas nunca a MESMA que a anterior.

    Medido: com banco de 3 frases e sorteio com reposição, 33% das vezes o
    professor falava a frase idêntica duas vezes seguidas ("Boa pergunta." /
    "Boa pergunta."). Acontece de verdade no caso F3 (aluno re-pergunta o ramo
    que já está rolando) e na troca de ramo, que falam dois fillers seguidos.
    """
    opcoes = _FILLER.get(gat, _FILLER_DEFAULT)
    restantes = [f for f in opcoes if f != evitar] or list(opcoes)
    return random.choice(restantes)

_ACOLHE = "Tranquilo não saber — é pra isso que a gente tá aqui. Olha:"
_VOLTA = "Voltando de onde a gente parou."
# P1.2: o avaliador semântico (LLM) disse "parcial" — reconhece o pedaço certo
# antes de completar (não tratar como erro silencioso, mas também não fingir
# que fechou a ideia inteira).
_PARCIAL = "Você chegou perto — parte disso já tá certa. Deixa eu completar:"


class Tocador:
    """Toca uma aula, injetando fala/escuta/desenho.

    falar(txt)   -> None se falou e seguiu; str = o aluno interrompeu com isso.
    ouvir(seg)   -> str | None: escuta até `seg`s por uma resposta a `pergunta`.
    desenhar(png, rotulo) -> None.
    cerebro      -> roteador da camada 2 (ou None p/ modo determinístico).
    avaliador    -> avaliador semântico de resposta, P1.2 (ou None p/ modo
                    determinístico — só substring/número, sem LLM).
    pausas       -> False zera todos os sleeps (testes / modo texto rápido).
    """

    def __init__(self, falar=None, ouvir=None, desenhar=None, *,
                 cerebro=_cerebro.roteia_interrupcao,
                 avaliador=_avaliador.avalia_resposta, pausas=True):
        self.falar = falar or self._falar_padrao
        self.ouvir = ouvir or (lambda seg: None)
        self.desenhar = desenhar or self._desenhar_padrao
        self.cerebro = cerebro
        self.avaliador = avaliador
        self.pausas = pausas
        self._falas: list[str] = []   # últimos 3 `diz` — contexto da camada 2
        self._n_png = 0
        self._ultimo_filler: str | None = None

    # ───────────────────────────────────────────── stubs (quando nada é injetado)
    def _falar_padrao(self, txt: str):
        _log(f"[falar] {txt}")
        return None

    def _desenhar_padrao(self, png: bytes, rotulo: str) -> None:
        d = Path("out/tocador")
        d.mkdir(parents=True, exist_ok=True)
        self._n_png += 1
        (d / f"{self._n_png:02d}_{rotulo}.png").write_bytes(png)

    # ───────────────────────────────────────────────────────────────── um beat
    def _toca_bloco(self, bloco: dict, *, retomar: bool = False, desde: int = 0):
        """Toca um beat. Devolve:
        ("barge", fala)      -> o aluno interrompeu durante o `diz`
        ("barge", fala, i)   -> interrompeu durante o passo `i` do `calc`
        ("resposta", fala|None) -> resposta a um beat de pergunta
        None                 -> seguiu normal

        `retomar=True`: o beat foi interrompido durante o `diz` e a gente já
        voltou do ramo. Pula a figura (já está na tela) e o `diz` (já foi dito),
        e roda SÓ o `calc` (com o `diz_passos`) + o `espera` — pra fórmula/conta
        do beat não sumir. Ver F1.

        `desde`: no replay do `calc`, começa do passo `desde` — os passos antes
        dele o aluno já viu E ouviu antes de interromper, não repete (F4).
        """
        fig = bloco.get("figura")
        # F7: aula do LLM pode mandar `figura` como string crua em vez de objeto —
        # o schema hoje deixa passar. Sem este guarda, `fig["gerador"]` estoura
        # TypeError e o `print` do except estoura AttributeError e derruba `toca()`.
        if fig and not retomar and not isinstance(fig, dict):
            print("[tocador] figura não é um objeto, pulando", file=sys.stderr)
            fig = None
        if fig and not retomar:
            try:
                gerador = fig["gerador"]
                if gerador == "figura":
                    png = GERADORES["figura"](fig["spec"])
                else:
                    png = GERADORES[gerador](**(fig.get("params") or {}))
                self.desenhar(png, gerador)
            except Exception as e:  # gerador desconhecido / params ruins numa aula do LLM
                print(f"[tocador] figura {fig!r} falhou, pulando: {e!r}",
                      file=sys.stderr)
                self.falar(LIMITACAO_VISUAL)

        if bloco.get("diz") and not retomar:
            self._falas.append(bloco["diz"])
            del self._falas[:-3]
            # a figura aparece ANTES da fala (SETTLE_S)
            if fig and self.pausas and config.SETTLE_S:
                time.sleep(config.SETTLE_S)
            fala = self.falar(bloco["diz"])
            if fala:
                # responder DURANTE a pergunta conta como a resposta, não interrupção
                return ("resposta" if bloco.get("pergunta") else "barge", fala)

        if bloco.get("pergunta") and not retomar:
            if not bloco.get("diz"):
                # nada foi perguntado em voz alta (schema já rejeita isso no
                # caminho do LLM, mas o tocador não pode confiar só nisso —
                # uma aula de ouro ou um roteiro escrito à mão pode ter o
                # mesmo erro). Sem isso, ficaria "escutando" uma pergunta que
                # nunca fez — o aluno esperando resposta pra um silêncio.
                print("[tocador] beat 'pergunta' sem 'diz' — pulando (nada foi perguntado)",
                      file=sys.stderr)
            elif "_resp_scriptada" in bloco:
                return ("resposta", bloco["_resp_scriptada"])
            else:
                seg = int(bloco["pergunta"].get("escuta_s", 12))
                return ("resposta", self.ouvir(seg))

        c = bloco.get("calc")
        # F7: mesmo caso da figura — `calc` pode chegar como string crua.
        if c and not isinstance(c, dict):
            print("[tocador] calc não é um objeto, pulando", file=sys.stderr)
            c = None
        if c:
            try:
                r = calc.CATALOGO[c["gerador"]](**(c.get("params") or {}))
            except Exception as e:  # gerador desconhecido / params ruins numa aula do LLM
                print(f"[tocador] calc {c!r} falhou, pulando: {e!r}",
                      file=sys.stderr)
                self.falar(LIMITACAO_CALC)
                r = None
            if r is not None:
                # sem `mostra_passos`, só o ÚLTIMO passo vai pra lousa — mas o
                # índice tem que continuar sendo o índice REAL dele. Fatiar com
                # [-1:] rebobinava o i pra 0 e o professor narrava `diz_passos[0]`
                # ("essa é a fórmula geral") enquanto a lousa mostrava o resultado:
                # a fala dizendo uma coisa e o desenho outra.
                diz_passos = bloco.get("diz_passos") or []
                ultimo = len(r.passos) - 1
                indices = range(len(r.passos)) if bloco.get("mostra_passos") else [ultimo]
                for i in indices:
                    if i < desde:          # já visto+ouvido antes do barge — não repete
                        continue
                    self.desenhar(lousa.passo_latex(r.passos[i]), f"passo{i + 1}")
                    # 1º a narração escrita (a palavra do autor sempre vence);
                    # 2º a leitura automática da fórmula; 3º silêncio com pausa.
                    narracao = (diz_passos[i]
                                if diz_passos and i < len(diz_passos) and diz_passos[i]
                                else fala_formula.fala(r.passos[i]))
                    if narracao:
                        fala = self.falar(narracao)
                        if fala:
                            return ("barge", fala, i)
                    elif self.pausas:
                        time.sleep(config.PASSO_S if i < ultimo else config.PASSO_FINAL_S)

        if self.pausas:
            time.sleep(config.PAUSA.get(bloco.get("espera"), config.PAUSA[None]))
        return None

    def _diz_filler(self, gat: str) -> str:
        """`_filler` lembrando o que foi dito da última vez — dois fillers
        seguidos (troca de ramo, ou F3) não podem sair iguais."""
        f = _filler(gat, evitar=self._ultimo_filler)
        self._ultimo_filler = f
        return f

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
        if not est.entra_ramo(gat):          # rede de segurança (não deve disparar)
            self.falar(HONESTO)
            return
        # filler só depois de saber que o ramo existe (senão o aluno ouviria
        # "Deixa eu ver." e logo em seguida "Essa eu não preparei...").
        if filler:
            self.falar(self._diz_filler(gat))
        for rb in est.drena_ramo():
            r = self._toca_bloco(rb)
            # beat de dentro do ramo interrompido no `diz` que TAMBÉM tem `calc`:
            # se a gente continuar drenando ESTE MESMO ramo (não trocar de ramo),
            # reexecuta só o calc depois — senão a conta some e o "_VOLTA" no fim
            # do laço mente que retomou de onde parou (mesmo bug do F1/F4, só que
            # essa cópia do replay nunca existiu aqui).
            retomar_calc = bool(r and r[0] == "barge" and rb.get("calc"))
            if r and r[0] == "barge":
                # mesma política da trilha principal: as 3 camadas, e honesto se
                # nada casar — nunca ignorar o aluno em silêncio (F2).
                g2 = self._resolve_interrupcao(r[1], est)
                if g2 and g2 != gat:
                    est.sai_ramo()
                    self._entra_ramo(est, g2)
                    return
                elif g2 == gat:
                    # F3: o aluno re-pergunta o mesmo ramo que já está rolando.
                    # Não re-entra (loop); reconhece e segue drenando — nunca
                    # ignorar o aluno em silêncio (SPEC §7).
                    self.falar(self._diz_filler(gat))
                elif g2 is None:
                    self.falar(HONESTO)
                if retomar_calc:
                    desde = r[2] + 1 if len(r) > 2 else 0
                    r2 = self._toca_bloco(rb, retomar=True, desde=desde)
                    if r2 and r2[0] == "barge":
                        self.falar(HONESTO)
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
            # beat interrompido no `diz` que TAMBÉM tem `calc`: depois do ramo a
            # gente reexecuta só o calc, senão a fórmula some (F1).
            retomar_calc = bool(r and r[0] == "barge" and bloco.get("calc"))

            if r and r[0] == "barge":
                gat = self._resolve_interrupcao(r[1], est)
                if gat is None:                 # camada 3: honesto, sem tocar o estado
                    self.falar(HONESTO)
                    _log(f"[tocador] honesto: {r[1]!r} não casou com ramo nenhum")
                else:
                    _log(f"[tocador] interrupção {r[1]!r} -> ramo {gat!r}")

            elif r and r[0] == "resposta":
                pg = bloco["pergunta"]
                senao = pg.get("senao")
                dita = r[1]
                if dita:
                    achou = classificar(dita, est.aula.ramos)
                    d = classificador._norm(dita)
                    eco = "nao sei" in d or (
                        dita.rstrip().endswith("?")
                        and (" ou " in f" {d} " or "por que" in d or "porque" in d)
                    )
                    acerta = pg.get("acerta") or []
                    if isinstance(acerta, str):
                        acerta = [acerta]
                    # P1 (autópsia 2026-09-12): "4", "quatro" e "o mdc é 4" são a
                    # MESMA resposta — substring de frase não enxerga isso. Se um
                    # item de 'acerta' carrega número, compara o número da fala do
                    # aluno com ele (dígito ou por extenso), não só o texto.
                    acertou = not eco and any(
                        classificador._norm(k) in d
                        or classificador.mesma_resposta_numerica(k, dita)
                        for k in acerta)
                    # P1.2 (autópsia 2026-09-12): os crivos acima são substring/
                    # número — não enxergam uma resposta certa ou parcialmente
                    # certa DITA COM OUTRAS PALAVRAS. Só entra o avaliador (LLM)
                    # quando os dois já disseram "não bateu" e vale a pena gastar
                    # a chamada — nunca quando já acertou, é eco, ou é "não sei"
                    # (F8 continua tratando isso antes, sem depender do LLM).
                    veredito = None
                    if (not acertou and not eco and acerta and self.avaliador
                            and not _NAO_SABE.search(d)):
                        veredito = self.avaliador(bloco["diz"], acerta, dita)
                    if (acertou or veredito == "certo") and pg.get("confirma"):
                        self.falar(pg["confirma"])   # fading: pula a derivação
                        gat = None
                    elif _NAO_SABE.search(d):
                        # só depois de descartar o acerto: acolhe e vai pro `senao`
                        # (que ENSINA) — um acerto hedgeado NÃO é "não saber" (F8).
                        self.falar(_ACOLHE)
                        gat = senao
                    elif veredito == "parcial":
                        # reconhece o pedaço certo antes de ensinar o resto —
                        # nunca tratar acerto parcial como erro silencioso.
                        self.falar(_PARCIAL)
                        gat = senao
                    else:
                        gat = achou or senao
                else:
                    gat = senao                 # calou -> `senao`

            elif est.na_principal and n_princ in script:
                gat = script.pop(n_princ)       # interrupção scriptada (modo gravação)

            if gat:
                self._entra_ramo(est, gat, filler=(not r or r[0] == "barge"))
            if retomar_calc:
                # F4: se o barge foi durante o `calc`, o replay começa do passo
                # seguinte — não relê o que o aluno já ouviu.
                desde = r[2] + 1 if len(r) > 2 else 0
                r2 = self._toca_bloco(bloco, retomar=True, desde=desde)
                if r2 and r2[0] == "barge":
                    # F2/F4: interrompeu DE NOVO durante a retomada. Um nível de
                    # recuperação basta — ack honesto e a aula segue (sem recursão).
                    self.falar(HONESTO)

        return est
