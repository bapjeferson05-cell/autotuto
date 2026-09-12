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
