"""test_validador.py — o portão entre o LLM e os geradores. Nunca tinha teste
dedicado, apesar de ser o que decide se um plano do LLM é seguro de mostrar pro
aluno (e o que devolve pro loop de correção em planejador.py)."""
import pytest

from professor import validador
from professor.aulas import carregar
from professor.esquema import GERADORES, Param, _TIPOS_QUAD, _TIPOS_TRI


# ─────────────────────────────────────────────────────────────────── _coage
def test_coage_int_e_float():
    assert validador._coage("5", Param("int"))[0] == 5
    assert validador._coage(5, Param("float"))[0] == 5.0


def test_coage_bool_aceita_variacoes_de_string():
    assert validador._coage("true", Param("bool"))[0] is True
    assert validador._coage("sim", Param("bool"))[0] is True
    assert validador._coage("nao", Param("bool"))[0] is False


def test_coage_nao_converte_da_erro():
    v, e = validador._coage("abc", Param("int"))
    assert v is None and e is not None


def test_coage_opcoes_fora_do_conjunto_da_erro():
    v, e = validador._coage("hexagono", Param("str", opcoes=("triangulo", "quadrado")))
    assert v is None and "fora do conjunto" in e


def test_coage_faixa_fora_do_intervalo_da_erro():
    v, e = validador._coage(2, Param("int", faixa=(3, 10)))
    assert v is None and "fora da faixa" in e


def test_coage_faixa_dentro_do_intervalo_ok():
    assert validador._coage(5, Param("int", faixa=(3, 10)))[0] == 5


def test_coage_dict_e_list_exigem_o_tipo_certo():
    v, e = validador._coage([1, 2], Param("dict"))
    assert v is None and "objeto" in e
    v, e = validador._coage({"a": 1}, Param("list"))
    assert v is None and "lista" in e


# ─────────────────────────────────────────────────────────── _valida_chamada
def test_valida_chamada_gerador_inexistente():
    _, erros = validador._valida_chamada({"gerador": "nao_existe"}, "figura")
    assert any("não existe" in e for e in erros)


def test_valida_chamada_familia_errada():
    # 'area_trapezio' é 'calc', não 'figura'
    _, erros = validador._valida_chamada(
        {"gerador": "area_trapezio", "params": {"B": 1, "b": 1, "h": 1}}, "figura")
    assert any("não cabe" in e for e in erros)


def test_valida_chamada_falta_parametro_obrigatorio():
    _, erros = validador._valida_chamada({"gerador": "triangulo", "params": {}}, "figura")
    assert any("falta o parâmetro obrigatório" in e for e in erros)


def test_valida_chamada_aplica_default_quando_omitido():
    params, erros = validador._valida_chamada(
        {"gerador": "poligono_regular", "params": {"n": 6}}, "figura")
    assert erros == []
    assert params["r"] == 4.0  # default do Param


def test_valida_chamada_parametro_desconhecido():
    _, erros = validador._valida_chamada(
        {"gerador": "triangulo", "params": {"tipo": "retangulo", "cor_favorita": "azul"}}, "figura")
    assert any("desconhecidos" in e for e in erros)


def test_valida_chamada_figura_usa_spec_nao_params():
    params, erros = validador._valida_chamada(
        {"gerador": "figura", "spec": {"pontos": {"A": [0, 0], "B": [1, 0]},
                                       "segmentos": [{"de": "A", "para": "B"}]}}, "figura")
    assert erros == []
    assert "spec" in params


# ───────────────────────────────────────────────────────── _valida_spec_figura
def test_spec_figura_chave_desconhecida_sugere_a_certa():
    erros = validador._valida_spec_figura({"pontos": {}, "circulo": []})
    assert any("circulos" in e for e in erros)


def test_spec_figura_ponto_malformado():
    erros = validador._valida_spec_figura({"pontos": {"A": [0, 0, 0]}})
    assert any("ponto 'A'" in e for e in erros)


def test_spec_figura_sem_nenhum_elemento():
    erros = validador._valida_spec_figura({"pontos": {}})
    assert any("não desenha nada" in e for e in erros)


def test_spec_figura_poligono_referencia_ponto_inexistente():
    erros = validador._valida_spec_figura({
        "pontos": {"A": [0, 0], "B": [1, 0]},
        "poligonos": [{"vs": ["A", "B", "Z"]}],
    })
    assert any("polígono.vs" in e for e in erros)


def test_spec_figura_segmento_referencia_ponto_inexistente():
    erros = validador._valida_spec_figura({
        "pontos": {"A": [0, 0]},
        "segmentos": [{"de": "A", "para": "Z"}],
    })
    assert any("segmento.para" in e for e in erros)


def test_spec_figura_circulo_sem_raio_nem_centro():
    erros = validador._valida_spec_figura({"pontos": {}, "circulos": [{}]})
    assert any("precisa de 'r'" in e for e in erros)
    assert any("precisa de 'centro'" in e for e in erros)


def test_spec_figura_valida_nao_reporta_nada():
    erros = validador._valida_spec_figura({
        "pontos": {"A": [0, 0], "B": [1, 0], "C": [1, 1]},
        "poligonos": [{"vs": ["A", "B", "C"], "preenche": True}],
    })
    assert erros == []


# ───────────────────────────── _mat_figura: consistência renderer × validador
# formas._TRI / formas._quad_pts são as coordenadas REAIS que o renderer usa —
# se o validador reprovasse alguma, um plano usando essa figura seria rejeitado
# à toa (ou pior: o LLM entraria num loop de correção sem conseguir corrigir).
@pytest.mark.parametrize("tipo", _TIPOS_TRI)
def test_mat_figura_triangulo_bate_com_as_coordenadas_do_renderer(tipo):
    assert validador._mat_figura("triangulo", {"tipo": tipo}) == []


@pytest.mark.parametrize("tipo", _TIPOS_QUAD)
def test_mat_figura_quadrilatero_bate_com_as_coordenadas_do_renderer(tipo):
    assert validador._mat_figura("quadrilatero", {"tipo": tipo}) == []


def test_mat_figura_estrela_k_valido():
    assert validador._mat_figura("estrela", {"n": 5, "k": 2}) == []


def test_mat_figura_estrela_k_invalido():
    problemas = validador._mat_figura("estrela", {"n": 5, "k": 4})
    assert problemas != []


def test_mat_figura_funcao_valida():
    assert validador._mat_figura("funcao", {"expr": "x**2", "x0": -5, "x1": 5}) == []


def test_mat_figura_funcao_expr_invalida():
    problemas = validador._mat_figura("funcao", {"expr": "isso não é python(("})
    assert any("expr inválida" in p for p in problemas)


def test_mat_figura_funcao_sem_valor_finito_no_intervalo():
    # log(x) com x só negativo — não dá nenhum valor finito real
    problemas = validador._mat_figura("funcao", {"expr": "log(x)", "x0": -10, "x1": -1})
    assert problemas != []


# ─────────────────────────────────────────────────────────────── _mat_calc
def test_mat_calc_valido_nao_reporta_nada():
    assert validador._mat_calc("area_trapezio", {"B": 18, "b": 10, "h": 6}) == []


def test_mat_calc_estoura_e_reportado_sem_lancar_excecao():
    problemas = validador._mat_calc("area_trapezio", {"B": 18, "b": 10})  # falta 'h'
    assert any("estourou" in p for p in problemas)


def test_mat_calc_resultado_negativo_em_grandeza_que_nao_pode_ser():
    problemas = validador._mat_calc("area_retangulo", {"base": -5, "altura": 2})
    assert any("negativo" in p for p in problemas)


def test_mat_calc_pitagoras_exige_exatamente_dois_dos_tres():
    assert validador._mat_calc("pitagoras", {"a": 3, "b": 4, "c": 5}) != []  # os 3 — demais
    assert validador._mat_calc("pitagoras", {"a": 3}) != []                  # só 1 — de menos
    assert validador._mat_calc("pitagoras", {"a": 3, "b": 4}) == []          # 2 — certo


# ────────────────────────────────────────────────────────────── valida_bloco
def test_valida_bloco_sem_diz_e_invalido():
    rel = validador.valida_bloco({"espera": "media"})
    assert not rel.ok


def test_valida_bloco_espera_invalida():
    rel = validador.valida_bloco({"diz": "oi", "espera": "rapidissima"})
    assert not rel.ok


def test_valida_bloco_pergunta_sem_senao():
    rel = validador.valida_bloco({"diz": "?", "pergunta": {"escuta_s": 10}})
    assert not rel.ok
    assert any("senao" in p for p in rel.problemas)


def test_valida_bloco_pergunta_senao_fora_dos_ramos():
    rel = validador.valida_bloco({"diz": "?", "pergunta": {"senao": "fantasma"}},
                                  ramos_validos={"nao_entendi"})
    assert not rel.ok


def test_valida_bloco_pergunta_escuta_s_fora_da_faixa():
    rel = validador.valida_bloco({"diz": "?", "pergunta": {"senao": "x", "escuta_s": 1}},
                                  ramos_validos={"x"})
    assert not rel.ok


def test_valida_bloco_minimo_valido():
    rel = validador.valida_bloco({"diz": "Olá", "espera": "media"})
    assert rel.ok


def test_valida_bloco_bloco_vazio():
    rel = validador.valida_bloco({})
    assert not rel.ok


# ───────────────────────────────────────────── gerador inexistente é FATAL,
# não só mais um "problema" recuperável (ver planejador._saneia)
def test_valida_bloco_figura_com_gerador_inexistente_e_fatal():
    rel = validador.valida_bloco({"diz": "olha", "figura": {"gerador": "hexagrama_magico"}})
    assert not rel.ok
    assert rel.fatais
    assert any("hexagrama_magico" in f for f in rel.fatais)


def test_valida_bloco_calc_com_gerador_inexistente_e_fatal():
    rel = validador.valida_bloco({"diz": "olha",
                                  "calc": {"gerador": "raiz_cubica_magica", "params": {}}})
    assert not rel.ok
    assert rel.fatais
    assert any("raiz_cubica_magica" in f for f in rel.fatais)


def test_valida_bloco_gerador_existente_mas_com_erro_nao_e_fatal():
    # 'triangulo' existe — faltar um parâmetro é recuperável, não é a mesma mentira
    rel = validador.valida_bloco({"diz": "olha", "figura": {"gerador": "triangulo",
                                                             "params": {}}})
    assert not rel.ok
    assert not rel.fatais


# ─────────────────────────────────────────────────────────────── valida_aula
def test_valida_aula_da_ouro_trapezio_e_100_por_cento_valida():
    rel = validador.valida_aula(carregar("trapezio"))
    assert rel.ok, rel.problemas


def test_valida_aula_sem_titulo():
    rel = validador.valida_aula({"titulo": "", "blocos": [{"diz": "oi"}]})
    assert any("titulo" in p for p in rel.problemas)


def test_valida_aula_sem_blocos():
    rel = validador.valida_aula({"titulo": "X", "blocos": []})
    assert any("blocos" in p for p in rel.problemas)


def test_valida_aula_ramo_vazio_e_invalido():
    rel = validador.valida_aula({
        "titulo": "X", "blocos": [{"diz": "oi"}], "ramos": {"nao_entendi": []},
    })
    assert any("ramos['nao_entendi']" in p for p in rel.problemas)


def test_valida_aula_propaga_erro_de_bloco_dentro_de_ramo():
    rel = validador.valida_aula({
        "titulo": "X", "blocos": [{"diz": "oi"}],
        "ramos": {"nao_entendi": [{"espera": "media"}]},  # sem 'diz'
    })
    assert not rel.ok
