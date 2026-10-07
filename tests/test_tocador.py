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


# ───── beat de PERGUNTA: falar durante a pergunta é RESPONDER, não interromper
def _aula_com_pergunta():
    return Aula(
        titulo="Teste",
        blocos=[{"diz": "bloco 1"},
                {"diz": "e se a base encolhesse? que figura vira?",
                 "pergunta": {"escuta_s": 12, "senao": "por_que",
                              "acerta": ["triangulo", "triângulo"],
                              "confirma": "Isso — vira um triângulo."}},
                {"diz": "bloco 3"}],
        ramos={"por_que": [{"diz": "ramo por que"}], "e_triangulo": [{"diz": "ramo triangulo"}]},
    )


def test_resposta_certa_durante_a_pergunta_nao_vira_interrupcao():
    # a tela manda apertar 0 pra responder; se isso virar barge, o aluno que ACERTOU
    # é mandado pro ramo de quem errou e o confirma nunca é dito.
    ditas = []

    def falar(txt):
        ditas.append(txt)
        if txt.startswith("e se a base"):
            return "acho que vira um triângulo"
        return None

    est = Tocador(falar=falar, pausas=False).toca(_aula_com_pergunta())

    assert "Isso — vira um triângulo." in ditas, "o confirma (fading) não foi dito"
    assert est.historico == [], f"entrou em ramo indevidamente: {est.historico}"
    assert "bloco 3" in ditas


def test_resposta_errada_durante_a_pergunta_vai_pro_ramo_senao():
    ditas = []

    def falar(txt):
        ditas.append(txt)
        if txt.startswith("e se a base"):
            return "sei lá, nenhuma ideia"
        return None

    est = Tocador(falar=falar, pausas=False).toca(_aula_com_pergunta())
    assert est.historico == ["por_que"]
    assert "Isso — vira um triângulo." not in ditas


# ───── tecla apertada numa fala de transição não pode ser destruída
def test_interrupcao_durante_fala_de_transicao_nao_se_perde():
    ditas = []
    aula = Aula(titulo="Teste",
                blocos=[{"diz": "b1"}, {"diz": "b2"}],
                ramos={"por_que": [{"diz": "r1"}], "nao_entendi": [{"diz": "n1"}]})

    def falar2(txt):
        ditas.append(txt)
        if txt == "b1":
            return "por que isso?"
        if txt == "Voltando de onde a gente parou.":
            return "não entendi essa parte"
        return None

    est = Tocador(falar=falar2, pausas=False).toca(aula)
    assert "nao_entendi" in est.historico, (
        "a tecla apertada na fala de transição foi destruída", ditas)


# ───── barge não classificado DENTRO de um ramo também admite
def test_barge_nao_classificado_dentro_do_ramo_admite():
    ditas = []

    def falar(txt):
        ditas.append(txt)
        if txt == "b1":
            return "por que isso?"
        if txt == "r1":
            return "blablabla sem sentido"
        return None

    aula = Aula(titulo="Teste", blocos=[{"diz": "b1"}, {"diz": "b2"}],
                ramos={"por_que": [{"diz": "r1"}, {"diz": "r2"}]})
    Tocador(falar=falar, pausas=False).toca(aula)
    assert sum("Essa eu não preparei agora" in d for d in ditas) >= 1, ditas
