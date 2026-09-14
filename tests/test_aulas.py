import pytest

from autotuto.aulas import carregar, disponiveis, RAMOS_GENERICOS
from autotuto.calc import CATALOGO as CALC_CATALOGO
from autotuto.figuras.canvas import figura
from autotuto.schema import validar_estrutura

NOMES = ["trapezio", "pitagoras", "eq_primeiro_grau", "regra_de_tres", "fracao",
         "angulos"]


def test_disponiveis():
    assert disponiveis() == NOMES


@pytest.mark.parametrize("nome", NOMES)
def test_aula_de_ouro_valida(nome):
    a = carregar(nome)
    assert validar_estrutura(a.para_json()) == []


@pytest.mark.parametrize("nome", NOMES)
def test_tem_ramos_genericos(nome):
    assert {"por_que", "nao_entendi", "repete",
            "de_onde_veio"} <= set(carregar(nome).ramos)


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


@pytest.mark.parametrize("nome", NOMES)
def test_diz_passos_casa_com_numero_de_passos_do_calc(nome):
    # o tocador narra uma frase de diz_passos por passo do calc — contagens
    # diferentes engolem frase ou deixam passo mudo
    aula = carregar(nome)
    for beat in _todos_os_beats(aula):
        dp = beat.get("diz_passos")
        c = beat.get("calc")
        if dp is None or c is None:
            continue
        passos = CALC_CATALOGO[c["gerador"]](**c["params"]).passos
        assert len(dp) == len(passos), (nome, c["gerador"], len(dp), len(passos))


@pytest.mark.parametrize("nome", NOMES)
def test_nenhuma_fala_tem_latex(nome):
    # `diz` e `confirma` são falados: nada de barra invertida, circunflexo ou "frac"
    aula = carregar(nome)
    for beat in _todos_os_beats(aula):
        falas = [beat.get("diz", "")]
        pg = beat.get("pergunta") or {}
        falas.append(pg.get("confirma", "") or "")
        falas += list(beat.get("diz_passos") or [])
        for f in falas:
            assert "\\" not in f and "^" not in f and "frac" not in f, (nome, f)


def test_trap_spec_tem_linha_de_altura():
    # F5: o "6" só pode aparecer junto de uma linha de altura de verdade
    from autotuto.aulas import _TRAP_SPEC
    assert _TRAP_SPEC.get("segmentos"), "sem linha de altura, o '6' cota o lado oblíquo"
    assert figura(_TRAP_SPEC)[:4] == b"\x89PNG"


def test_carregar_nao_vaza_mutacao_entre_execucoes():
    # o tocador escreve nos beats; cada carregar() tem que dar um objeto novo
    a1 = carregar("trapezio")
    a1.blocos[0]["_resultado"] = "sujeira"
    a2 = carregar("trapezio")
    assert "_resultado" not in a2.blocos[0]


# ───────────────────── "de onde veio essa fórmula?" (humanizar o conteúdo)

@pytest.mark.parametrize("nome", NOMES)
def test_toda_aula_tem_de_onde_veio(nome):
    assert carregar(nome).ramos["de_onde_veio"]


@pytest.mark.parametrize("nome", NOMES)
def test_cada_aula_de_ouro_conta_a_historia_DELA(nome):
    # se a aula não sobrescreve, o aluno ouve o genérico admitindo que não sabe
    # — aceitável num plano de LLM, inaceitável numa aula escrita à mão.
    generico = RAMOS_GENERICOS["de_onde_veio"][0]["diz"]
    assert carregar(nome).ramos["de_onde_veio"][0]["diz"] != generico


def test_o_generico_admite_que_nao_sabe_em_vez_de_inventar():
    # ESTE é o teste que importa. Num plano gerado por LLM sobre um tópico
    # qualquer, o ramo genérico não faz ideia de qual fórmula é. Inventar uma
    # origem histórica ali seria a mentira que a regra única do projeto proíbe.
    texto = " ".join(b["diz"] for b in RAMOS_GENERICOS["de_onde_veio"]).lower()
    assert "não vou inventar" in texto or "nao vou inventar" in texto
    assert "não sei" in texto or "nao sei" in texto
    # e não pode citar povo, século, nem nome próprio de matemático
    for pista in ("egito", "grécia", "babilôn", "árabe", "pitágoras",
                  "euclides", "século"):
        assert pista not in texto, pista


def test_generico_devolve_a_pergunta_pro_aluno():
    # admitir que não sabe não pode virar beco sem saída: tem que convidar
    texto = " ".join(b["diz"] for b in RAMOS_GENERICOS["de_onde_veio"]).lower()
    assert "me diz" in texto or "me conta" in texto


def test_plano_de_llm_sem_historia_cai_no_generico_honesto():
    from autotuto.aulas import _com_genericos
    plano = {"titulo": "Números primos", "topico": "primos",
             "blocos": [{"diz": "um número primo só é divisível por 1 e por ele"}]}
    d = _com_genericos(plano)
    assert d["ramos"]["de_onde_veio"] == RAMOS_GENERICOS["de_onde_veio"]
