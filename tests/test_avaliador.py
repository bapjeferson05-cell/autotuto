from autotuto.avaliador import avalia_resposta

PERGUNTA = "por que a área do triângulo é base vezes altura dividido por dois?"
ESPERADO = ["porque o triângulo é metade de um retângulo"]


def test_llm_diz_certo():
    fake = lambda msgs, **k: '{"veredito": "certo"}'
    assert avalia_resposta(PERGUNTA, ESPERADO, "porque ele é metade de um retângulo",
                            perguntar=fake) == "certo"


def test_llm_diz_parcial():
    fake = lambda msgs, **k: '{"veredito": "parcial"}'
    assert avalia_resposta(PERGUNTA, ESPERADO, "porque divide por dois",
                            perguntar=fake) == "parcial"


def test_llm_diz_errado():
    fake = lambda msgs, **k: '{"veredito": "errado"}'
    assert avalia_resposta(PERGUNTA, ESPERADO, "porque sim",
                            perguntar=fake) == "errado"


def test_llm_devolve_veredito_fora_do_vocabulario_vira_none():
    fake = lambda msgs, **k: '{"veredito": "mais ou menos"}'
    assert avalia_resposta(PERGUNTA, ESPERADO, "sei lá", perguntar=fake) is None


def test_lixo_de_json_vira_none():
    fake = lambda msgs, **k: "desculpa não entendi"
    assert avalia_resposta(PERGUNTA, ESPERADO, "x", perguntar=fake) is None


def test_llm_explode_vira_none():
    def fake(msgs, **k):
        raise TimeoutError()
    assert avalia_resposta(PERGUNTA, ESPERADO, "x", perguntar=fake) is None


def test_resposta_vazia_vira_none_sem_chamar_llm():
    def fake(msgs, **k):
        raise AssertionError("não deveria chamar o LLM sem resposta do aluno")
    assert avalia_resposta(PERGUNTA, ESPERADO, "", perguntar=fake) is None
    assert avalia_resposta(PERGUNTA, ESPERADO, "   ", perguntar=fake) is None


def test_esperado_vazio_vira_none_sem_chamar_llm():
    def fake(msgs, **k):
        raise AssertionError("não deveria chamar o LLM sem 'acerta' pra comparar")
    assert avalia_resposta(PERGUNTA, [], "qualquer coisa", perguntar=fake) is None


def test_regua_empurra_pro_lado_do_aluno():
    # ACHADO em bateria local: o modelo local reprovou como "errado" uma
    # definição de triângulo tecnicamente correta, só porque não era a redação
    # esperada. O erro é assimétrico — reprovar quem acertou faz o professor
    # explicar o que o aluno já sabia e dá a entender que ele errou. A régua
    # tem que dizer isso ao modelo, explicitamente.
    from autotuto.avaliador import _SIS
    s = _SIS.lower()
    assert "exemplos de redação" in s          # o 'acerta' não é lista fechada
    assert "outras palavras" in s
    assert s.count("na dúvida") >= 2           # as duas faixas de dúvida
    assert "último recurso" in s


def test_veredito_fora_do_vocabulario_vira_none():
    from autotuto.avaliador import avalia_resposta
    r = avalia_resposta("p", ["x"], "resposta",
                        perguntar=lambda m, **k: '{"veredito": "mais ou menos"}')
    assert r is None
