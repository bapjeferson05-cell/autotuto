"""Gerador de exercício: questão NOVA pro aluno tentar.

A regra que manda em tudo aqui: a resposta vem do `calc`, nunca de template.
Exercício e gabarito não podem ter como discordar.
"""
import pytest

from autotuto import calc
from autotuto.exercicios import (PROVA_GEOMETRIA, Exercicio, folha, gerar, serie,
                                 topicos)


@pytest.mark.parametrize("topico", topicos())
@pytest.mark.parametrize("dif", [1, 2, 3])
def test_todo_topico_gera_exercicio_bem_formado(topico, dif):
    e = gerar(topico, dificuldade=dif, semente=1234)
    assert e.enunciado and e.enunciado[0].isupper()
    assert e.enunciado.endswith(("?", ".", "= 0"))
    assert e.resposta
    assert "{" not in e.enunciado and "}" not in e.enunciado   # template preenchido
    assert e.calc["gerador"] in calc.CATALOGO


@pytest.mark.parametrize("topico", topicos())
def test_a_resposta_sai_do_calc_e_nao_do_template(topico):
    # O TESTE CENTRAL: refaz a conta pelo motor e o número tem que bater. Se
    # alguém um dia escrever a resposta à mão no molde do enunciado, isto
    # quebra — e é a única coisa que impede o gabarito de mentir.
    # Compara NÚMERO, não texto: a resposta passa por uma limpeza cosmética
    # (35.0 -> 35) que não pode ser confundida com divergência.
    e = gerar(topico, semente=99)
    r = calc.CATALOGO[e.calc["gerador"]](**e.calc["params"])
    bruto = e.resposta.split()[0]              # tira a unidade
    try:
        assert float(bruto) == pytest.approx(float(r.valor)), (topico, bruto, r.valor)
    except ValueError:                         # resposta em texto ("não existe", "15/2")
        assert bruto == str(r.valor), (topico, bruto, r.valor)


@pytest.mark.parametrize("topico", topicos())
def test_mesma_semente_da_a_mesma_questao(topico):
    # dá pra refazer a mesma folha amanhã, e dá pra testar
    assert gerar(topico, semente=7) == gerar(topico, semente=7)


@pytest.mark.parametrize("topico", topicos())
def test_serie_nao_repete_enunciado(topico):
    # enunciado repetido numa folha de treino é questão desperdiçada: o aluno
    # reconhece e responde de memória, que é o oposto do treino.
    exs = serie(topico, 5, semente=3)
    assert len({e.enunciado for e in exs}) == len(exs) == 5


def test_a_pegadinha_do_maior_que_90_aparece_na_dificuldade_alta():
    # foi ela que derrubou o aluno na prova real: 145° não tem complemento.
    # Se o treino nunca mostrar isso, ele erra de novo.
    exs = serie("complemento", 30, dificuldade=3, semente=11)
    assert any(e.resposta == "não existe" for e in exs)


def test_dificuldade_1_nunca_solta_a_pegadinha():
    # começar pelo caso impossível confunde quem está aprendendo a definição
    for s in range(12):
        exs = serie("complemento", 20, dificuldade=1, semente=s)
        assert all(e.resposta != "não existe" for e in exs), s


def test_equacao_nao_sai_com_numero_entre_parenteses():
    # "2x + (-10) = 0" é saída de computador; prova escreve "2x - 10 = 0"
    for e in serie("eq_primeiro_grau", 20, dificuldade=3, semente=4):
        assert "(-" not in e.enunciado, e.enunciado
        assert "+ -" not in e.enunciado


def test_equacao_tem_sempre_raiz_inteira():
    for e in serie("eq_primeiro_grau", 20, dificuldade=3, semente=8):
        assert float(e.resposta) == int(float(e.resposta)), e.enunciado


def test_fracao_do_enunciado_e_irredutivel():
    import math
    for e in serie("fracao_de", 25, dificuldade=3, semente=6):
        num, den = e.calc["params"]["num"], e.calc["params"]["den"]
        assert math.gcd(num, den) == 1, e.enunciado


def test_resposta_nao_carrega_ponto_zero_a_toa():
    for e in serie("area_trapezio", 10, semente=2):
        assert not e.resposta.startswith("0.") and ".0 " not in e.resposta, e.resposta


def test_vira_beat_que_o_tocador_sabe_tocar():
    from autotuto.schema import validar_estrutura
    e = gerar("pitagoras", semente=5)
    aula = {"titulo": "treino", "topico": "t", "blocos": [e.como_beat()]}
    assert validar_estrutura(aula) == []


def test_folha_da_prova_cobre_os_topicos_da_prova_real():
    exs = folha(PROVA_GEOMETRIA, quantas=2, semente=1)
    assert len(exs) == 2 * len(PROVA_GEOMETRIA)
    assert {e.topico for e in exs} == set(PROVA_GEOMETRIA)


def test_topico_inexistente_diz_quais_existem():
    with pytest.raises(ValueError) as err:
        gerar("trigonometria")
    assert "complemento" in str(err.value)      # a mensagem ensina


def test_cli_roda_e_esconde_o_gabarito_embaixo(capsys):
    from autotuto.exercicios import main
    assert main(["complemento", "4", "2"]) == 0
    saida = capsys.readouterr().out
    assert saida.index("1. Calcule") < saida.index("GABARITO")   # questões primeiro
    assert "responde TUDO antes de rolar" in saida


def test_cli_lista_e_ajuda_nao_quebram(capsys):
    from autotuto.exercicios import main
    assert main(["--lista"]) == 0
    assert main([]) == 0
    assert main(["nao_existe_isso"]) == 2


# ───── defeitos que eu mesmo encontrei revisando o próprio diff

@pytest.mark.parametrize("topico", topicos())
@pytest.mark.parametrize("dif", [1, 2, 3])
def test_serie_entrega_a_quantidade_que_prometeu(topico, dif):
    # BUG meu: `serie("pitagoras", 10)` devolvia 6 CALADO, porque a receita
    # tinha 6 pares decorados e esgotava. Folha de treino que entrega menos do
    # que o aluno pediu, sem avisar, é a folha mentindo.
    assert len(serie(topico, 10, dificuldade=dif, semente=1)) == 10


def test_serie_falha_alto_quando_nao_tem_como_encher():
    # e quando de fato não dá, tem que DIZER — com quantas dá e o que fazer.
    with pytest.raises(ValueError) as e:
        serie("pitagoras", 500, dificuldade=1)
    assert "só rende" in str(e.value) and "500" in str(e.value)


def test_ternos_pitagoricos_sao_gerados_e_todos_fecham():
    # lista decorada era jukebox voltando pela porta dos fundos. Agora vêm da
    # parametrização de Euclides — e todo par TEM que ter hipotenusa inteira.
    import math

    from autotuto.exercicios import _TERNOS
    for dif, pares in _TERNOS.items():
        assert len(pares) >= 10, dif
        for a, b in pares:
            c = math.isqrt(a * a + b * b)
            assert c * c == a * a + b * b, (a, b)


def test_dificuldade_1_de_pitagoras_e_so_a_familia_do_3_4_5():
    # não é "número menor", é a família que o aluno RECONHECE: a hipotenusa
    # sai múltipla de 5 e ele confere de cabeça. (5,12,13) no nível 1 é dar
    # terno que ele nunca viu e chamar de fácil.
    import math

    from autotuto.exercicios import _TERNOS
    for a, b in _TERNOS[1]:
        k = math.gcd(a, b)
        assert (a // k, b // k) == (3, 4), (a, b)
        assert math.isqrt(a * a + b * b) % 5 == 0
