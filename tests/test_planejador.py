"""Testes do planejador — problema (texto) → Aula validada.

Todos usam um `perguntar` fake: NENHUMA chamada de rede real.
"""
import json

from autotuto.aulas import carregar
from autotuto.planejador import _SISTEMA, _exemplo_dirigido, planeja


def test_sistema_so_promete_chaves_de_figura_que_o_canvas_implementa():
    # F6: o prompt prometia `circulos` e `cotas`, que canvas.figura ignorava em
    # silêncio — o LLM pedia um desenho que nunca aparecia. As chaves citadas
    # têm que ser um subconjunto do que é implementado. A lista de implementadas
    # sai do CÓDIGO de `figura()`, não de uma lista à mão que envelhece: quem
    # apagar uma primitiva do canvas sem tirar do prompt derruba este teste.
    import inspect
    import re

    from autotuto.figuras import canvas
    fonte = inspect.getsource(canvas.figura)
    implementadas = set(re.findall(r'spec\.(?:get|setdefault)\("(\w+)"', fonte))
    assert "circulos" in implementadas        # sanity: o regex achou as chaves
    linha = next(l for l in _SISTEMA.splitlines() if "chaves:" in l)
    citadas = {c.strip(" .") for c in linha.split("chaves:")[1].split(",")}
    assert citadas <= implementadas, citadas - implementadas
    assert "cotas" not in _SISTEMA


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
    # assinatura (kwarg extra) — o contrato explícito rejeita ANTES de
    # rodar, e isso também não pode passar como rel.ok=True.
    plano = json.dumps({
        "titulo": "Ângulos", "topico": "angulos", "dados": {},
        "blocos": [{"diz": "vamos calcular",
                    "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 1, "b": -90, "x": "y"}}}],
        "ramos": {"por_que": [{"diz": "porque sim"}], "nao_entendi": [{"diz": "de novo"}]},
    })
    aula, rel = planeja("ângulos complementares", perguntar=lambda m, **k: plano)
    assert not rel.ok
    assert any("argumento desconhecido" in a for a in rel.avisos)


def test_timeout_maior_quando_nao_ha_few_shot_dirigido():
    # autópsia 2026-09-12: sem few-shot (tópico fora das 4 aulas de ouro) o
    # modelo demora mais — não pode usar o timeout curto do caminho feliz.
    from autotuto.config import PLANEJADOR_TIMEOUT_NOVO_S, PLANEJADOR_TIMEOUT_S
    vistos = []

    def fake(m, *, timeout, **k):
        vistos.append(timeout)
        return json.dumps(carregar("trapezio").para_json())

    planeja("me explica o universo", perguntar=fake)   # sem pista -> timeout maior
    assert vistos[-1] == PLANEJADOR_TIMEOUT_NOVO_S

    vistos.clear()
    planeja("resolva 2x - 8 = 0", perguntar=fake)       # bate a pista -> timeout curto
    assert vistos[-1] == PLANEJADOR_TIMEOUT_S


# P1.1 — fixture de regressão: o plano REAL que o qwen2.5:7b gerou na autópsia
# de 2026-09-12 pra "ângulos complementares" (nunca visto antes). O modelo
# entendeu a matemática, escolheu o gerador CERTO (eq_primeiro_grau), mas
# mandou um kwarg que não existe na assinatura (`x`). Fixado aqui pra sempre
# — se isso passar a passar de primeira, é melhoria real, não sorte numa
# pergunta diferente.
_PLANO_ANGULOS_COM_KWARG_INVALIDO = {
    "titulo": "Complementaridade de Ângulos", "topico": "angulos", "dados": {},
    "blocos": [
        {"diz": "Vamos calcular o ângulo complementar de 35 graus.",
         "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 1, "b": -90, "x": "angulo2"}},
         "mostra_passos": True, "diz_passos": ["35 + x = 90", "resolvendo"]},
    ],
    "ramos": {"por_que": [{"diz": "porque sim"}], "nao_entendi": [{"diz": "de novo"}]},
}
_PLANO_ANGULOS_CORRIGIDO = {
    **_PLANO_ANGULOS_COM_KWARG_INVALIDO,
    "blocos": [{**_PLANO_ANGULOS_COM_KWARG_INVALIDO["blocos"][0],
                "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 1, "b": -90}}}],
}


def test_kwarg_invalido_dispara_correcao_e_retry_resolve():
    # P1.1 + contrato explícito: não basta REJEITAR o kwarg extra — o motivo
    # que volta pro LLM precisa ser claro o bastante pra ele produzir a
    # chamada certa da próxima vez (é isso que o teste prova, não só que o
    # schema barrou).
    respostas = iter([json.dumps(_PLANO_ANGULOS_COM_KWARG_INVALIDO),
                      json.dumps(_PLANO_ANGULOS_CORRIGIDO)])
    mandados = []

    def fake(m, **k):
        mandados.append(m[-1]["content"])   # a última msg = a instrução de correção
        return next(respostas)

    aula, rel = planeja("ângulos complementares", perguntar=fake, tentativas=2)
    assert rel.ok and not rel.avisos                   # corrigiu e ficou limpo
    motivo = mandados[-1]
    assert "eq_primeiro_grau" in motivo and "'x'" in motivo   # qual gerador, qual chave sobrando
    assert "a, b" in motivo                                   # e o que É aceito — não só "deu erro"


def test_kwarg_invalido_sem_correcao_esgota_tentativas_mas_nao_troca_de_assunto():
    # o modelo insiste no mesmo erro em toda tentativa. Perder o passo de UMA
    # conta é bem menos ruim pro aluno que o professor virar pra outro
    # assunto (trapézio) sem avisar — a forma validou, só uma ferramenta
    # falhou. Aceita o candidato mesmo assim; rel.ok=False conta a verdade.
    aula, rel = planeja("ângulos complementares", tentativas=2,
                        perguntar=lambda m, **k: json.dumps(_PLANO_ANGULOS_COM_KWARG_INVALIDO))
    assert not rel.ok
    assert aula.titulo == "Complementaridade de Ângulos"   # não virou trapézio
    assert any("argumento desconhecido" in a for a in rel.avisos)


def test_exemplo_literal_do_usuario_fluxo_completo_de_correcao():
    # eq_primeiro_grau(a=35, b=90, x=35) -> REJEITADO -> LLM recebe o erro ->
    # eq_primeiro_grau(a=35, b=90) -> EXECUTA. De ponta a ponta, determinístico.
    ruim = json.dumps({
        "titulo": "t", "topico": "t", "dados": {},
        "blocos": [{"diz": "x", "calc": {"gerador": "eq_primeiro_grau",
                                        "params": {"a": 35, "b": 90, "x": 35}}}],
        "ramos": {"por_que": [{"diz": "y"}], "nao_entendi": [{"diz": "z"}]},
    })
    bom = json.dumps({
        "titulo": "t", "topico": "t", "dados": {},
        "blocos": [{"diz": "x", "calc": {"gerador": "eq_primeiro_grau",
                                        "params": {"a": 35, "b": 90}}}],
        "ramos": {"por_que": [{"diz": "y"}], "nao_entendi": [{"diz": "z"}]},
    })
    respostas = iter([ruim, bom])
    corrigido_recebido = []

    def fake(m, **k):
        corrigido_recebido.append(m[-1]["content"])
        return next(respostas)

    aula, rel = planeja("qualquer coisa", perguntar=fake, tentativas=2)
    assert rel.ok and not rel.avisos                          # EXECUTOU limpo
    assert "argumento desconhecido" in corrigido_recebido[-1]  # o LLM recebeu o motivo
    assert "'x'" in corrigido_recebido[-1]
