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
from professor.classificador import classificar
from professor.esquema import GERADORES
from professor.estado import EstadoAula

_FALLBACK_RAMO = "Boa pergunta — deixa eu achar um jeito melhor de mostrar isso."


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
    if bloco.get("figura"):
        saida["figura_png_base64"] = _renderiza_figura(bloco["figura"])
    if bloco.get("calc"):
        c = bloco["calc"]
        r = GERADORES[c["gerador"]].fn(**(c.get("params") or {}))
        saida["passos_latex"] = r.passos if bloco.get("mostra_passos") else r.passos[-1:]
        saida["valor"] = r.valor
    return saida


def _renderiza_extra(diz: str) -> dict[str, Any]:
    return {"fim": False, "diz": diz, "tem_pergunta": False}


def iniciar_sessao(problema: str) -> tuple[str, Sessao, dict]:
    """Planeja a aula e devolve (session_id, Sessao, primeiro beat renderizado)."""
    aula, rel = planejador.planeja(problema, verbose=False)
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
            acertou = achou == senao or any(k in resposta.lower() for k in pg.get("acerta", []))
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
        if not est.na_principal:
            est.sai_ramo()   # troca de ramo, não empilha (mesma regra do Tocador)
        gat = classificar(resposta, est.aula.ramos) or "por_que"
        saida = _entra_num_ramo(sessao, gat)
        if saida is None:
            sessao.bloco_atual = None
            return _renderiza_extra(_FALLBACK_RAMO)
        return saida

    # 3) sem resposta: só continua a trilha atual (drena o ramo, depois retoma a principal)
    bloco = est.proximo()
    if bloco is None and not est.na_principal:
        est.sai_ramo()
        bloco = est.proximo()
    sessao.bloco_atual = bloco
    if bloco is None:
        return {"fim": True, "resumo": est.resumo()}
    return _renderiza_bloco(bloco)
