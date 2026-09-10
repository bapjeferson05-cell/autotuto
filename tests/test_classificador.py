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
