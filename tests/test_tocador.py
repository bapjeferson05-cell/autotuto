"""test_tocador.py — a regra de ouro no barge-in: interrupção que não classifica
em ramo nenhum não pode fingir que entendeu (não tinha teste dedicado)."""
from professor.esquema import Aula
from professor.tocador import Tocador


def _aula():
    return Aula(
        titulo="Teste",
        blocos=[{"diz": "bloco 1"}, {"diz": "bloco 2"}, {"diz": "bloco 3"}],
        ramos={"por_que": [{"diz": "ramo por que"}]},
    )


def test_barge_nao_classificado_nao_entra_em_ramo_nenhum():
    # "beleza, entendi" não bate em nenhuma regra do classificador (ver
    # classificador.py __main__) — não pode virar "por_que" por default.
    ditas = []

    def falar(txt):
        ditas.append(txt)
        if txt == "bloco 1":
            return "beleza, entendi"
        return None

    est = Tocador(falar=falar, pausas=False).toca(_aula())

    assert est.historico == []
    assert "Essa eu não preparei agora" in " ".join(ditas)
    assert "bloco 2" in ditas and "bloco 3" in ditas   # a aula continuou normal


def test_barge_classificado_entra_no_ramo_certo_sem_o_fallback_honesto():
    ditas = []

    def falar(txt):
        ditas.append(txt)
        if txt == "bloco 1":
            return "por que que é assim?"
        return None

    est = Tocador(falar=falar, pausas=False).toca(_aula())

    assert est.historico == ["por_que"]
    assert "Essa eu não preparei agora" not in " ".join(ditas)
    assert "ramo por que" in ditas
