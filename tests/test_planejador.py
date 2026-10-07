"""test_planejador.py — só a parte pura e offline: `_saneia`. planeja() de verdade
precisa de LLM/rede, isso aqui testa só a "última linha de defesa" antes de mostrar
o plano pro aluno."""
from professor.esquema import Aula
from professor.planejador import _saneia, planeja_offline


def _bloco_ok(diz="oi"):
    return {"diz": diz, "espera": "media"}


def _bloco_gerador_fantasma():
    return {"diz": "olha essa figura", "figura": {"gerador": "hexagrama_magico"}}


# ─────── fatal na TRILHA PRINCIPAL derruba o plano: é o que o aluno vai ver
def test_gerador_impossivel_na_principal_descarta_o_plano():
    aula = Aula("Teste", [_bloco_ok(), _bloco_gerador_fantasma(), _bloco_ok("fim")])
    saneada, notas, fatais = _saneia(aula)

    assert saneada.titulo == planeja_offline().titulo
    assert fatais, "o chamador precisa conseguir detectar isso sem ler frase em português"
    assert any("hexagrama_magico" in n for n in notas)


# ─────── fatal num RAMO opcional NÃO derruba: trocar uma aula boa de círculo por
# um trapézio é uma mentira maior que a que se quis evitar
def test_gerador_impossivel_num_ramo_descarta_so_o_ramo():
    aula = Aula("Área do círculo", [_bloco_ok("b1"), _bloco_ok("b2")],
                ramos={"nao_entendi": [_bloco_ok("r1")],
                       "por_que": [_bloco_gerador_fantasma()]})
    saneada, notas, fatais = _saneia(aula)

    assert saneada.titulo == "Área do círculo", "a aula boa foi jogada fora"
    assert not fatais, "ramo opcional quebrado não torna a aula uma não-resposta"
    assert len(saneada.blocos) == 2
    assert any("por_que" in n and "descartado" in n for n in notas)
    # o ramo descartado ganha o fallback honesto em vez de simplesmente sumir
    assert saneada.ramos["por_que"]
    assert "hexagrama" not in str(saneada.ramos["por_que"])


# ─────── poda parcial dentro de um ramo não pode ser silenciosa
def test_poda_parcial_dentro_de_ramo_deixa_rastro():
    aula = Aula("Teste", [_bloco_ok()],
                ramos={"nao_entendi": [_bloco_ok("p1"), {"espera": "media"}, _bloco_ok("p3")]})
    saneada, notas, fatais = _saneia(aula)

    assert len(saneada.ramos["nao_entendi"]) == 2
    assert notas, "o bloco sumiu do ramo e ninguém ficou sabendo"
    assert not fatais


# ─────── comportamento antigo que não pode regredir
def test_bloco_sem_diz_e_podado_sem_derrubar_o_plano():
    aula = Aula("Teste", [_bloco_ok(), {"espera": "media"}, _bloco_ok("fim")])
    saneada, notas, fatais = _saneia(aula)
    assert saneada.titulo == "Teste"
    assert len(saneada.blocos) == 2
    assert any("removid" in n for n in notas)
    assert not fatais


def test_plano_totalmente_bom_nao_muda_titulo():
    aula = Aula("Teste", [_bloco_ok(), _bloco_ok("fim")])
    saneada, notas, fatais = _saneia(aula)
    assert saneada.titulo == "Teste"
    assert len(saneada.blocos) == 2
    assert not fatais
