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


def test_os_demos_convidam_o_aluno_a_interromper():
    # relato de uso real: a pessoa falou em voz alta, o professor seguiu por
    # cima (BARGE_IN=0 por padrão) e a experiência virou "mais um vídeo, só que
    # ao vivo". A interrupção é a razão de existir do projeto e o aluno não tem
    # como adivinhar que ela existe — então o professor convida, em voz alta.
    import pathlib

    from autotuto import config

    for arq in ("demos/demo_texto.py", "demos/demo_voz.py"):
        fonte = pathlib.Path(arq).read_text()
        assert "CONVITE_INTERRUPCAO" in fonte, arq
        assert "convidou = True" in fonte, arq          # uma vez só
    # o convite tem que ensinar as teclas que existem de verdade
    from autotuto.visor import _TECLAS
    for tecla in ("1", "2", "4"):
        assert tecla in config.CONVITE_INTERRUPCAO
        assert tecla in _TECLAS


def test_demos_nao_pedem_desculpa_duas_vezes_pelo_fallback():
    # a AULA_SEM_PLANO já diz em voz alta que não deu; o demo repetir vira
    # desculpa em dobro antes da mesma frase.
    import pathlib
    for arq in ("demos/demo_texto.py", "demos/demo_voz.py"):
        assert "já tenho pronta" not in pathlib.Path(arq).read_text(), arq
