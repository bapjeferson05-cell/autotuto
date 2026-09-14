"""Testes do módulo validador (checagem matemática)."""
from autotuto.validador import checar_matematica


def test_gerador_de_calc_desconhecido():
    """Avisa se gerador de calc não existe no CATALOGO."""
    a = {
        "blocos": [{"diz": "x", "calc": {"gerador": "fantasma", "params": {}}}],
        "ramos": {},
    }
    avisos = checar_matematica(a)
    assert any("fantasma" in e for e in avisos)


def test_params_que_explodem():
    """Avisa se os params fazem o gerador levantar exceção."""
    a = {
        "blocos": [
            {
                "diz": "x",
                "calc": {"gerador": "regra_de_tres", "params": {"a": 0, "b": 1, "c": 1}},
            }
        ],
        "ramos": {},
    }
    avisos = checar_matematica(a)
    assert avisos  # divisão por zero -> aviso


def test_aula_boa_sem_avisos():
    """Aula bem-formada não gera avisos."""
    a = {
        "blocos": [
            {
                "diz": "x",
                "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
            }
        ],
        "ramos": {},
    }
    assert checar_matematica(a) == []


def test_figura_gerador_desconhecido():
    """Avisa se gerador nomeado de figura não existe."""
    a = {
        "blocos": [{"figura": {"gerador": "figura_fantasma"}}],
        "ramos": {},
    }
    avisos = checar_matematica(a)
    assert any("figura_fantasma" in e for e in avisos)


def test_figura_inline_nao_avisa():
    """Specs inline (gerador='figura') não geram avisos mesmo com spec ruim."""
    a = {
        "blocos": [{"figura": {"gerador": "figura", "spec": {"pontos": {}}}}],
        "ramos": {},
    }
    avisos = checar_matematica(a)
    assert avisos == []


def test_area_negativa():
    """Avisa se gerador de área/comprimento retorna valor negativo."""
    a = {
        "blocos": [
            {
                "diz": "x",
                "calc": {"gerador": "area_trapezio", "params": {"B": -5, "b": 10, "h": 6}},
            }
        ],
        "ramos": {},
    }
    avisos = checar_matematica(a)
    # O calc vai executar com B=-5, b=10, h=6 -> (-5 + 10) * 6 / 2 = 15 (positivo)
    # Mas se trocarmos para valores que dão negativo:
    a2 = {
        "blocos": [
            {
                "diz": "x",
                "calc": {"gerador": "area_trapezio", "params": {"B": 5, "b": 10, "h": -6}},
            }
        ],
        "ramos": {},
    }
    avisos2 = checar_matematica(a2)
    # (5 + 10) * (-6) / 2 = -45 -> deve avisar valor negativo
    assert any("negativo" in e or "valor" in e for e in avisos2)


def test_ramo_com_calc():
    """Valida calc também em ramos."""
    a = {
        "blocos": [],
        "ramos": {
            "caminho1": [
                {
                    "diz": "y",
                    "calc": {"gerador": "gerador_inexistente", "params": {}},
                }
            ]
        },
    }
    avisos = checar_matematica(a)
    assert any("gerador_inexistente" in e for e in avisos)


def test_houve_falha_grave_gerador_desconhecido():
    from autotuto.validador import houve_falha_grave
    assert houve_falha_grave(["gerador de calc desconhecido: fantasma"]) is True
    assert houve_falha_grave(["gerador de figura desconhecido: grafico_barras"]) is True


def test_houve_falha_grave_execucao_falhou():
    from autotuto.validador import houve_falha_grave
    assert houve_falha_grave(["eq_primeiro_grau falhou: unexpected keyword argument 'x'"]) is True


def test_houve_falha_grave_falso_para_aviso_leve():
    from autotuto.validador import houve_falha_grave
    assert houve_falha_grave(["area_trapezio: valor negativo (-45)"]) is False
    assert houve_falha_grave([]) is False


def test_calc_com_kwarg_extra_e_rejeitado_antes_de_rodar():
    # contrato explícito por gerador: eq_primeiro_grau(a, b) não aceita 'x'.
    # A rejeição usa a ASSINATURA de verdade (inspect), não uma lista à parte.
    a = {
        "blocos": [{"diz": "x", "calc": {"gerador": "eq_primeiro_grau",
                                        "params": {"a": 1, "b": -90, "x": "y"}}}],
        "ramos": {},
    }
    avisos = checar_matematica(a)
    assert len(avisos) == 1
    msg = avisos[0]
    assert "eq_primeiro_grau" in msg and "'x'" in msg
    assert "a, b" in msg                      # diz exatamente o que É aceito
    assert "falhou" not in msg                # não foi um TypeError pego depois —
                                               # foi rejeitado ANTES de chamar a função


def test_calc_com_params_validos_nao_e_rejeitado():
    a = {
        "blocos": [{"diz": "x", "calc": {"gerador": "eq_primeiro_grau",
                                        "params": {"a": 1, "b": -90}}}],
        "ramos": {},
    }
    assert checar_matematica(a) == []


def test_calc_kwarg_extra_conta_como_falha_grave():
    from autotuto.validador import houve_falha_grave
    a = {
        "blocos": [{"diz": "x", "calc": {"gerador": "eq_primeiro_grau",
                                        "params": {"a": 1, "b": -90, "x": "y"}}}],
        "ramos": {},
    }
    assert houve_falha_grave(checar_matematica(a)) is True


def test_exemplo_literal_do_usuario_eq_primeiro_grau_com_x_extra():
    # o caso exato pedido pra fechar essa peça: eq_primeiro_grau(a=35, b=90,
    # x=35) -> REJEITADO com "argumento desconhecido"; sem o x, EXECUTA.
    a_ruim = {"blocos": [{"diz": "x", "calc": {"gerador": "eq_primeiro_grau",
                                              "params": {"a": 35, "b": 90, "x": 35}}}],
             "ramos": {}}
    avisos = checar_matematica(a_ruim)
    assert len(avisos) == 1 and "argumento desconhecido" in avisos[0] and "'x'" in avisos[0]

    a_bom = {"blocos": [{"diz": "x", "calc": {"gerador": "eq_primeiro_grau",
                                             "params": {"a": 35, "b": 90}}}],
            "ramos": {}}
    assert checar_matematica(a_bom) == []


# ───── "promete calcular e não mostra" (achado em bateria local, tópico 9)

def test_promessa_de_conta_sem_calc_e_grave():
    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [{"diz": "Beleza, então vamos calcular isso agora."},
                        {"diz": "E é isso, valeu!"}]}
    avisos = checar_matematica(plano)
    assert any("promete a conta" in a for a in avisos), avisos
    # grave = o LLM ganha uma chance de corrigir, igual a um erro de schema
    assert avisos_graves(avisos)


def test_promessa_paga_no_beat_seguinte_nao_acusa():
    # "agora vamos calcular" + beat com o calc é o padrão NORMAL da aula
    from autotuto.validador import checar_matematica
    plano = {"blocos": [
        {"diz": "Beleza, vamos calcular isso agora."},
        {"diz": "pronto", "calc": {"gerador": "area_retangulo",
                                   "params": {"base": 2, "altura": 3}}}]}
    assert [a for a in checar_matematica(plano) if "promete" in a] == []


def test_promessa_dentro_de_ramo_tambem_conta():
    from autotuto.validador import checar_matematica
    plano = {"blocos": [{"diz": "oi"}],
             "ramos": {"por_que": [{"diz": "Deixa eu fazer a conta pra você ver."}]}}
    assert any("ramo 'por_que'" in a and "promete" in a
               for a in checar_matematica(plano))


def test_entrega_no_passado_nao_e_promessa():
    # "isso dá oitenta e quatro" é entrega, não promessa — não pode acusar
    from autotuto.validador import checar_matematica
    plano = {"blocos": [{"diz": "Isso dá oitenta e quatro metros quadrados."},
                        {"diz": "E é isso."}]}
    assert [a for a in checar_matematica(plano) if "promete" in a] == []


def test_aulas_de_ouro_nao_disparam_falso_positivo_de_promessa():
    from autotuto.aulas import carregar, disponiveis
    from autotuto.validador import checar_matematica
    for nome in disponiveis():
        avisos = [a for a in checar_matematica(carregar(nome).para_json())
                  if "promete" in a]
        assert avisos == [], (nome, avisos)


# ───── deriva de idioma (achado em bateria local: qwen trocou pra chinês)

def test_fala_em_chines_e_grave():
    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [{"diz": "Agora a gente soma as bases 然后除以二"}]}
    avisos = checar_matematica(plano)
    assert any("chinês" in a for a in avisos), avisos
    assert avisos_graves(avisos)        # o LLM ganha chance de reescrever


def test_deriva_de_idioma_pega_diz_passos_e_confirma():
    from autotuto.validador import checar_matematica
    plano = {"blocos": [
        {"diz": "ok", "diz_passos": ["primeiro passo", "第二步"]},
        {"diz": "ok", "pergunta": {"escuta_s": 10, "senao": "x",
                                   "confirma": "правильно"}}]}
    avisos = [a for a in checar_matematica(plano) if "não em português" in a]
    assert len(avisos) == 2, avisos


def test_portugues_com_acento_e_simbolo_nao_e_falso_positivo():
    from autotuto.validador import checar_matematica
    plano = {"blocos": [{"diz": "Três metros quadrados — é isso aí, tranquilo? ½ não"},
                        {"diz": "Ângulo de 90°, área ≈ 84 u²"}]}
    assert [a for a in checar_matematica(plano) if "não em português" in a] == []


def test_aulas_de_ouro_passam_no_teste_de_idioma():
    from autotuto.aulas import carregar, disponiveis
    from autotuto.validador import checar_matematica
    for nome in disponiveis():
        ruim = [a for a in checar_matematica(carregar(nome).para_json())
                if "não em português" in a]
        assert ruim == [], (nome, ruim)


# ───── spec inline de figura (achado local: prova geométrica perdida)

def test_spec_inline_com_ponto_nao_declarado_e_grave():
    # ANTES: spec inline (gerador="figura") não era validado de jeito nenhum.
    # Estourava só no tocador, que pede desculpa e segue sem o desenho — o
    # modelo nunca via o erro. Uma prova geométrica com reta paralela se perdeu
    # assim, por um ponto citado em "segmentos" e esquecido em "pontos".
    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [{"diz": "olha a paralela", "figura": {"gerador": "figura", "spec": {
        "pontos": {"A": [0, 0], "B": [6, 0], "C": [2, 4]},
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}],
        "segmentos": [{"de": "C", "para": "E", "tracejado": True}]}}}]}
    avisos = checar_matematica(plano)
    assert any("'E'" in a and "pontos" in a for a in avisos), avisos
    assert avisos_graves(avisos)       # volta pro modelo com chance de correção


def test_spec_inline_correto_nao_acusa():
    from autotuto.validador import checar_matematica
    plano = {"blocos": [{"figura": {"gerador": "figura", "spec": {
        "pontos": {"A": [0, 0], "B": [6, 0], "C": [2, 4], "E": [4, 4]},
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}],
        "segmentos": [{"de": "C", "para": "E", "tracejado": True}],
        "marcas": [{"tipo": "par", "de": "A", "para": "B"}]}}}]}
    assert checar_matematica(plano) == []


def test_gerador_nomeado_com_params_ruins_e_pego_antes_do_ar():
    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [{"figura": {"gerador": "circulo", "params": {"raio": -5}}}]}
    assert avisos_graves(checar_matematica(plano))


# ───── diz_passos separado do calc (achado local: causa raiz nº 2)

def test_diz_passos_sem_calc_no_mesmo_beat_e_grave():
    # o tocador só lê diz_passos DENTRO do bloco do calc: separado em outro
    # beat, a narração inteira some — sem erro, sem log. Os passos apareciam
    # mudos na lousa.
    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [
        {"diz": "vamos à conta",
         "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
         "mostra_passos": True},
        {"diz": "agora eu explico", "diz_passos": ["a fórmula", "os números", "dá 84"]}]}
    avisos = checar_matematica(plano)
    assert any(a.startswith("diz_passos sem calc") for a in avisos), avisos
    assert avisos_graves(avisos)


def test_diz_passos_junto_do_calc_nao_acusa():
    from autotuto.validador import checar_matematica
    plano = {"blocos": [{
        "diz": "a conta",
        "calc": {"gerador": "area_retangulo", "params": {"base": 3, "altura": 4}},
        "mostra_passos": True, "diz_passos": ["três vezes quatro dá doze"]}]}
    assert [a for a in checar_matematica(plano) if "diz_passos" in a] == []


def test_prompt_mostra_calc_e_diz_passos_no_mesmo_beat():
    from autotuto.planejador import _SISTEMA
    assert "MESMO OBJETO de beat" in _SISTEMA
    assert '"diz_passos": [' in _SISTEMA      # o exemplo concreto está lá


# ───── contrato de params da FIGURA (achado da bateria local)

def test_kwarg_errado_em_gerador_de_figura_e_grave():
    # O `**_` de todo gerador de figura ENGOLE o kwarg errado em silêncio: o
    # render não estoura, e a figura sai com o valor PADRÃO no lugar do que o
    # enunciado pedia. O aluno vê um retângulo que não é o do problema e
    # ninguém fica sabendo. `_validar_calc` tinha esse contrato desde sempre;
    # `_validar_figura` nunca ganhou.
    from autotuto.validador import avisos_graves, checar_matematica
    plano = {"blocos": [{"diz": "olha o terreno", "figura": {
        "gerador": "retangulo", "params": {"base": 12, "largura": 20}}}]}
    avisos = checar_matematica(plano)
    assert any("largura" in a and "base, altura" in a for a in avisos), avisos
    assert avisos_graves(avisos)


def test_kwarg_engolido_produzia_mesmo_png_do_default():
    # a prova de que o render sozinho NUNCA pegaria isso
    from autotuto.figuras.catalogo import retangulo
    assert retangulo(base=12, largura=20) == retangulo(base=12, altura=7)


def test_params_certos_de_figura_nao_acusam():
    from autotuto.validador import checar_matematica
    for gerador, params in (("retangulo", {"base": 12, "altura": 20}),
                            ("trapezio", {"B": 18, "b": 10, "h": 6}),
                            ("circulo", {"raio": 5}),
                            ("fracao", {"num": 3, "den": 4}),
                            ("triangulo", {"tipo": "reto", "base": 8, "altura": 6}),
                            ("reta_numerica", {"inicio": 0, "fim": 10, "passo": 1})):
        plano = {"blocos": [{"figura": {"gerador": gerador, "params": params}}]}
        assert checar_matematica(plano) == [], (gerador, checar_matematica(plano))


def test_spec_inline_nao_passa_pelo_contrato_de_kwargs():
    # gerador="figura" recebe `spec`, não kwargs nomeados — o contrato não se
    # aplica e não pode inventar aviso
    from autotuto.validador import checar_matematica
    plano = {"blocos": [{"figura": {"gerador": "figura", "spec": {
        "pontos": {"A": [0, 0], "B": [1, 1]}, "segmentos": [["A", "B"]]}}}]}
    assert checar_matematica(plano) == []


def test_aulas_de_ouro_passam_no_contrato_de_figura():
    from autotuto.aulas import carregar, disponiveis
    from autotuto.validador import checar_matematica
    for nome in disponiveis():
        assert checar_matematica(carregar(nome).para_json()) == [], nome
