"""Smoke dos 3 entry points (Task 14).

Só garante que: (1) os módulos importam sem rodar o loop principal;
(2) o roteiro de gravação roda headless e dispara a interrupção scriptada.
"""
import importlib
import json

import pytest

from autotuto.aulas import carregar
from autotuto.tocador import Tocador

ROTEIROS = ["roteiros/trapezio.json", "roteiros/fracao.json"]


@pytest.mark.parametrize("mod", ["demos.demo_texto", "demos.demo_voz", "demos.demo_roteiro"])
def test_demos_importam(mod):
    # não pode disparar servidor/modelos/loop no import — corpo fica em main().
    importlib.import_module(mod)


@pytest.mark.parametrize("ROTEIRO", ROTEIROS)
def test_roteiro_headless(ROTEIRO):
    with open(ROTEIRO, encoding="utf-8") as f:
        r = json.load(f)
    est = Tocador(pausas=False, cerebro=None, avaliador=None).toca(
        carregar(r["aula"]),
        interrupcoes={int(k): v for k, v in r.get("interrupcoes", {}).items()},
        respostas={int(k): v for k, v in r.get("respostas", {}).items()},
    )
    assert est.historico  # disparou pelo menos a interrupção scriptada
    # o ramo scriptado tem que existir mesmo (nome errado no JSON viraria
    # fallback honesto silencioso, e o vídeo sairia com o professor se
    # desculpando em vez de explicar)
    for gat in r.get("interrupcoes", {}).values():
        assert gat in carregar(r["aula"]).ramos, (ROTEIRO, gat)


def test_parece_pergunta_ignora_ruido_e_aceita_pergunta_real():
    from demos.demo_voz import _parece_pergunta

    assert not _parece_pergunta(". . . .")
    assert not _parece_pergunta("")
    assert not _parece_pergunta("uh")
    assert not _parece_pergunta("× ÷ ×")           # símbolos não contam como letra
    assert not _parece_pergunta("Legendado pela comunidade Amara.org")  # alucinação do whisper
    assert _parece_pergunta("por que divide por dois")
    assert _parece_pergunta("quero entender trapézio")


def test_bateria_roda_sem_llm_e_conta_os_fallbacks():
    # a régua tem que funcionar offline (planejador sem LLM = tudo fallback) e
    # contar certo — senão ela mede errado justamente quando mais importa
    import demos.bateria as bateria

    chamadas = []

    def morto(m, **k):
        chamadas.append(m)
        raise ConnectionError("sem llm")

    original = bateria.planejador.llm.perguntar
    bateria.planejador.llm.perguntar = morto
    try:
        codigo = bateria.main([])
    finally:
        bateria.planejador.llm.perguntar = original
    assert codigo == 1                       # saiu != 0 porque houve fallback
    assert len(chamadas) == len(bateria.TOPICOS)


def test_bateria_tem_os_11_topicos_do_achado():
    # 4 com aula de ouro, 7 sem — é a composição que expôs o bug
    from autotuto.planejador import _exemplo_dirigido
    import demos.bateria as bateria

    assert len(bateria.TOPICOS) == 11
    sem_pista = sum(_exemplo_dirigido(t) is None for t in bateria.TOPICOS)
    assert sem_pista == 7, sem_pista
