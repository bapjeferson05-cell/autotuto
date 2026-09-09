"""aulas.py — aulas de ouro, escritas à mão.

Não são geradas por LLM. São a referência: a pedagogia que a gente QUER, no schema
do projeto. Servem pra três coisas:
  1. o MVP da Maratona (o Ciclo do Trapézio roda daqui);
  2. few-shot no prompt do planejador (o LLM copia o padrão);
  3. teste de fogo do renderizador — se `figura` desenha isso, desenha o resto.

    from professor.aulas import carregar
    aula = carregar("trapezio")
"""
from __future__ import annotations

from professor.esquema import Aula

# trapézio isósceles: base maior 18 (embaixo), base menor 10 (em cima), altura 6
_A, _B, _C, _D = [0, 0], [18, 0], [14, 6], [4, 6]


def _trap(**mais):
    base = {"pontos": {"A": _A, "B": _B, "C": _C, "D": _D},
            "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
            "mostrar_pontos": False, "nomear_pontos": False}
    for k, v in mais.items():
        if k in base and isinstance(base[k], list):
            base[k] = base[k] + v
        else:
            base[k] = v
    return {"gerador": "figura", "spec": base}


TRAPEZIO: dict = {
    "titulo": "Área do trapézio — o terreno",
    "topico": "area_trapezio",
    "dados": {"B": 18, "b": 10, "h": 6, "area": 84},
    "blocos": [
        {"diz": "Olha esse terreno. Quatro lados, e o de baixo é paralelo ao de cima. "
                "Isso é um trapézio.",
         "figura": _trap(marcas=[{"tipo": "par", "de": "A", "para": "B", "n": 1},
                                 {"tipo": "par", "de": "D", "para": "C", "n": 1}],
                         rotulos=[{"xy": [9, -2.4], "texto": r"\text{terreno}", "tam": 15}]),
         "espera": "media"},
        {"diz": "As duas bases. A de baixo, a maior, tem dezoito metros. A de cima, a menor, tem dez.",
         "figura": _trap(segmentos=[{"de": "A", "para": "B", "cor": "destaque", "lw": 5},
                                    {"de": "D", "para": "C", "cor": "destaque", "lw": 5}],
                         cotas=[{"de": "A", "para": "B", "texto": "18", "lado": -1},
                                {"de": "D", "para": "C", "texto": "10", "lado": 1}]),
         "espera": "media"},
        {"diz": "A distância entre as duas bases é a altura. Aqui, seis metros — sempre "
                "perpendicular às bases.",
         "figura": {"gerador": "figura", "spec": {
             "pontos": {"A": _A, "B": _B, "C": _C, "D": _D, "P": [9, 0], "Q": [9, 6]},
             "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
             "segmentos": [{"de": "P", "para": "Q", "rotulo": "h = 6", "cor": "azul",
                            "lw": 4, "ls": "--", "desloca": 1.6}],
             "angulos": [{"em": "P", "de": "B", "para": "Q", "reto": True}],
             "mostrar_pontos": False, "nomear_pontos": False}},
         "espera": "media"},
        {"diz": "A área do trapézio: soma as duas bases, multiplica pela altura, e divide por dois.",
         "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
         "mostra_passos": True, "espera": "longa"},
        {"diz": "Oitenta e quatro metros quadrados. Esse é o tamanho do terreno.",
         "espera": "media"},
    ],
    "ramos": {
        # "por que dividido por dois?"
        "por_que_div_2": [
            {"diz": "Boa pergunta. Se o terreno fosse um retângulo com a base maior — dezoito "
                    "por seis — a área seria bem maior que a real.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B, "C": _C, "D": _D, "R": [0, 6], "S": [18, 6]},
                 "poligonos": [{"vs": ["A", "B", "S", "R"], "preenche": False, "cor": "verm",
                                "lw": 2, "ls": "--"},
                               {"vs": ["A", "B", "C", "D"], "preenche": True}],
                 "rotulos": [{"xy": [9, 7.4], "texto": r"18\times 6", "cor": "verm", "tam": 14}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "E com a base menor — dez por seis — a área seria menor que a real. "
                    "O trapézio fica no meio dos dois.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B, "C": _C, "D": _D, "E": [4, 0], "F": [14, 0]},
                 "poligonos": [{"vs": ["E", "F", "C", "D"], "preenche": False, "cor": "azul",
                                "lw": 2, "ls": "--"},
                               {"vs": ["A", "B", "C", "D"], "preenche": True}],
                 "rotulos": [{"xy": [9, 3], "texto": r"10\times 6", "cor": "azul", "tam": 14}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "Então a gente usa a média das bases: dezoito mais dez, dividido por dois, "
                    "dá quatorze. Um retângulo de quatorze por seis tem exatamente a área do trapézio.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B, "C": _C, "D": _D,
                            "G": [2, 0], "H": [16, 0], "I": [16, 6], "J": [2, 6]},
                 "poligonos": [{"vs": ["G", "H", "I", "J"], "preenche": True, "cor": "verde",
                                "alpha": 0.13, "lw": 2},
                               {"vs": ["A", "B", "C", "D"], "preenche": False}],
                 "cotas": [{"de": "G", "para": "H", "texto": "14", "lado": -1}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "longa"},
        ],
        # "não entendi"
        "nao_entendi": [
            {"diz": "Sem pressa, vou por partes. Primeiro só a base de baixo: dezoito metros.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B},
                 "segmentos": [{"de": "A", "para": "B", "cor": "destaque", "lw": 5}],
                 "cotas": [{"de": "A", "para": "B", "texto": "18", "lado": -1}],
                 "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "Agora a base de cima: dez metros.",
             "figura": _trap(segmentos=[{"de": "D", "para": "C", "cor": "destaque", "lw": 5}],
                             cotas=[{"de": "D", "para": "C", "texto": "10", "lado": 1}]),
             "espera": "media"},
            {"diz": "Soma as duas: vinte e oito. Vezes a altura, seis: cento e sessenta e oito. "
                    "Divide por dois: oitenta e quatro.",
             "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
             "mostra_passos": True, "espera": "longa"},
        ],
        # "e se fosse um triângulo?"
        "e_triangulo": [
            {"diz": "Imagina a base menor encolhendo. Nove... cinco... até virar um ponto só. "
                    "O trapézio virou um triângulo.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B, "T": [9, 6]},
                 "poligonos": [{"vs": ["A", "B", "T"], "preenche": True}],
                 "cotas": [{"de": "A", "para": "B", "texto": "18", "lado": -1}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "E a fórmula continua valendo: a base menor virou zero. Dezoito mais zero, "
                    "vezes seis, sobre dois. Que é base vezes altura sobre dois — a fórmula do triângulo.",
             "calc": {"gerador": "area_triangulo", "params": {"base": 18, "altura": 6}},
             "mostra_passos": True, "espera": "longa"},
        ],
        # "tem outro jeito? / não decorei a fórmula"
        "decompor": [
            {"diz": "Se não lembra a fórmula, dá pra cortar o trapézio. Duas linhas verticais "
                    "nas pontas da base de cima.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B, "C": _C, "D": _D, "E": [4, 0], "F": [14, 0]},
                 "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
                 "segmentos": [{"de": "D", "para": "E", "cor": "azul", "ls": "--"},
                               {"de": "C", "para": "F", "cor": "azul", "ls": "--"}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "No meio sobra um retângulo: dez de base, seis de altura. Área sessenta.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"E": [4, 0], "F": [14, 0], "C": _C, "D": _D},
                 "poligonos": [{"vs": ["E", "F", "C", "D"], "preenche": True, "cor": "verde"}],
                 "cotas": [{"de": "E", "para": "F", "texto": "10", "lado": -1}],
                 "rotulos": [{"xy": [9, 3], "texto": r"10\times 6 = 60", "tam": 13}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "Nas pontas, dois triângulos iguais: base quatro, altura seis, doze cada. "
                    "Sessenta mais doze mais doze: oitenta e quatro. Mesmo resultado.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B, "C": _C, "D": _D, "E": [4, 0], "F": [14, 0]},
                 "poligonos": [{"vs": ["A", "E", "D"], "preenche": True, "cor": "roxo"},
                               {"vs": ["F", "B", "C"], "preenche": True, "cor": "roxo"},
                               {"vs": ["E", "F", "C", "D"], "preenche": True, "cor": "verde"}],
                 "cotas": [{"de": "A", "para": "E", "texto": "4", "lado": -1}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "longa"},
        ],
    },
}

# ═══════════════════════════════════════════════════ PITÁGORAS — a escada na parede
# triângulo retângulo: chão 3 (P→B), parede ? (P→B... P→T), escada 5 (B→T). altura = 4.
_P, _Bp, _T = [0, 0], [3, 0], [0, 4]


def _tri_escada(**mais):
    base = {"pontos": {"P": _P, "B": _Bp, "T": _T},
            "poligonos": [{"vs": ["P", "B", "T"], "preenche": True}],
            "angulos": [{"em": "P", "de": "B", "para": "T", "reto": True}],
            "mostrar_pontos": False, "nomear_pontos": False}
    base.update(mais)
    return {"gerador": "figura", "spec": base}


PITAGORAS: dict = {
    "titulo": "Teorema de Pitágoras — a escada na parede",
    "topico": "pitagoras",
    "dados": {"chao": 3, "escada": 5, "altura": 4},
    "blocos": [
        {"diz": "Uma escada de cinco metros encostada na parede. O pé dela está a três "
                "metros da parede. A gente quer saber a que altura ela chega.",
         "figura": _tri_escada(
             segmentos=[{"de": "B", "para": "T", "rotulo": "5", "cor": "destaque", "lw": 5},
                        {"de": "P", "para": "B", "rotulo": "3", "cor": "azul"},
                        {"de": "P", "para": "T", "rotulo": "?", "cor": "verm"}],
             rotulos=[{"xy": [-1.3, 2], "texto": r"\text{parede}", "tam": 13},
                      {"xy": [1.5, -0.9], "texto": r"\text{chão}", "tam": 13}]),
         "espera": "media"},
        {"diz": "Repara: a parede e o chão fazem um ângulo reto. Isso é um triângulo "
                "retângulo. E a escada, que fica na frente do ângulo reto, é a hipotenusa "
                "— o lado maior.",
         "figura": _tri_escada(
             segmentos=[{"de": "B", "para": "T", "rotulo": "5", "cor": "destaque", "lw": 5},
                        {"de": "P", "para": "B", "rotulo": "3", "cor": "azul"},
                        {"de": "P", "para": "T", "rotulo": "?", "cor": "verm"}]),
         "espera": "media"},
        {"diz": "O teorema de Pitágoras diz: a hipotenusa ao quadrado é igual à soma dos "
                "outros dois lados ao quadrado. Cinco ao quadrado é três ao quadrado mais a "
                "altura ao quadrado.",
         "calc": {"gerador": "pitagoras", "params": {"a": 3, "c": 5}},
         "mostra_passos": True, "espera": "longa"},
        {"diz": "A altura é quatro metros. A escada toca a parede a quatro metros do chão.",
         "figura": _tri_escada(
             segmentos=[{"de": "B", "para": "T", "rotulo": "5", "cor": "destaque", "lw": 5},
                        {"de": "P", "para": "B", "rotulo": "3", "cor": "azul"},
                        {"de": "P", "para": "T", "rotulo": "4", "cor": "verde", "lw": 5}]),
         "espera": "media"},
    ],
    "ramos": {
        "por_que": [
            {"diz": "Olha o desenho clássico. Um quadrado em cada lado do triângulo. O do "
                    "chão tem área nove, o da parede tem dezesseis.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"P": _P, "B": _Bp, "T": _T,
                            "c1": [3, -3], "c2": [0, -3], "w1": [-4, 4], "w2": [-4, 0]},
                 "poligonos": [{"vs": ["P", "B", "c1", "c2"], "preenche": True, "cor": "azul", "alpha": 0.15},
                               {"vs": ["P", "T", "w1", "w2"], "preenche": True, "cor": "verm", "alpha": 0.15},
                               {"vs": ["P", "B", "T"], "preenche": True}],
                 "rotulos": [{"xy": [1.5, -1.5], "texto": "9", "tam": 20},
                             {"xy": [-2, 2], "texto": "16", "tam": 20}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "E o quadrado da hipotenusa, da escada, tem área vinte e cinco. Nove mais "
                    "dezesseis dá vinte e cinco. É sempre assim: os dois menores somados dão o maior.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"P": _P, "B": _Bp, "T": _T, "h1": [4, 7], "h2": [7, 3]},
                 "poligonos": [{"vs": ["B", "T", "h1", "h2"], "preenche": True, "cor": "destaque", "alpha": 0.18},
                               {"vs": ["P", "B", "T"], "preenche": True}],
                 "rotulos": [{"xy": [3.5, 3.5], "texto": "25", "tam": 20}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "longa"},
        ],
        "nao_entendi": [
            {"diz": "Devagar. Primeiro: onde está o ângulo reto? No canto, onde a parede "
                    "encontra o chão.",
             "figura": _tri_escada(),
             "espera": "media"},
            {"diz": "A hipotenusa é sempre o lado da frente do ângulo reto, e é sempre o maior. "
                    "Aqui é a escada: cinco metros.",
             "figura": _tri_escada(
                 segmentos=[{"de": "B", "para": "T", "rotulo": "5", "cor": "destaque", "lw": 5}]),
             "espera": "media"},
            {"diz": "Aí a conta: cinco ao quadrado, vinte e cinco. Menos três ao quadrado, "
                    "nove. Sobra dezesseis. Raiz de dezesseis: quatro.",
             "calc": {"gerador": "pitagoras", "params": {"a": 3, "c": 5}},
             "mostra_passos": True, "espera": "longa"},
        ],
        "achar_hipotenusa": [
            {"diz": "Se fosse o contrário — você sabe o chão e a altura, e quer a escada — é "
                    "a mesma fórmula. Três ao quadrado mais quatro ao quadrado.",
             "figura": _tri_escada(
                 segmentos=[{"de": "P", "para": "B", "rotulo": "3", "cor": "azul"},
                            {"de": "P", "para": "T", "rotulo": "4", "cor": "verde"},
                            {"de": "B", "para": "T", "rotulo": "?", "cor": "destaque", "lw": 5}]),
             "espera": "media"},
            {"diz": "Nove mais dezesseis, vinte e cinco. Raiz de vinte e cinco: cinco. A escada "
                    "tem cinco metros.",
             "calc": {"gerador": "pitagoras", "params": {"a": 3, "b": 4}},
             "mostra_passos": True, "espera": "longa"},
        ],
    },
}

_CATALOGO = {"trapezio": TRAPEZIO, "pitagoras": PITAGORAS}


def carregar(nome: str) -> Aula:
    return Aula.de_json(_CATALOGO[nome])


def disponiveis() -> list[str]:
    return list(_CATALOGO)
