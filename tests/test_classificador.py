from autotuto.classificador import classificar, _norm

RAMOS_TRAP = ["por_que_div_2", "nao_entendi", "e_triangulo", "repete"]
RAMOS_PITA = ["por_que", "nao_entendi", "repete"]
RAMOS_FRAC = ["por_que", "nao_entendi", "repete", "comeca_pelo_de_baixo",
              "e_se_outro_corte", "e_se_metade"]

def test_por_que_especifico():
    assert classificar("por que que divide por dois?", RAMOS_TRAP) == "por_que_div_2"

def test_por_que_generico_rebaixa():
    assert classificar("mas por que isso funciona?", RAMOS_TRAP) == "por_que_div_2"
    assert classificar("mas por que isso funciona?", RAMOS_PITA) == "por_que"

def test_repete():
    assert classificar("pode repetir?", RAMOS_PITA) == "repete"
    assert classificar("hã?", RAMOS_PITA) == "repete"

def test_nunca_devolve_gatilho_ausente():
    # "e se fosse um triangulo" casa e_triangulo, mas pitagoras NAO tem esse ramo
    assert classificar("e se fosse um triângulo?", RAMOS_PITA) is None

def test_sem_match_e_none():
    assert classificar("quanto custa o pedreiro", RAMOS_TRAP) is None

def test_norm():
    assert _norm("Pêra Aí, POR QUÊ?!") == "pera ai por que"


def test_extrai_numero_digito_e_por_extenso():
    from autotuto.classificador import extrai_numero
    assert extrai_numero("4") == 4.0
    assert extrai_numero("quatro") == 4.0
    assert extrai_numero("o mdc é 4") == 4.0
    assert extrai_numero("acho que é quatro") == 4.0
    assert extrai_numero("vinte e cinco") == 25.0
    assert extrai_numero("trinta") == 30.0
    assert extrai_numero("cem") == 100.0
    assert extrai_numero("não sei") is None


def test_mesma_resposta_numerica():
    from autotuto.classificador import mesma_resposta_numerica
    assert mesma_resposta_numerica("4", "quatro") is True
    assert mesma_resposta_numerica("4", "o mdc é 4") is True
    assert mesma_resposta_numerica("4", "acho que é quatro") is True
    assert mesma_resposta_numerica("4", "5") is False
    assert mesma_resposta_numerica("4", "não sei") is False


def test_numero_atomico_aceita_so_o_numero_puro():
    from autotuto.classificador import _numero_atomico
    assert _numero_atomico("4") == 4.0
    assert _numero_atomico("quatro") == 4.0
    assert _numero_atomico("vinte e cinco") == 25.0
    assert _numero_atomico("cem") == 100.0
    # NÃO atômico: o número é só parte de uma frase maior
    assert _numero_atomico("três triângulos") is None
    assert _numero_atomico("dividido por dois") is None
    assert _numero_atomico("metade de um retângulo") is None
    assert _numero_atomico("o mdc é 4") is None


def test_mesma_resposta_numerica_so_com_acerta_atomico():
    # P1.1 — o achado do "três lados" ≈ "três triângulos" (2026-09-12): o
    # 'acerta' precisa ser numericamente atômico pro avaliador numérico
    # sequer entrar em cena.
    from autotuto.classificador import mesma_resposta_numerica
    # regressão obrigatória: as respostas boas continuam batendo
    assert mesma_resposta_numerica("4", "quatro") is True
    assert mesma_resposta_numerica("4", "o mdc é 4") is True
    assert mesma_resposta_numerica("4", "acho que é quatro") is True
    assert mesma_resposta_numerica("4", "5") is False
    # o falso positivo do "três lados" — NÃO pode mais acertar
    assert mesma_resposta_numerica("três triângulos", "triângulo tem três lados") is False
    assert mesma_resposta_numerica("dividido por dois", "porque divide por 2") is False
    assert mesma_resposta_numerica("metade de um retângulo", "porque divide por 2") is False


def test_gatilhos_da_aula_de_fracao():
    # os ramos da aula de fração precisam de caminho na camada 1 (regex) — se só
    # o cerebro (LLM) alcançasse, o modo determinístico nunca chegaria neles.
    assert classificar("e se cortasse em mais pedaços?", RAMOS_FRAC) == "e_se_outro_corte"
    assert classificar("seis oitavos não é a mesma coisa?", RAMOS_FRAC) == "e_se_outro_corte"
    assert classificar("e se fosse a metade?", RAMOS_FRAC) == "e_se_metade"
    assert classificar("começa por onde?", RAMOS_FRAC) == "comeca_pelo_de_baixo"
    assert classificar("qual vem primeiro?", RAMOS_FRAC) == "comeca_pelo_de_baixo"


def test_gatilhos_de_fracao_nao_vazam_pra_outras_aulas():
    # aula sem esses ramos não pode receber um gatilho que ela não tem
    for fala in ("e se fosse a metade?", "e se cortasse em mais pedaços?",
                 "começa por onde?"):
        assert classificar(fala, RAMOS_PITA) in (None, "por_que", "nao_entendi",
                                                 "repete"), fala


def test_por_que_divide_por_dois_continua_ganhando_de_metade():
    # "metade" aparece nas duas regras; no trapézio a específica tem que vencer
    assert classificar("por que divide pela metade?", RAMOS_TRAP) == "por_que_div_2"


def test_gatilho_de_onde_veio():
    ramos = ["por_que", "nao_entendi", "repete", "de_onde_veio"]
    for fala in ("de onde veio essa fórmula?", "de onde saiu isso?",
                 "quem inventou isso?", "quem foi que descobriu isso?",
                 "como descobriram isso?", "quem criou essa conta?",
                 "qual a história dessa fórmula?"):
        assert classificar(fala, ramos) == "de_onde_veio", fala


def test_de_onde_veio_vence_o_por_que_generico():
    # a regra larga do por_que (\bpor ?que\b) engoliria "por que essa fórmula
    # existe" — a específica tem que vir antes
    ramos = ["por_que", "nao_entendi", "repete", "de_onde_veio"]
    assert classificar("por que essa formula existe?", ramos) == "de_onde_veio"
    # mas um "por que" comum continua indo pro por_que
    assert classificar("mas por que isso funciona?", ramos) == "por_que"


def test_de_onde_veio_nao_rouba_o_por_que_div_2_do_trapezio():
    # "de onde vem esse dois" é pergunta sobre o PASSO, não sobre a história
    assert classificar("de onde vem esse dois?", RAMOS_TRAP) == "por_que_div_2"


def test_de_onde_veio_nao_vaza_pra_aula_que_nao_tem():
    assert classificar("quem inventou isso?", ["por_que", "repete"]) in (None, "por_que")
