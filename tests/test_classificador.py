from autotuto.classificador import classificar, _norm

RAMOS_TRAP = ["por_que_div_2", "nao_entendi", "e_triangulo", "repete"]
RAMOS_PITA = ["por_que", "nao_entendi", "repete"]

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
