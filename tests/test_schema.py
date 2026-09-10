from autotuto.schema import Aula, validar_estrutura

AULA_OK = {"titulo": "T", "topico": "area_trapezio", "dados": {"B": 18},
           "blocos": [{"diz": "olá"}],
           "ramos": {"por_que": [{"diz": "porque sim"}]}}

def test_aula_valida_nao_tem_erros():
    assert validar_estrutura(AULA_OK) == []

def test_bloco_sem_diz_figura_calc_e_erro():
    obj = {**AULA_OK, "blocos": [{}]}
    assert any("vazio" in e for e in validar_estrutura(obj))

def test_pergunta_precisa_de_senao():
    obj = {**AULA_OK, "blocos": [{"diz": "x", "pergunta": {"escuta_s": 10}}]}
    assert any("senao" in e for e in validar_estrutura(obj))

def test_pergunta_senao_tem_que_ser_ramo_existente():
    obj = {**AULA_OK, "blocos": [{"diz": "x", "pergunta": {"escuta_s": 10, "senao": "fantasma"}}]}
    assert any("fantasma" in e for e in validar_estrutura(obj))

def test_acerta_tem_que_ser_lista_de_strings():
    obj = {**AULA_OK, "blocos": [{"diz": "x", "pergunta":
           {"escuta_s": 10, "senao": "por_que", "acerta": "triangulo"}}]}
    assert any("acerta" in e for e in validar_estrutura(obj))

def test_de_json_e_para_json_roundtrip():
    a = Aula.de_json(AULA_OK)
    assert a.para_json()["titulo"] == "T"
    assert a.ramos["por_que"][0]["diz"] == "porque sim"
