"""test_classificador.py — fala do aluno → gatilho de ramo.

A tabela de casos do antigo bloco `if __name__ == "__main__":` de classificador.py
virou testes de verdade aqui, mais os casos de borda que esse bloco não cobria:
sem lista de ramos, ramos que não incluem o gatilho casado, e prioridade entre regras
que colidem na mesma fala.
"""
from professor.classificador import classificar

_RAMOS_PADRAO = ["por_que_div_2", "nao_entendi", "e_triangulo", "decompor", "por_que"]


# ────────────────────────────────────────────── casos originais (do __main__)
def test_por_que_div_2():
    assert classificar("Peraí, por que que divide por dois?", _RAMOS_PADRAO) == "por_que_div_2"


def test_nao_entendi():
    assert classificar("não entendi essa parte", _RAMOS_PADRAO) == "nao_entendi"


def test_e_triangulo():
    assert classificar("e se fosse um triângulo?", _RAMOS_PADRAO) == "e_triangulo"


def test_decompor():
    assert classificar("tem outro jeito? não decorei a fórmula", _RAMOS_PADRAO) == "decompor"


def test_por_que_generico():
    assert classificar("por que a altura é perpendicular?", _RAMOS_PADRAO) == "por_que"


def test_sem_gatilho_nenhum():
    assert classificar("beleza, entendi", _RAMOS_PADRAO) is None


# ────────────────────────────────────────────── normalização (acento/caixa/pontuação)
def test_ignora_acento_e_caixa():
    assert classificar("POR QUE DIVIDE POR DOIS???", _RAMOS_PADRAO) == "por_que_div_2"
    assert classificar("NÃO ENTENDI NADA", _RAMOS_PADRAO) == "nao_entendi"


# ────────────────────────────────────────────── prioridade entre regras
def test_por_que_div_2_ganha_de_por_que_generico_na_mesma_frase():
    # "por que" bate na regra genérica também, mas por_que_div_2 vem primeiro na lista
    assert classificar("por que divide por 2?", _RAMOS_PADRAO) == "por_que_div_2"


# ────────────────────────────────────────────── sem lista de ramos (aceita tudo)
def test_sem_lista_de_ramos_ainda_classifica():
    assert classificar("por que isso?") == "por_que"
    assert classificar("não entendi") == "nao_entendi"


# ────────────────────────────────────────────── o 'por_que' genérico rebaixa pro
# primeiro 'por_que*' que a aula realmente tem
def test_por_que_generico_rebaixa_para_por_que_disponivel_na_aula():
    ramos = ["nao_entendi", "por_que_na_prova"]
    assert classificar("por que isso funciona?", ramos) == "por_que_na_prova"


def test_por_que_generico_sem_nenhum_por_que_na_aula_nao_classifica():
    ramos = ["nao_entendi", "decompor"]
    assert classificar("por que isso funciona?", ramos) is None


# ────────────────────────────────────────────── gatilho fora da aula: deve ser
# ignorado (cai pra próxima regra), não devolvido do mesmo jeito
def test_gatilho_fora_dos_ramos_disponiveis_nao_e_devolvido():
    # a fala bate no regex de 'decompor', mas a aula não tem esse ramo — não deveria
    # classificar como 'decompor' (ramo que não existe nessa aula)
    ramos_sem_decompor = ["nao_entendi", "por_que_div_2", "e_triangulo", "por_que"]
    assert classificar("tem outro jeito de fazer isso?", ramos_sem_decompor) != "decompor"


def test_gatilho_fora_dos_ramos_mas_outra_regra_bate_ainda_classifica():
    # a fala bate tanto em 'e_triangulo' (ramo ausente) quanto, sozinha, não bateria em
    # mais nada — então o resultado tem que ser None, não 'e_triangulo'
    ramos_sem_triangulo = ["nao_entendi", "por_que_div_2", "decompor", "por_que"]
    assert classificar("e se fosse um triângulo?", ramos_sem_triangulo) is None
