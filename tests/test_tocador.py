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


def test_modo_gravacao_scriptado():
    est = Tocador(pausas=False, cerebro=None).toca(
        carregar("trapezio"),
        interrupcoes={2: "por_que_div_2"}, respostas={4: "vira um triângulo"})
    assert "por_que_div_2" in est.historico


def test_desenha_figura_e_passos_do_calc():
    rotulos = []
    Tocador(falar=lambda t: None, ouvir=lambda s: None,
            desenhar=lambda png, rot: rotulos.append((rot, isinstance(png, bytes))),
            pausas=False, cerebro=None).toca(carregar("pitagoras"))
    assert any(r == "figura" and ok for r, ok in rotulos)          # spec inline
    assert any(r.startswith("passo") and ok for r, ok in rotulos)  # calc na lousa
