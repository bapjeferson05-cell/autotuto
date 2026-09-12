"""Testes do planejador — problema (texto) → Aula validada.

Todos usam um `perguntar` fake: NENHUMA chamada de rede real.
"""
import json

from autotuto.aulas import carregar
from autotuto.planejador import _SISTEMA, _exemplo_dirigido, planeja


def test_sistema_so_promete_chaves_de_figura_que_o_canvas_implementa():
    # F6: o prompt prometia `circulos` e `cotas`, que canvas.figura ignora em
    # silêncio. As chaves citadas têm que ser um subconjunto do que é implementado.
    implementadas = {"pontos", "poligonos", "segmentos", "angulos", "marcas", "rotulos"}
    linha = next(l for l in _SISTEMA.splitlines() if "chaves:" in l)
    citadas = {c.strip(" .") for c in linha.split("chaves:")[1].split(",")}
    assert citadas <= implementadas, citadas - implementadas
    assert "circulos" not in _SISTEMA and "cotas" not in _SISTEMA


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


def test_planeja_gerador_de_figura_desconhecido_nao_fica_ok():
    # autópsia 2026-09-12: um plano que valida a FORMA mas pede um gerador de
    # figura que não existe (ex.: o LLM inventou "grafico_barras") saía com
    # rel.ok=True — o contrato mentia. Uma etapa do plano não ia acontecer.
    plano = json.dumps({
        "titulo": "Gráfico", "topico": "grafico_barras", "dados": {},
        "blocos": [{"diz": "olha o gráfico", "figura": {"gerador": "grafico_barras"}}],
        "ramos": {"por_que": [{"diz": "porque sim"}], "nao_entendi": [{"diz": "de novo"}]},
    })
    aula, rel = planeja("interpretação de gráfico", perguntar=lambda m, **k: plano)
    assert aula.blocos                    # a aula continua sendo a gerada (não vira fallback)
    assert not rel.ok                     # mas o relatório não finge que deu tudo certo
    assert any("grafico_barras" in a for a in rel.avisos)


def test_planeja_calc_com_kwarg_invalido_nao_fica_ok():
    # o LLM pode chamar um gerador de verdade com params que não existem na
    # assinatura (kwarg extra) — o Python levanta TypeError, e isso também
    # não pode passar como rel.ok=True.
    plano = json.dumps({
        "titulo": "Ângulos", "topico": "angulos", "dados": {},
        "blocos": [{"diz": "vamos calcular",
                    "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 1, "b": -90, "x": "y"}}}],
        "ramos": {"por_que": [{"diz": "porque sim"}], "nao_entendi": [{"diz": "de novo"}]},
    })
    aula, rel = planeja("ângulos complementares", perguntar=lambda m, **k: plano)
    assert not rel.ok
    assert any("falhou" in a for a in rel.avisos)
