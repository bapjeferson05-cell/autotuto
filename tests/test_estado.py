"""test_estado.py — EstadoAula é a pilha de trilhas que segura toda a interrupção
e retomada (o coração da "conversa" do professor). Não tinha nenhum teste."""
from professor.esquema import Aula
from professor.estado import EstadoAula, Trilha


def _aula() -> Aula:
    return Aula(
        titulo="Teste",
        topico="topico_teste",
        dados={"x": 1},
        blocos=[
            {"diz": "bloco 1"},
            {"diz": "bloco 2", "figura": {"gerador": "figura", "spec": {}}},
            {"diz": "bloco 3", "calc": {"gerador": "foo", "params": {"y": 2, "x": 99}}},
        ],
        ramos={
            "ramo_a": [{"diz": "a1"}, {"diz": "a2", "figura": {"gerador": "g2"}}],
        },
    )


# ────────────────────────────────────────────────────────────────── Trilha
def test_trilha_avanca_e_esgota():
    t = Trilha([{"a": 1}, {"a": 2}])
    assert t.proximo() == {"a": 1}
    assert t.proximo() == {"a": 2}
    assert t.proximo() is None
    assert t.posicao == "2/2"


def test_trilha_posicao_antes_de_comecar():
    assert Trilha([{"a": 1}, {"a": 2}]).posicao == "0/2"


# ────────────────────────────────────────────────────────────── inicialização
def test_estado_inicial_esta_na_trilha_principal():
    e = EstadoAula(_aula())
    assert e.na_principal is True
    assert e.trilha.rotulo == "principal"
    assert e.dados == {"x": 1}


def test_dados_do_estado_e_copia_independente_da_aula():
    aula = _aula()
    e = EstadoAula(aula)
    e.dados["novo"] = 99
    assert "novo" not in aula.dados


# ────────────────────────────────────────────────────────────────── proximo()
def test_proximo_registra_figura_atual():
    e = EstadoAula(_aula())
    e.proximo()  # bloco 1, sem figura
    assert e.figura_atual is None
    e.proximo()  # bloco 2, com figura
    assert e.figura_atual == {"gerador": "figura", "spec": {}}


def test_proximo_registra_calc_e_mescla_dados_sem_sobrescrever():
    e = EstadoAula(_aula())
    e.proximo()
    e.proximo()
    e.proximo()  # bloco 3 — tem calc
    assert e.calc_atual["gerador"] == "foo"
    assert e.dados["y"] == 2  # novo — entra
    assert e.dados["x"] == 1  # já existia (vindo da aula) — calc (x=99) NÃO sobrescreve


def test_proximo_esgota_a_trilha_principal():
    e = EstadoAula(_aula())
    for _ in range(3):
        assert e.proximo() is not None
    assert e.proximo() is None


# ─────────────────────────────────────────────────────────────── entra_ramo()
def test_entra_ramo_empilha_e_devolve_os_blocos():
    e = EstadoAula(_aula())
    blocos = e.entra_ramo("ramo_a")
    assert len(blocos) == 2
    assert e.na_principal is False
    assert e.trilha.rotulo == "ramo:ramo_a"
    assert e.historico == ["ramo_a"]


def test_entra_ramo_gatilho_inexistente_nao_empilha():
    e = EstadoAula(_aula())
    assert e.entra_ramo("nao_existe") == []
    assert e.na_principal is True
    assert e.historico == []


# ─────────────────────────────────────────────────────── drena_ramo() / sai_ramo()
def test_drena_ramo_consome_tudo_e_desempilha():
    e = EstadoAula(_aula())
    e.entra_ramo("ramo_a")
    drenados = list(e.drena_ramo())
    assert len(drenados) == 2
    assert e.na_principal is True


def test_drena_ramo_registra_figura_do_ultimo_bloco_do_ramo():
    e = EstadoAula(_aula())
    e.entra_ramo("ramo_a")
    list(e.drena_ramo())
    assert e.figura_atual == {"gerador": "g2"}


def test_drena_ramo_na_principal_nao_faz_nada():
    e = EstadoAula(_aula())
    assert list(e.drena_ramo()) == []
    assert e.na_principal is True


def test_trilha_principal_fica_intacta_apos_um_ramo():
    e = EstadoAula(_aula())
    e.proximo()  # consome o bloco 1 da principal
    e.entra_ramo("ramo_a")
    list(e.drena_ramo())
    # a principal retoma do bloco 2 — não reiniciou do zero
    assert e.proximo() == {"diz": "bloco 2", "figura": {"gerador": "figura", "spec": {}}}


def test_sai_ramo_desempilha():
    e = EstadoAula(_aula())
    e.entra_ramo("ramo_a")
    e.sai_ramo()
    assert e.na_principal is True


def test_sai_ramo_na_principal_nao_quebra():
    e = EstadoAula(_aula())
    e.sai_ramo()
    assert e.na_principal is True


# ────────────────────────────────────────────────────────────────── resumo()
def test_resumo_contem_topico_dados_e_caminho():
    r = EstadoAula(_aula()).resumo()
    assert "topico_teste" in r
    assert "x=1" in r
    assert "principal" in r


def test_resumo_sem_ramos_usados_nao_menciona_ramos_usados():
    assert "ramos usados" not in EstadoAula(_aula()).resumo()


def test_resumo_com_ramo_usado_lista_o_historico():
    e = EstadoAula(_aula())
    e.entra_ramo("ramo_a")
    r = e.resumo()
    assert "ramos usados" in r
    assert "ramo_a" in r
