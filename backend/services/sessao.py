"""sessao.py — a Aula pra HTTP: um passo por request, sem bloquear.

Reusa `professor/` inteiro (planejador, EstadoAula, o catálogo de geradores) — não
reimplementa nada da pedagogia. A diferença pro `professor/tocador.py` (feito pra
voz/terminal, com `falar`/`ouvir` bloqueantes) é só a orquestração: aqui cada chamada
de `avanca()` devolve UM beat renderizado, e quem decide quando pedir o próximo é o
cliente HTTP (o frontend), não um loop local.

    sessao = iniciar_sessao(problema)
    saida = sessao["beat_atual"]          # primeiro beat, já pronto
    saida = avanca(sessao, resposta=None) # sem resposta: só continua
    saida = avanca(sessao, resposta="por que divide por dois?")  # interrompe
    saida = avanca(sessao, resposta="vira um triângulo")         # responde uma 'pergunta'
"""
from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass, field
from typing import Any

from professor import planejador
from professor.aulas import disponiveis
from professor.classificador import classificar, normalizar
from professor.esquema import GERADORES
from professor.estado import EstadoAula

_FALLBACK_RAMO = "Boa pergunta — deixa eu achar um jeito melhor de mostrar isso."
_NAO_PREPAREI = "Essa eu não preparei agora — sigo daqui."


@dataclass
class Sessao:
    estado: EstadoAula
    bloco_atual: dict | None = None
    avisos: list[str] = field(default_factory=list)


SESSOES: dict[str, Sessao] = {}


def _renderiza_figura(fig: dict) -> str:
    gerador = GERADORES[fig["gerador"]]
    png = (gerador.fn(fig.get("spec", {})) if fig["gerador"] == "figura"
           else gerador.fn(**(fig.get("params") or {})))
    return base64.b64encode(png).decode("ascii")


def _renderiza_bloco(bloco: dict) -> dict[str, Any]:
    saida: dict[str, Any] = {
        "fim": False,
        "diz": bloco.get("diz"),
        "tem_pergunta": bool(bloco.get("pergunta")),
    }
    # Um gerador que estoura (params crus do LLM, ex.: "18" em vez de 18) virava
    # HTTP 500 — e, como o beat já tinha sido consumido, o retry do cliente pulava
    # ele e a aula seguia sem a conta. Aqui o beat continua, sem fingir que
    # desenhou: o aluno é avisado de que a figura/conta não saiu.
    if bloco.get("figura"):
        try:
            saida["figura_png_base64"] = _renderiza_figura(bloco["figura"])
        except Exception as e:  # noqa: BLE001
            saida["falhou"] = f"a figura deste passo não pôde ser desenhada ({e})"
    if bloco.get("calc"):
        c = bloco["calc"]
        try:
            r = GERADORES[c["gerador"]].fn(**(c.get("params") or {}))
        except Exception as e:  # noqa: BLE001
            saida["falhou"] = f"a conta deste passo não pôde ser feita ({e})"
            return saida
        saida["passos_latex"] = r.passos if bloco.get("mostra_passos") else r.passos[-1:]
        saida["valor"] = r.valor
        # diz_passos é o "worked example": uma frase por linha da conta. O tocador
        # de voz narra cada uma; aqui era descartado e o aluno via álgebra muda.
        if bloco.get("diz_passos"):
            saida["diz_passos"] = list(bloco["diz_passos"])
    return saida


def _renderiza_extra(diz: str) -> dict[str, Any]:
    return {"fim": False, "diz": diz, "tem_pergunta": False}


def iniciar_sessao(problema: str) -> tuple[str, Sessao, dict]:
    """Planeja a aula e devolve (session_id, Sessao, primeiro beat renderizado)."""
    aula, rel = planejador.planeja(problema, verbose=False)

    # rel.fatais = "a aula que eu devolvi NÃO é sobre o que você pediu" (LLM fora do
    # ar -> plano offline, que é a aula de ouro do trapézio). Servir isso como
    # resposta é a mesma mentira que o cli.py já recusa — e aqui era pior, porque é
    # o caminho que o README anuncia com `docker compose up`, e o único rastro era
    # um campo JSON que nenhum componente do frontend renderiza.
    if rel.fatais:
        est = EstadoAula(aula)
        sessao = Sessao(estado=est, bloco_atual=None, avisos=rel.fatais)
        sid = uuid.uuid4().hex
        SESSOES[sid] = sessao
        return sid, sessao, {
            "fim": True,
            "recusa": True,
            "diz": ("Não consegui montar uma aula sobre isso agora — não tenho o "
                    "modelo disponível aqui. Não vou te empurrar outra aula no lugar."),
            "aulas_prontas": disponiveis(),
            "avisos_planejador": rel.fatais + rel.avisos,
        }

    est = EstadoAula(aula)
    bloco = est.proximo()
    sessao = Sessao(estado=est, bloco_atual=bloco)
    sid = uuid.uuid4().hex
    SESSOES[sid] = sessao

    saida = _renderiza_bloco(bloco) if bloco else {"fim": True, "resumo": est.resumo()}
    saida["titulo"] = aula.titulo
    saida["topico"] = aula.topico
    if rel.avisos:
        saida["avisos_planejador"] = rel.avisos
    return sid, sessao, saida


def _entra_num_ramo(sessao: Sessao, gatilho: str) -> dict[str, Any] | None:
    """Empilha o ramo do gatilho e devolve o primeiro beat dele — ou None se o
    gatilho não existir na aula (quem chama decide o fallback)."""
    blocos = sessao.estado.entra_ramo(gatilho)
    if not blocos:
        return None
    bloco = sessao.estado.proximo()
    sessao.bloco_atual = bloco
    return _renderiza_bloco(bloco) if bloco else None


def avanca(sessao: Sessao, resposta: str | None = None) -> dict[str, Any]:
    est = sessao.estado
    bloco_ant = sessao.bloco_atual
    resposta = (resposta or "").strip()

    # 1) o beat anterior era uma 'pergunta' esperando resposta do aluno — silêncio
    # conta como resposta errada (vai pro ramo 'senao'), igual ao Tocador original
    if bloco_ant and bloco_ant.get("pergunta"):
        pg = bloco_ant["pergunta"]
        senao = pg.get("senao")
        if resposta:
            achou = classificar(resposta, est.aula.ramos)
            # `achou == senao` contava como ACERTO: como `senao` costuma ser o ramo
            # de remediação (por_que), quem respondia "por quê?" — ou seja, admitia
            # não saber — era parabenizado e tinha a derivação pulada. Acerto é só
            # bater nas palavras de `acerta`.
            dita = normalizar(resposta)
            acertou = any(normalizar(k) in dita for k in pg.get("acerta", []))
            if acertou and pg.get("confirma"):
                # fading: confirma curto, PULA a derivação — não entra em ramo
                sessao.bloco_atual = None
                return _renderiza_extra(pg["confirma"])
            gat = achou or senao
        else:
            gat = senao
        saida = _entra_num_ramo(sessao, gat) if gat else None
        if saida is None:
            sessao.bloco_atual = None
            return _renderiza_extra(_FALLBACK_RAMO)
        return saida

    # 2) o aluno interrompeu com uma pergunta espontânea (não era beat de pergunta)
    if resposta:
        # Sem classificar em ramo nenhum, cair em "por_que" era FINGIR que entendeu:
        # o aluno pode ter dito qualquer coisa e levava a explicação de uma pergunta
        # que não fez. Admite e segue de onde estava — a mesma regra do tocador.
        gat = classificar(resposta, est.aula.ramos)
        if not gat:
            sessao.bloco_atual = None
            return _renderiza_extra(_NAO_PREPAREI)
        # só desempilha o ramo atual DEPOIS de saber que há pra onde ir: antes,
        # um gatilho que não existia jogava fora o resto da explicação em que o
        # aluno estava e devolvia só o pedido de desculpas genérico.
        if not est.na_principal:
            est.sai_ramo()
        saida = _entra_num_ramo(sessao, gat)
        if saida is None:
            sessao.bloco_atual = None
            return _renderiza_extra(_FALLBACK_RAMO)
        return saida

    # 3) sem resposta: só continua a trilha atual (drena o ramo, depois retoma a principal)
    bloco = est.proximo()
    # `if` desempilhava UM nível só: com ramo dentro de ramo (um beat de pergunta
    # dentro de um ramo empilha o segundo), a aula era declarada encerrada com a
    # trilha principal ainda cheia — e o frontend tira o formulário no `fim`, então
    # a sessão morria sem volta.
    while bloco is None and not est.na_principal:
        est.sai_ramo()
        bloco = est.proximo()
    sessao.bloco_atual = bloco
    if bloco is None:
        return {"fim": True, "resumo": est.resumo()}
    return _renderiza_bloco(bloco)
