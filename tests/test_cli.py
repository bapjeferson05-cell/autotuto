"""test_cli.py — o comando único `autotuto`. Só a parte pura (resolução de nome
e listagem); tocar de verdade abre um Visor/HTTP, isso é coisa de demo manual."""
from professor.aulas import disponiveis
from professor.cli import _lista, _norm, resolve


def test_resolve_bate_nome_exato():
    assert resolve("trapezio") == "trapezio"


def test_resolve_ignora_acento_e_maiuscula():
    assert resolve("Trapézio") == "trapezio"
    assert resolve("PITÁGORAS") == "pitagoras"


def test_resolve_topico_fora_do_catalogo_e_none():
    assert resolve("circulo") is None
    assert resolve("qualquer coisa que não existe") is None


def test_norm_colapsa_espacos_e_pontuacao():
    assert _norm("eq. primeiro grau!") == "eq_primeiro_grau"


def test_lista_cita_todas_as_aulas_de_ouro():
    txt = _lista()
    for nome in disponiveis():
        assert nome in txt


def test_lista_nao_menciona_llm_como_caminho_padrao():
    # a mensagem padrão oferece o catálogo; o planejador só aparece atrás de --novo
    txt = _lista()
    assert "--novo" in txt
