"""Testes do tocador — o loop e a interrupção de 3 camadas.

O coração do sistema: o professor ou responde de verdade, ou admite que não
preparou aquilo. Nunca finge. Estes testes travam esse comportamento.
"""
from autotuto.aulas import carregar
from autotuto.tocador import Tocador, HONESTO


def roda(nome, *, barge=None, quando=2, resp=None, cerebro=None):
    """Toca a aula `nome` capturando tudo que foi falado.

    barge: se dado, o aluno "interrompe" com esse texto na `quando`-ésima fala.
    resp:  o que o `ouvir` devolve (resposta a um beat de pergunta).
    """
    L = []
    n = [0]

    def falar(t):
        L.append(t)
        n[0] += 1
        return barge if (barge and n[0] == quando) else None

    est = Tocador(falar=falar, ouvir=lambda s: resp,
                  pausas=False, cerebro=cerebro).toca(carregar(nome))
    return est, L


def test_toca_a_aula_inteira():
    est, L = roda("pitagoras")
    assert "pitagoras" in est.resumo() and len(L) >= 4


def test_interrupcao_classificada_entra_no_ramo():
    est, L = roda("pitagoras", barge="mas por que isso funciona?")
    assert est.historico == ["por_que"]


def test_interrupcao_fora_do_script_e_honesta_e_retoma():
    est, L = roda("pitagoras", barge="quanto custa o pedreiro", cerebro=None)
    assert any(HONESTO in x for x in L)
    assert est.historico == []                       # NÃO entrou em ramo nenhum
    assert "deixa eu achar um jeito melhor" not in " ".join(L).lower()


def test_camada_2_roteia_quando_regex_falha():
    fake = lambda fala, ctx, ramos: "nao_entendi" if "boiando" in fala else None
    est, L = roda("pitagoras", barge="tô boiando total", cerebro=fake)
    assert est.historico == ["nao_entendi"]


def test_cerebro_devolvendo_lixo_e_ignorado():
    est, L = roda("pitagoras", barge="xyz", cerebro=lambda *a: "ramo_fantasma")
    assert est.historico == [] and any(HONESTO in x for x in L)


def test_pergunta_nao_sei_acolhe_e_vai_pro_senao():
    est, L = roda("trapezio", resp="sei lá, não faço ideia")
    assert any("não saber" in x.lower() for x in L)
    b = next(x for x in carregar("trapezio").blocos if x.get("pergunta"))
    assert est.historico == [b["pergunta"]["senao"]]


def test_pergunta_resposta_certa_faz_fading():
    est, L = roda("trapezio", resp="acho que vira um triângulo")
    assert est.historico == []                       # pulou a derivação, sem ramo


def test_acerto_hedgeado_nao_vira_nao_sei():
    # F8: "deve ser" casa o regex _NAO_SABE, mas a resposta está CERTA -> fading,
    # não "Tranquilo não saber".
    est, L = roda("trapezio", resp="deve ser um triângulo")
    assert est.historico == []
    assert not any("não saber" in x.lower() for x in L)


def test_barge_no_beat_da_formula_nao_perde_o_calc():
    # F1: interromper o `diz` do beat da fórmula (que tem `calc`) não pode fazer
    # a fórmula + a narração do resultado sumirem.
    rotulos, L = [], []

    def falar(t):
        L.append(t)
        return "quanto custa o pedreiro" if t.startswith("A fórmula soma") else None

    Tocador(falar=falar, ouvir=lambda s: "triângulo",
            desenhar=lambda png, rot: rotulos.append(rot),
            pausas=False, cerebro=None).toca(carregar("trapezio"))
    assert any(HONESTO in x for x in L)               # não casou nada -> honesto
    assert any(r.startswith("passo") for r in rotulos)   # a fórmula voltou pra lousa
    assert any("oitenta e quatro" in x.lower() for x in L)  # o resultado foi dito


def test_barge_dentro_do_ramo_sem_match_e_honesto():
    # F2: interrupção dentro de um ramo que não casa em nenhuma camada -> HONESTO
    # falado e o ramo termina (não troca de ramo, não ignora o aluno).
    seen = []

    def falar(t):
        seen.append(t)
        if t.startswith("A parede e o chão"):
            return "mas por que isso funciona?"       # entra no ramo por_que
        if t.startswith("Desenha um quadrado"):
            return "quanto ganha o pedreiro por hora"  # barge dentro do ramo
        return None

    est = Tocador(falar=falar, ouvir=lambda s: None,
                  pausas=False, cerebro=None).toca(carregar("pitagoras"))
    assert any(HONESTO in x for x in seen)
    assert est.historico == ["por_que"]              # o ramo terminou, sem desvio


def test_gerador_torto_nao_derruba_a_sessao():
    # F7: aula gerada com gerador/params inválidos -> loga e pula, a aula segue.
    from autotuto.schema import Aula
    aula = Aula.de_json({
        "titulo": "torta", "topico": "t", "dados": {},
        "blocos": [
            {"diz": "um", "figura": {"gerador": "nao_existe", "params": {}}},
            {"diz": "dois", "calc": {"gerador": "area_trapezio", "params": {"x": 1}},
             "mostra_passos": True},
            {"diz": "tres"},
        ],
        "ramos": {},
    })
    L = []
    Tocador(falar=lambda t: L.append(t) or None, ouvir=lambda s: None,
            desenhar=lambda p, r: None, pausas=False, cerebro=None).toca(aula)
    assert L == ["um", "dois", "tres"]


def test_modo_gravacao_scriptado():
    # o beat de pergunta do trapézio é o 3º beat principal (n_princ == 3).
    est = Tocador(pausas=False, cerebro=None).toca(
        carregar("trapezio"),
        interrupcoes={2: "por_que_div_2"},
        respostas={3: "acho que vira um triângulo"})
    # interrupção scriptada dispara o ramo; a resposta certa à pergunta faz
    # fading (confirma + pula a derivação) -> nenhum ramo a mais.
    assert est.historico == ["por_que_div_2"]


def test_desenha_figura_e_passos_do_calc():
    rotulos = []
    Tocador(falar=lambda t: None, ouvir=lambda s: None,
            desenhar=lambda png, rot: rotulos.append((rot, isinstance(png, bytes))),
            pausas=False, cerebro=None).toca(carregar("pitagoras"))
    assert any(r == "figura" and ok for r, ok in rotulos)          # spec inline
    assert any(r.startswith("passo") and ok for r, ok in rotulos)  # calc na lousa
