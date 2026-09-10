"""Testes do planejador — problema (texto) → Aula validada.

Todos usam um `perguntar` fake: NENHUMA chamada de rede real.
"""
import json

from autotuto.aulas import carregar
from autotuto.planejador import _exemplo_dirigido, planeja


def test_pista_de_equacao():
    # regex de equação (\b\d*x\s*[-+=]) e a palavra "resolva" → aula de ouro certa
    assert json.loads(_exemplo_dirigido("resolva 2x - 8 = 0"))["topico"] == "eq_primeiro_grau"
    assert json.loads(_exemplo_dirigido("x + 5 = 12"))["topico"] == "eq_primeiro_grau"


def test_pista_regra_de_tres():
    dirigido = _exemplo_dirigido("se 3 cadernos custam 24, quanto custam 5")
    assert json.loads(dirigido)["topico"] == "regra_de_tres"


def test_sem_pista_e_none():
    assert _exemplo_dirigido("me explica o universo") is None


def test_planeja_valida_e_corrige():
    ruim = json.dumps({"titulo": "x", "blocos": [{}], "ramos": {}})  # bloco vazio
    bom = json.dumps(carregar("trapezio").para_json())
    respostas = iter([ruim, bom])
    aula, rel = planeja("área de um trapézio", perguntar=lambda m, **k: next(respostas))
    assert rel.ok and aula.blocos


def test_sem_llm_cai_no_trapezio():
    def morto(m, **k):
        raise ConnectionError()

    aula, rel = planeja("qualquer coisa", perguntar=morto)
    assert aula.titulo == carregar("trapezio").titulo and not rel.ok
