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


# ───── a recusa honesta quando o planejador cai no plano offline
# (achado atacando a demo: planeja() sem LLM devolve a aula de ouro do TRAPÉZIO
#  com rel.ok=True — tocar aquilo responderia "círculo" com trapézio)

class _VisorFake:
    def __init__(self):
        self.falas, self.estados, self.tocou = [], [], False

    def mostrar_fala(self, txt):
        self.falas.append(txt)

    def estado(self, nome):
        self.estados.append(nome)

    def falar(self, txt):                 # só é chamado se a aula FOR tocada
        self.tocou = True
        return None

    def desenhar(self, png, rotulo=""):
        self.tocou = True

    def resumo(self, txt):
        pass

    def pop_injecao(self):
        return None


def test_planejador_offline_recusa_em_vez_de_tocar_trapezio(monkeypatch):
    from professor import cli, planejador
    from professor.aulas import carregar
    from professor.validador import Relatorio

    # exatamente o que planeja() devolve sem Ollama no ar. O gate olha `fatais`,
    # não a frase em português — reescrever o aviso não pode desligar a regra.
    monkeypatch.setattr(planejador, "planeja",
                        lambda *a, **k: (carregar("trapezio"),
                                         Relatorio(avisos=["qualquer frase, em qualquer idioma"],
                                                   fatais=["a aula devolvida não é sobre o pedido"])))
    v = _VisorFake()
    cli._tenta_planejador(v, "área do círculo")

    assert not v.tocou, "tocou uma aula de trapézio pra quem pediu círculo"
    assert any("Não consegui montar" in f for f in v.falas)
    assert any("círculo" in f for f in v.falas)


def test_planejador_com_plano_de_verdade_toca_normal(monkeypatch):
    from professor import cli, planejador
    from professor.esquema import Aula
    from professor.validador import Relatorio

    monkeypatch.setattr(planejador, "planeja",
                        lambda *a, **k: (Aula("Círculo", [{"diz": "olha o círculo"}]),
                                         Relatorio()))
    v = _VisorFake()
    cli._tenta_planejador(v, "círculo")
    assert v.tocou


# ───── porta ocupada: rodar a demo duas vezes cuspia OSError na tela
def _ocupa(porta):
    import socket
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", porta))
    s.listen(1)
    return s


def test_abre_visor_cai_pra_proxima_porta_quando_a_8080_esta_ocupada():
    from professor import cli

    ocupada = _ocupa(cli._PORTAS[0])
    try:
        v = cli._abre_visor()
        try:
            assert v.porta == cli._PORTAS[1]
        finally:
            v.stop()
    finally:
        ocupada.close()


def test_abre_visor_com_todas_ocupadas_sai_com_mensagem_e_nao_traceback():
    import pytest

    from professor import cli

    socks = [_ocupa(p) for p in cli._PORTAS]
    try:
        with pytest.raises(SystemExit) as e:
            cli._abre_visor()
        assert "ocupadas" in str(e.value)
    finally:
        for s in socks:
            s.close()


# ───── resolve() precisa aceitar frase natural, senão a caixa do visor manda
# pro LLM uma aula que existe pronta no catálogo
def test_resolve_aceita_frase_natural():
    from professor.cli import resolve
    assert resolve("área do trapézio") == "trapezio"
    assert resolve("teorema de pitágoras") == "pitagoras"
    assert resolve("quero entender a hipotenusa") == "pitagoras"
    assert resolve("equação do primeiro grau") == "eq_primeiro_grau"
    assert resolve("quanto custam 5 cadernos") == "regra_de_tres"


def test_resolve_continua_dizendo_nao_pro_que_nao_existe():
    from professor.cli import resolve
    assert resolve("área do círculo") is None
    assert resolve("fração") is None
    assert resolve("banana com farofa") is None


def test_ouvir_teclado_respeita_a_janela_anunciada():
    """o terminal anuncia 'esperando resposta (12s)'; o teto de 8s tratava quem
    respondia no nono segundo como quem ficou calado."""
    import time as _t

    from professor import cli

    class _V:
        def __init__(self):
            self.chamadas = 0

        def pop_injecao(self):
            self.chamadas += 1
            return "respondi tarde" if self.chamadas > 3 else None

    v = _V()
    t0 = _t.monotonic()
    assert cli._ouvir_teclado(v, 12) == "respondi tarde"
    assert _t.monotonic() - t0 < 12, "não devia esperar a janela toda depois de ouvir"
