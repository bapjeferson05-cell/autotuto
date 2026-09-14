"""Smoke dos 3 entry points (Task 14).

Só garante que: (1) os módulos importam sem rodar o loop principal;
(2) o roteiro de gravação roda headless e dispara a interrupção scriptada.
"""
import importlib
import json

import pytest

from autotuto.aulas import carregar
from autotuto.tocador import Tocador

ROTEIRO = "roteiros/trapezio.json"


@pytest.mark.parametrize("mod", ["demos.demo_texto", "demos.demo_voz", "demos.demo_roteiro"])
def test_demos_importam(mod):
    # não pode disparar servidor/modelos/loop no import — corpo fica em main().
    importlib.import_module(mod)


def test_roteiro_headless():
    with open(ROTEIRO, encoding="utf-8") as f:
        r = json.load(f)
    est = Tocador(pausas=False, cerebro=None, avaliador=None).toca(
        carregar(r["aula"]),
        interrupcoes={int(k): v for k, v in r.get("interrupcoes", {}).items()},
        respostas={int(k): v for k, v in r.get("respostas", {}).items()},
    )
    assert est.historico  # disparou pelo menos a interrupção scriptada


def test_parece_pergunta_ignora_ruido_e_aceita_pergunta_real():
    from demos.demo_voz import _parece_pergunta

    assert not _parece_pergunta(". . . .")
    assert not _parece_pergunta("")
    assert not _parece_pergunta("uh")
    assert not _parece_pergunta("× ÷ ×")           # símbolos não contam como letra
    assert not _parece_pergunta("Legendado pela comunidade Amara.org")  # alucinação do whisper
    assert _parece_pergunta("por que divide por dois")
    assert _parece_pergunta("quero entender trapézio")
