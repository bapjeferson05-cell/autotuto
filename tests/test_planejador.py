"""test_planejador.py — só a parte pura e offline: `_saneia`. planeja() de verdade
precisa de LLM/rede, isso aqui testa só a "última linha de defesa" antes de mostrar
o plano pro aluno."""
from professor.esquema import Aula
from professor.planejador import _saneia, planeja_offline


def _bloco_ok(diz="oi"):
    return {"diz": diz, "espera": "media"}


def _bloco_gerador_fantasma():
    return {"diz": "olha essa figura", "figura": {"gerador": "hexagrama_magico"}}


# ─────── gerador inexistente derruba o PLANO INTEIRO — não é podado bloco a bloco
def test_saneia_gerador_inexistente_descarta_o_plano_inteiro():
    aula = Aula("Teste", [_bloco_ok(), _bloco_gerador_fantasma(), _bloco_ok("fim")])
    saneada, notas = _saneia(aula)

    # nunca é a aula original com o bloco ruim só removido: cai pro plano offline
    assert saneada.titulo == planeja_offline().titulo
    assert len(saneada.blocos) == len(planeja_offline().blocos)
    assert any("hexagrama_magico" in n for n in notas)


def test_saneia_gerador_inexistente_num_ramo_tambem_derruba_o_plano():
    aula = Aula("Teste", [_bloco_ok()], ramos={"por_que": [_bloco_gerador_fantasma()]})
    saneada, notas = _saneia(aula)
    assert saneada.titulo == planeja_offline().titulo
    assert any("hexagrama_magico" in n for n in notas)


# ─────── um bloco quebrado por outro motivo continua só sendo podado (comportamento
# antigo, não regrediu)
def test_saneia_bloco_sem_diz_e_podado_sem_derrubar_o_plano():
    aula = Aula("Teste", [_bloco_ok(), {"espera": "media"}, _bloco_ok("fim")])
    saneada, notas = _saneia(aula)
    assert saneada.titulo == "Teste"
    assert len(saneada.blocos) == 2
    assert any("removid" in n for n in notas)


def test_saneia_plano_totalmente_bom_nao_muda_titulo():
    aula = Aula("Teste", [_bloco_ok(), _bloco_ok("fim")])
    saneada, notas = _saneia(aula)
    assert saneada.titulo == "Teste"
    assert len(saneada.blocos) == 2
