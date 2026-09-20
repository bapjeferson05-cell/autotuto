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

    # exatamente o que planeja() devolve sem Ollama no ar
    monkeypatch.setattr(planejador, "planeja",
                        lambda *a, **k: (carregar("trapezio"),
                                         Relatorio(avisos=["plano offline (conexão recusada)"])))
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
