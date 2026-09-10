import pytest

from autotuto.aulas import carregar, disponiveis, RAMOS_GENERICOS
from autotuto.calc import CATALOGO as CALC_CATALOGO
from autotuto.figuras.canvas import figura
from autotuto.schema import validar_estrutura

NOMES = ["trapezio", "pitagoras", "eq_primeiro_grau", "regra_de_tres"]


def test_disponiveis():
    assert disponiveis() == NOMES


@pytest.mark.parametrize("nome", NOMES)
def test_aula_de_ouro_valida(nome):
    a = carregar(nome)
    assert validar_estrutura(a.para_json()) == []


@pytest.mark.parametrize("nome", NOMES)
def test_tem_ramos_genericos(nome):
    assert {"por_que", "nao_entendi", "repete"} <= set(carregar(nome).ramos)


def test_aula_sobrescreve_generico():
    # pitagoras define seu proprio por_que -> nao pode ser o texto generico
    assert (carregar("pitagoras").ramos["por_que"][0]["diz"]
            != RAMOS_GENERICOS["por_que"][0]["diz"])


def test_trapezio_tem_beat_pergunta_com_fading():
    b = next(x for x in carregar("trapezio").blocos if x.get("pergunta"))
    assert b["pergunta"]["senao"] in carregar("trapezio").ramos
    assert "triangulo" in " ".join(b["pergunta"]["acerta"]).lower()
    assert b["pergunta"].get("confirma")


def _todos_os_beats(aula):
    yield from aula.blocos
    for ramo in aula.ramos.values():
        yield from ramo


@pytest.mark.parametrize("nome", NOMES)
def test_toda_figura_renderiza(nome):
    aula = carregar(nome)
    achou = False
    for beat in _todos_os_beats(aula):
        fig = beat.get("figura")
        if not fig:
            continue
        achou = True
        assert fig["gerador"] == "figura", (nome, fig)
        png = figura(fig["spec"])
        assert png[:4] == b"\x89PNG", (nome, fig["spec"])
    assert achou, f"{nome} nao tem nenhuma figura"


@pytest.mark.parametrize("nome", NOMES)
def test_todo_calc_esta_no_catalogo(nome):
    aula = carregar(nome)
    achou = False
    for beat in _todos_os_beats(aula):
        c = beat.get("calc")
        if not c:
            continue
        achou = True
        assert c["gerador"] in CALC_CATALOGO, (nome, c["gerador"])
    assert achou, f"{nome} nao tem nenhum calc"


@pytest.mark.parametrize("nome", NOMES)
def test_pergunta_senao_aponta_ramo_existente(nome):
    aula = carregar(nome)
    for beat in aula.blocos:
        pg = beat.get("pergunta")
        if pg:
            assert pg["senao"] in aula.ramos
