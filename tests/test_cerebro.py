from autotuto.cerebro import roteia_interrupcao

RAMOS = {"por_que": [{"diz": "..."}], "nao_entendi": [{"diz": "..."}], "repete": [{"diz": "..."}]}

def test_llm_escolhe_ramo():
    fake = lambda msgs, **k: '{"ramo": "nao_entendi"}'
    assert roteia_interrupcao("tô boiando", "ctx", RAMOS, perguntar=fake) == "nao_entendi"

def test_llm_diz_nenhum():
    fake = lambda msgs, **k: '{"ramo": "nenhum"}'
    assert roteia_interrupcao("qual teu nome?", "ctx", RAMOS, perguntar=fake) is None

def test_llm_devolve_ramo_inexistente_vira_none():
    fake = lambda msgs, **k: '{"ramo": "inventado"}'
    assert roteia_interrupcao("x", "ctx", RAMOS, perguntar=fake) is None

def test_llm_explode_vira_none():
    def fake(msgs, **k): raise TimeoutError()
    assert roteia_interrupcao("x", "ctx", RAMOS, perguntar=fake) is None

def test_lixo_de_json_vira_none():
    fake = lambda msgs, **k: "desculpa não entendi"
    assert roteia_interrupcao("x", "ctx", RAMOS, perguntar=fake) is None
