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


def test_sem_llm_admite_em_vez_de_trocar_de_assunto():
    # ANTES: sem LLM o fallback era a aula de ouro do TRAPÉZIO — o aluno pedia
    # porcentagem e o professor começava a falar de terreno, calado. Trocar de
    # assunto sem avisar é a mentira que a regra única do projeto proíbe.
    def morto(m, **k):
        raise ConnectionError()

    aula, rel = planeja("quanto é 15 por cento de 80", perguntar=morto)
    assert not rel.ok and rel.erros
    assert aula.titulo != carregar("trapezio").titulo
    assert aula.topico == "sem_plano"
    # e o aluno TEM que ouvir isso, não só o log do dev
    tudo = " ".join(b.get("diz", "") for b in aula.blocos).lower()
    assert "nao consegui" in tudo or "não consegui" in tudo
    # nada de matemática de outro assunto na boca do professor
    assert "trapezio" not in tudo and "trapézio" not in tudo


def test_fallback_ainda_tem_pra_onde_ir_se_o_aluno_interromper():
    def morto(m, **k):
        raise ConnectionError()

    aula, _ = planeja("qualquer coisa", perguntar=morto)
    assert {"por_que", "nao_entendi", "repete"} <= set(aula.ramos)


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


def test_timeout_e_o_mesmo_nos_dois_caminhos():
    # O par curto/longo (45s com pista, 100s sem) nasceu quando "sem pista"
    # queria dizer "sem exemplo nenhum". Depois que todo problema passou a levar
    # exemplo, a relação INVERTEU: o dirigido é o de prompt MAIOR, e ficou com o
    # teto CURTO. A bateria de 2026-09-15 mostrou na cara — os 3 únicos
    # fracassos foram tópicos COM aula de ouro, todos em 45.0s cravados,
    # enquanto os genéricos passavam em ~20s com o teto de 100s.
    from autotuto.config import PLANEJADOR_TIMEOUT_S
    vistos = []

    def fake(m, *, timeout, **k):
        vistos.append(timeout)
        return json.dumps(carregar("trapezio").para_json())

    planeja("me explica o universo", perguntar=fake)    # sem pista
    planeja("resolva 2x - 8 = 0", perguntar=fake)        # com pista
    assert vistos == [PLANEJADOR_TIMEOUT_S, PLANEJADOR_TIMEOUT_S]


def test_o_caminho_dirigido_nao_pode_ter_teto_menor_que_o_generico():
    # guarda contra a inversão voltar: quem tem o prompt maior não pode ganhar
    # menos tempo. Mede os dois prompts de verdade.
    from autotuto.planejador import _SISTEMA, exemplo
    dirigido, _ = exemplo("resolva 2x - 8 = 0")
    generico, marcado = exemplo("o que são números primos")
    assert not marcado
    maior = len(_SISTEMA) + 2 * len(dirigido)
    menor = len(_SISTEMA) + 2 * len(generico)
    assert maior > menor          # o dirigido É o mais pesado
    # ...e por isso os dois usam o mesmo teto (ver teste acima)


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


def test_pista_de_fracao():
    # "3/4" e "metade" são sinal forte de fração e têm que vencer a regra de três
    for problema in ("quanto é 3/4 de 12", "não entendo fração",
                     "o que é a metade de 20", "três quartos de 40",
                     "me explica numerador e denominador"):
        assert json.loads(_exemplo_dirigido(problema))["topico"] == "fracao_de", problema


def test_pista_de_fracao_nao_rouba_a_regra_de_tres():
    dirigido = _exemplo_dirigido("se 3 cadernos custam 24, quanto custam 5")
    assert json.loads(dirigido)["topico"] == "regra_de_tres"


# ───────────── a causa-raiz do "7 de 11 tópicos caem no fallback" (bateria real)

def test_todo_problema_leva_exemplo_no_prompt():
    # ACHADO: quando nenhuma pista de tópico casava, o prompt ia pro modelo SEM
    # NENHUM exemplo de JSON. Numa bateria de 11 tópicos, 7 caíam nesse caminho —
    # e eram exatamente os 7 que voltavam com plano quebrado. Um 7B não acerta
    # schema aninhado só pela descrição em prosa.
    from autotuto.planejador import exemplo
    for problema in ("quanto é 15 por cento de 80", "o que é mmc", "números primos",
                     "média aritmética de 4 notas", "área do círculo de raio 3",
                     "", "askdjhaskjdh"):
        texto, _ = exemplo(problema)
        assert texto and json.loads(texto)["blocos"], problema


def test_planeja_sempre_injeta_o_exemplo_nas_mensagens():
    vistas = []

    def espia(mensagens, **k):
        vistas.append(mensagens)
        raise ConnectionError()      # não interessa a resposta, só o prompt

    planeja("quanto é 15 por cento de 80", perguntar=espia)
    papeis = [m["role"] for m in vistas[0]]
    assert papeis == ["system", "user", "assistant", "user"]
    assert json.loads(vistas[0][2]["content"])["blocos"]     # o exemplo está lá


def test_exemplo_generico_manda_nao_copiar_o_assunto():
    # o risco do exemplo genérico é o modelo copiar o ASSUNTO dele e o professor
    # sair falando de retângulo pra quem perguntou de porcentagem — o mesmo
    # estrago do fallback antigo. O cabeçalho tem que dizer isso na cara.
    vistas = []

    def espia(mensagens, **k):
        vistas.append(mensagens)
        raise ConnectionError()

    planeja("quanto é 15 por cento de 80", perguntar=espia)
    pedido = vistas[0][1]["content"].lower()
    assert "estrutura" in pedido
    assert "não copie o assunto" in pedido


def test_exemplo_dirigido_ainda_vence_quando_o_topico_casa():
    from autotuto.planejador import exemplo
    texto, dirigido = exemplo("área do trapézio")
    assert dirigido and json.loads(texto)["topico"] == "area_trapezio"
    texto, dirigido = exemplo("números primos")
    assert not dirigido


def test_exemplo_de_estrutura_e_ele_proprio_uma_aula_valida():
    # exemplo que ensina erro é pior que exemplo nenhum: se o few-shot tem um
    # gerador que não existe ou um "senao" órfão, o modelo copia exatamente isso.
    from autotuto.aulas import EXEMPLO_ESTRUTURA, _com_genericos
    from autotuto.schema import validar_estrutura
    from autotuto.validador import avisos_graves, checar_matematica

    dic = _com_genericos(EXEMPLO_ESTRUTURA)
    assert validar_estrutura(dic) == []
    assert avisos_graves(checar_matematica(dic)) == []


def test_exemplo_de_estrutura_nao_polui_as_aulas_de_ouro():
    from autotuto.aulas import disponiveis
    assert "area_retangulo" not in disponiveis()
    assert "sem_plano" not in disponiveis()


# ─────────────────────── "mesma frase falada 2x seguidas" (achado em bateria local)

def _planeja_com(plano):
    return planeja("um problema", perguntar=lambda m, **k: json.dumps(plano))


def test_fala_repetida_em_beats_seguidos_e_removida():
    aula, rel = _planeja_com({
        "titulo": "T", "topico": "t", "blocos": [
            {"diz": "Vamos somar as bases.", "espera": "curta"},
            {"diz": "Vamos somar as bases.", "espera": "curta"},   # repetido: some
            {"diz": "Agora divide por dois."},
        ]})
    assert [b.get("diz") for b in aula.blocos] == ["Vamos somar as bases.",
                                                   "Agora divide por dois."]
    assert any("repetida" in a for a in rel.avisos)


def test_fala_repetida_mantem_o_beat_que_tem_figura_ou_calc():
    # o beat não some: só a fala duplicada sai, o desenho/a conta continuam
    aula, _ = _planeja_com({
        "titulo": "T", "topico": "t", "blocos": [
            {"diz": "Olha o retângulo."},
            {"diz": "Olha o retângulo.",
             "calc": {"gerador": "area_retangulo", "params": {"base": 3, "altura": 4}}},
        ]})
    assert len(aula.blocos) == 2
    assert "diz" not in aula.blocos[1] and aula.blocos[1]["calc"]


def test_fala_repetida_nao_mexe_em_beat_de_pergunta():
    # sem `diz` o tocador não pergunta nada e fica escutando um silêncio —
    # repetir é menos ruim que matar a pergunta
    aula, _ = _planeja_com({
        "titulo": "T", "topico": "t",
        "blocos": [{"diz": "O que acontece aqui?"},
                   {"diz": "O que acontece aqui?",
                    "pergunta": {"escuta_s": 10, "senao": "nao_entendi"}}],
        "ramos": {"nao_entendi": [{"diz": "explico"}]}})
    assert aula.blocos[1]["diz"] == "O que acontece aqui?"


def test_repeticao_entre_ramo_e_principal_e_permitida():
    # a primeira frase de um ramo PODE repetir a última da principal: ali é
    # retomada de propósito, não gagueira
    aula, _ = _planeja_com({
        "titulo": "T", "topico": "t",
        "blocos": [{"diz": "Divide por dois."},
                   {"diz": "Pronto.", "pergunta": {"escuta_s": 10, "senao": "por_que_x"}}],
        "ramos": {"por_que_x": [{"diz": "Divide por dois."}, {"diz": "Por causa da média."}]}})
    assert aula.ramos["por_que_x"][0]["diz"] == "Divide por dois."


# ───────── os ramos genéricos no "senao" (achado local: causa raiz nº 1)

_PLANO_COM_GENERICO = {
    "titulo": "Porcentagem", "topico": "porcentagem", "dados": {},
    "blocos": [
        {"diz": "Quinze por cento de oitenta."},
        {"diz": "Você lembra o que 'por cento' quer dizer?",
         "pergunta": {"escuta_s": 10, "senao": "nao_entendi"}},
        {"diz": "É por cem.",
         "calc": {"gerador": "porcentagem", "params": {"parte": 12, "todo": 80}}},
    ]}


def test_senao_num_ramo_generico_nao_e_rejeitado():
    # BUG: o prompt promete que por_que/nao_entendi/repete existem sempre, mas a
    # validação rodava no JSON CRU, antes do merge. Um plano PERFEITO que usasse
    # "senao": "nao_entendi" — o que o prompt manda fazer — era reprovado com
    # "não é um ramo", queimava as 3 tentativas e caía no fallback.
    n = []

    def responde(m, **k):
        n.append(1)
        return json.dumps(_PLANO_COM_GENERICO)

    aula, rel = planeja("quanto é 15 por cento de 80", perguntar=responde)
    assert len(n) == 1, f"gastou {len(n)} tentativas num plano válido"
    assert rel.ok and not rel.erros
    assert aula.titulo == "Porcentagem"          # não virou fallback
    assert aula.blocos[1]["pergunta"]["senao"] == "nao_entendi"


def test_senao_num_ramo_inventado_continua_sendo_erro():
    # o outro lado: nome que NÃO é genérico e não foi declarado tem que reprovar
    plano = {**_PLANO_COM_GENERICO, "blocos": [
        {"diz": "oi"},
        {"diz": "e aí?", "pergunta": {"escuta_s": 10, "senao": "ramo_que_nao_existe"}}]}
    pedidos = []

    def responde(m, **k):
        pedidos.append(m[-1]["content"])
        return json.dumps(plano)

    planeja("qualquer coisa", perguntar=responde)
    assert any("ramo_que_nao_existe" in p for p in pedidos[1:])


def test_prompt_diz_os_nomes_exatos_dos_ramos_sempre_presentes():
    from autotuto.planejador import _SISTEMA
    for nome in ("por_que", "nao_entendi", "repete"):
        assert f'"{nome}"' in _SISTEMA
    assert "EXISTEM SEMPRE" in _SISTEMA


def test_ramos_em_formato_errado_ainda_reclama_no_schema_sem_estourar():
    # `ramos` como lista: o merge não pode levantar TypeError antes da validação
    plano = {"titulo": "T", "topico": "t", "blocos": [{"diz": "oi"}], "ramos": []}
    pedidos = []

    def responde(m, **k):
        pedidos.append(m[-1]["content"])
        return json.dumps(plano)

    aula, rel = planeja("qualquer coisa", perguntar=responde)
    assert any("ramos" in p for p in pedidos[1:])


# ───── enxugar o few-shot dirigido (achado: 45% dele era coordenada crua)

def test_exemplo_dirigido_mostra_uma_figura_inline_e_so_uma():
    # uma ocorrência ensina a forma {"gerador":"figura","spec":{...}}; as outras
    # três só inchavam o prompt e convidavam a copiar as coordenadas do trapézio
    from autotuto.planejador import exemplo
    for problema in ("resolva 2x - 8 = 0", "área do trapézio",
                     "teorema de pitágoras", "regra de três"):
        d = json.loads(exemplo(problema)[0])
        beats = list(d["blocos"]) + [b for v in d.get("ramos", {}).values() for b in v]
        inline = [b for b in beats
                  if isinstance(b.get("figura"), dict)
                  and b["figura"].get("gerador") == "figura"]
        assert len(inline) == 1, (problema, len(inline))
        assert isinstance(inline[0]["figura"]["spec"], dict)   # completo, não truncado


def test_exemplo_dirigido_continua_sendo_uma_aula_valida():
    # exemplo que ensina erro é pior que exemplo nenhum: depois de enxugar, ele
    # ainda tem que passar no schema e na checagem matemática
    from autotuto.aulas import _com_genericos
    from autotuto.planejador import exemplo
    from autotuto.schema import validar_estrutura
    from autotuto.validador import avisos_graves, checar_matematica
    for problema in ("resolva 2x - 8 = 0", "área do trapézio",
                     "teorema de pitágoras", "regra de três", "3/4 de 12"):
        d = _com_genericos(json.loads(exemplo(problema)[0]))
        assert validar_estrutura(d) == [], problema
        assert avisos_graves(checar_matematica(d)) == [], problema


def test_nenhum_beat_do_exemplo_fica_vazio_depois_de_enxugar():
    from autotuto.planejador import exemplo
    for problema in ("resolva 2x - 8 = 0", "área do trapézio", "3/4 de 12"):
        d = json.loads(exemplo(problema)[0])
        beats = list(d["blocos"]) + [b for v in d.get("ramos", {}).values() for b in v]
        for b in beats:
            assert b.get("diz") or b.get("figura") or b.get("calc"), (problema, b)
