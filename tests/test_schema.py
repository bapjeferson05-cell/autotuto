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

def test_figura_string_crua_e_erro():
    # F7: `figura` como string (não objeto) — o schema tem que pegar
    obj = {**AULA_OK, "blocos": [{"diz": "x", "figura": "trapezio"}]}
    assert any("figura" in e for e in validar_estrutura(obj))


def test_calc_com_gerador_nao_texto_e_erro():
    obj = {**AULA_OK, "blocos": [{"diz": "x", "calc": {"gerador": 123}}]}
    assert any("calc.gerador" in e for e in validar_estrutura(obj))


def test_figura_inline_valida_nao_tem_erro():
    obj = {**AULA_OK, "blocos": [{"diz": "x", "figura":
           {"gerador": "figura", "spec": {"pontos": {}}}}]}
    assert validar_estrutura(obj) == []


def test_de_json_e_para_json_roundtrip():
    a = Aula.de_json(AULA_OK)
    assert a.para_json()["titulo"] == "T"
    assert a.ramos["por_que"][0]["diz"] == "porque sim"


def test_figura_string_crua_DENTRO_de_ramo_e_erro():
    # code-review: a checagem de forma só rodava em blocos de topo. Um beat
    # malformado dentro de 'ramos' passava batido e só explodia depois, no
    # validador matemático (AttributeError) — quebrando o "nunca crasha".
    obj = {**AULA_OK, "ramos": {"por_que": [{"diz": "x", "figura": "trapezio"}]}}
    assert any("figura" in e for e in validar_estrutura(obj))


def test_calc_string_crua_DENTRO_de_ramo_e_erro():
    obj = {**AULA_OK, "ramos": {"por_que": [{"diz": "x", "calc": "area_trapezio"}]}}
    assert any("calc" in e for e in validar_estrutura(obj))


def test_beat_string_crua_e_erro_sem_crashar():
    # achado ao vivo 2026-09-13: um item de 'blocos' pode chegar do LLM como
    # STRING CRUA (não um beat/objeto) -- sem o guarda, `b.get(...)` estourava
    # AttributeError aqui dentro, derrubando o thread do planejador e, sem
    # try/except lá em cima, o processo do demo inteiro.
    obj = {**AULA_OK, "blocos": [{"diz": "oi"}, "isso não é um beat"]}
    erros = validar_estrutura(obj)
    assert any("bloco[1]" in e and "objeto" in e for e in erros)


def test_beat_string_crua_DENTRO_de_ramo_e_erro_sem_crashar():
    obj = {**AULA_OK, "ramos": {"por_que": [{"diz": "x"}, "string crua"]}}
    erros = validar_estrutura(obj)
    assert any("por_que" in e and "objeto" in e for e in erros)


# ───── o JSON Schema pro constrained decoding

def test_esquema_e_raso_de_proposito():
    # levantamento de 2026: modelo quantizado pequeno devolve array vazio em
    # schema aninhado 3+ níveis. `spec` e `params` ficam objeto LIVRE porque
    # travá-los seria trocar um erro por outro.
    from autotuto.schema import esquema_json
    e = esquema_json()
    beat = e["properties"]["blocos"]["items"]["properties"]
    assert beat["figura"]["properties"]["spec"] == {"type": "object"}
    assert beat["calc"]["properties"]["params"] == {"type": "object"}


def test_esquema_trava_o_que_quebrava_de_verdade():
    from autotuto.schema import esquema_json
    e = esquema_json()
    assert e["properties"]["blocos"]["type"] == "array"
    assert e["properties"]["blocos"]["minItems"] == 1
    beat = e["properties"]["blocos"]["items"]["properties"]
    assert beat["pergunta"]["properties"]["senao"]["type"] == "string"
    assert beat["pergunta"]["required"] == ["senao"]
    assert beat["diz_passos"]["type"] == "array"


def test_as_aulas_de_ouro_batem_com_o_proprio_esquema():
    # se o esquema recusasse a nossa própria aula escrita à mão, ele estaria
    # errado — e a gente estaria forçando o modelo a errar.
    import pytest
    jsonschema = pytest.importorskip(
        "jsonschema", reason="dep de teste: pip install -e '.[test]'")
    from autotuto.aulas import carregar, disponiveis
    from autotuto.schema import esquema_json
    for nome in disponiveis():
        jsonschema.validate(carregar(nome).para_json(), esquema_json())


def test_espera_do_esquema_bate_com_a_validacao():
    from autotuto.schema import _ESPERAS, esquema_json
    enum = esquema_json()["properties"]["blocos"]["items"]["properties"]["espera"]["enum"]
    assert set(enum) == {x for x in _ESPERAS if x}
