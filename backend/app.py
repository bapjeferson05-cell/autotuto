"""app.py — API HTTP do AutoTuto: o mesmo professor/ dos demos de voz/terminal,
exposto por request/response pra um frontend web.

    uvicorn backend.app:app --reload      # rodar a partir da raiz do repo

    POST /api/aulas          {"problema": "..."}         -> inicia uma sessão
    POST /api/aulas/{id}/proximo   {"resposta": "..."?}   -> avança um beat
    GET  /api/aulas/{id}/estado                            -> resumo da sessão
"""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.services import sessao as svc_sessao

app = FastAPI(title="AutoTuto API")

_origens = os.environ.get("AUTOTUTO_CORS_ORIGENS", "http://localhost:5173,http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origens.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IniciarIn(BaseModel):
    problema: str


class ProximoIn(BaseModel):
    resposta: str | None = None


@app.post("/api/aulas")
def iniciar(corpo: IniciarIn):
    if not corpo.problema.strip():
        raise HTTPException(400, "problema vazio")
    sid, _sessao, saida = svc_sessao.iniciar_sessao(corpo.problema)
    return {"session_id": sid, **saida}


@app.post("/api/aulas/{session_id}/proximo")
def proximo(session_id: str, corpo: ProximoIn):
    sessao = svc_sessao.SESSOES.get(session_id)
    if sessao is None:
        raise HTTPException(404, "sessão não encontrada")
    return svc_sessao.avanca(sessao, resposta=corpo.resposta)


@app.get("/api/aulas/{session_id}/estado")
def estado(session_id: str):
    sessao = svc_sessao.SESSOES.get(session_id)
    if sessao is None:
        raise HTTPException(404, "sessão não encontrada")
    return {"resumo": sessao.estado.resumo(), "na_principal": sessao.estado.na_principal}


@app.get("/api/saude")
def saude():
    return {"ok": True}
