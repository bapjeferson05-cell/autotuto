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
        # beat PERGUNTA — o aluno pensa antes de a fórmula aparecer (self-explanation)
        {"diz": "Antes de eu te dar a fórmula, me diz uma coisa: e se a base de cima fosse "
                "encolhendo, até virar zero? Que figura o trapézio viraria?",
         "figura": _trap(segmentos=[{"de": "D", "para": "C", "cor": "destaque", "lw": 5}]),
         "pergunta": {"escuta_s": 12, "senao": "e_triangulo",
                      "acerta": ["triangulo", "triângulo"],
                      "confirma": "Isso! Vira um triângulo. E guarda essa ideia — a fórmula "
                                  "do trapézio já contém a do triângulo."}},
        {"diz": "Então a fórmula é essa: soma das duas bases, vezes a altura, dividido "
                "por dois — porque a gente quer a MÉDIA das bases.",
         "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
         "mostra_passos": True,
         "diz_passos": ["Essa é a fórmula geral.",
                        "Troco pelos números do terreno: dezoito mais dez, vezes seis.",
                        "Dezoito mais dez é vinte e oito, vezes seis dá cento e sessenta e "
                        "oito. Divido por dois: oitenta e quatro."],
         "espera": "longa"},
        {"diz": "Oitenta e quatro metros quadrados — esse é o tamanho do terreno.",
         "espera": "media"},
    ],
    "ramos": {
        # "por que dividido por dois?"
        "por_que_div_2": [
            {"diz": "Pensa assim: se o terreno fosse um retângulo usando a base maior — "
                    "dezoito por seis — daria área demais.",
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
            {"diz": "Agora junta tudo — devagar.",
             "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
             "mostra_passos": True,
             "diz_passos": ["A fórmula.",
                            "Os números: dezoito mais dez, vezes seis.",
                            "Vinte e oito vezes seis é cento e sessenta e oito. Metade: oitenta e quatro."],
             "espera": "longa"},
        ],
        # "e se fosse um triângulo?"
        "e_triangulo": [
            {"diz": "É isso: a base de cima encolhe até zero, e o trapézio vira um triângulo.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _A, "B": _B, "T": [9, 6]},
                 "poligonos": [{"vs": ["A", "B", "T"], "preenche": True}],
                 "cotas": [{"de": "A", "para": "B", "texto": "18", "lado": -1}],
                 "mostrar_pontos": False, "nomear_pontos": False}},
             "espera": "media"},
            {"diz": "E olha por que a mesma fórmula serve: com a base menor igual a zero, "
                    "sobra base maior vezes altura, sobre dois. É a fórmula do triângulo.",
             "calc": {"gerador": "area_triangulo", "params": {"base": 18, "altura": 6}},
             "mostra_passos": True,
             "diz_passos": ["Base vezes altura, sobre dois.",
                            "Dezoito vezes seis é cento e oito. Metade: cinquenta e quatro."],
             "espera": "longa"},
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
        {"diz": "O teorema de Pitágoras: a hipotenusa ao quadrado é a soma dos outros dois "
                "lados ao quadrado. Como a gente quer a altura, isola ela.",
         "calc": {"gerador": "pitagoras", "params": {"a": 3, "c": 5}},
         "mostra_passos": True,
         "diz_passos": ["Altura ao quadrado é hipotenusa ao quadrado menos o chão ao quadrado.",
                        "Cinco ao quadrado é vinte e cinco; três ao quadrado é nove. Vinte e cinco menos nove: dezesseis.",
                        "A altura é a raiz de dezesseis: quatro."],
         "espera": "longa"},
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
            {"diz": "Aí é só a conta.",
             "calc": {"gerador": "pitagoras", "params": {"a": 3, "c": 5}},
             "mostra_passos": True,
             "diz_passos": ["A altura ao quadrado é o que sobra.",
                            "Vinte e cinco menos nove: dezesseis.",
                            "Raiz de dezesseis: quatro."],
             "espera": "longa"},
        ],
        "achar_hipotenusa": [
            {"diz": "Se fosse o contrário — você sabe o chão e a altura, e quer a escada — é "
                    "a mesma fórmula, só que agora você SOMA os dois lados.",
             "figura": _tri_escada(
                 segmentos=[{"de": "P", "para": "B", "rotulo": "3", "cor": "azul"},
                            {"de": "P", "para": "T", "rotulo": "4", "cor": "verde"},
                            {"de": "B", "para": "T", "rotulo": "?", "cor": "destaque", "lw": 5}]),
             "espera": "media"},
            {"diz": "Escada ao quadrado é três ao quadrado mais quatro ao quadrado.",
             "calc": {"gerador": "pitagoras", "params": {"a": 3, "b": 4}},
             "mostra_passos": True,
             "diz_passos": ["Some os catetos ao quadrado.",
                            "Nove mais dezesseis: vinte e cinco.",
                            "Raiz de vinte e cinco: cinco. A escada tem cinco metros."],
             "espera": "longa"},
        ],
    },
}

# ═══════════════════════════════════════════════════ EQUAÇÃO DO 1º GRAU — a balança
# "pensei num número, multipliquei por 3, somei 5, deu 20" → 3x + 5 = 20 → x = 5.
# âncora concreta: uma balança de dois pratos (concreteness fading → símbolo).
def _balanca(esq: str, dir: str, *, nivel=True):
    dy = 0.0 if nivel else 0.7
    return {"gerador": "figura", "spec": {
        "pontos": {"P": [0, 1.6], "F1": [-1.3, -1.1], "F2": [1.3, -1.1],
                   "L": [-6, 1.6 + dy], "R": [6, 1.6 - dy],
                   "PL": [-6, -0.9 + dy], "PR": [6, -0.9 - dy]},
        "poligonos": [{"vs": ["P", "F1", "F2"], "preenche": True, "cor": "fraco"}],
        "segmentos": [{"de": "L", "para": "R", "cor": "giz", "lw": 4},
                      {"de": "L", "para": "PL", "cor": "fraco", "lw": 1.5},
                      {"de": "R", "para": "PR", "cor": "fraco", "lw": 1.5}],
        "circulos": [{"centro": "PL", "r": 2.4, "cor": "azul", "centro_ponto": False},
                     {"centro": "PR", "r": 2.4, "cor": "destaque", "centro_ponto": False}],
        "rotulos": [{"xy": [-6, -1.0 + dy], "texto": esq, "cor": "azul", "tam": 16},
                    {"xy": [6, -1.0 - dy], "texto": dir, "cor": "destaque", "tam": 16}],
        "mostrar_pontos": False, "nomear_pontos": False}}


EQ_PRIMEIRO_GRAU: dict = {
    "titulo": "Equação do 1º grau — a balança",
    "topico": "eq_primeiro_grau",
    "dados": {"a": 3, "b": 5, "resultado": 20, "x": 5},
    "blocos": [
        {"diz": "Pensei num número. Multipliquei por três, somei cinco, e deu vinte. "
                "Qual é o número?",
         "figura": _balanca(r"3x + 5", r"20"),
         "espera": "media"},
        {"diz": "Chama o número de x. De um lado da balança: três x mais cinco. "
                "Do outro: vinte. Ela está em equilíbrio — os dois lados são iguais.",
         "figura": _balanca(r"3x + 5", r"20"),
         "espera": "media"},
        {"diz": "Antes de resolver: se eu tiro cinco do lado esquerdo, o que preciso "
                "fazer pra balança não desequilibrar?",
         "figura": _balanca(r"3x + 5", r"20"),
         "pergunta": {"escuta_s": 12, "senao": "por_que",
                      "acerta": ["dois lado", "dos dois", "outro lado", "os dois", "ambos",
                                 "mesma coisa", "tira dos dois", "tirar dos dois"],
                      "confirma": "Exato — tiro cinco dos DOIS lados. É a regra: o que "
                                  "faço de um lado, faço do outro."}},
        {"diz": "Então: tiro cinco dos dois lados, depois divido os dois lados por três.",
         "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 3, "b": -15}},
         "mostra_passos": True,
         "diz_passos": ["Três x mais cinco igual a vinte vira três x menos quinze igual a zero.",
                        "Passo o quinze pro outro lado: três x igual a quinze.",
                        "Divido por três: x igual a cinco."],
         "espera": "longa"},
        {"diz": "O número é cinco. Confere: cinco vezes três é quinze, mais cinco, vinte.",
         "figura": _balanca(r"3\cdot 5 + 5", r"20"),
         "espera": "media"},
    ],
    "ramos": {
        "por_que": [
            {"diz": "A balança só fica reta se os dois lados pesam igual. Se eu mexo só "
                    "num lado, ela pende. Por isso toda operação vai nos DOIS lados ao "
                    "mesmo tempo.",
             "figura": _balanca(r"3x + 5", r"20", nivel=False),
             "espera": "longa"},
            {"diz": "Tirando cinco dos dois: sobra três x de um lado, quinze do outro. "
                    "Ainda em equilíbrio.",
             "figura": _balanca(r"3x", r"15"),
             "espera": "media"},
        ],
        "nao_entendi": [
            {"diz": "Devagar. A igualdade é uma balança: três x mais cinco pesa o mesmo "
                    "que vinte.",
             "figura": _balanca(r"3x + 5", r"20"), "espera": "media"},
            {"diz": "Primeiro passo, só um: tiro cinco de cada lado. Fica três x igual a quinze.",
             "figura": _balanca(r"3x", r"15"), "espera": "media"},
            {"diz": "Segundo passo: três x é quinze, então x é quinze dividido por três. Cinco.",
             "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 3, "b": -15}},
             "mostra_passos": True, "espera": "longa"},
        ],
        "outro_numero": [
            {"diz": "Se em vez de vinte desse oito: três x mais cinco igual a oito. Tira "
                    "cinco: três x igual a três. Divide: x igual a um.",
             "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 3, "b": -3}},
             "mostra_passos": True, "espera": "longa"},
        ],
    },
}


# ═══════════════════════════════════════════════════ REGRA DE TRÊS — a proporção
# "3 cadernos custam 24 reais. Quanto custam 5?" → 3/24 = 5/x → x = 40.
def _tabela_prop(v22: str):
    return {"gerador": "figura", "spec": {
        "pontos": {"A": [0, 0], "B": [6, 0], "C": [0, 3], "D": [6, 3],
                   "M": [3, 0], "N": [3, 3], "P": [0, 1.5], "Q": [6, 1.5]},
        "segmentos": [{"de": "A", "para": "B"}, {"de": "C", "para": "D"},
                      {"de": "A", "para": "C"}, {"de": "B", "para": "D"},
                      {"de": "M", "para": "N", "cor": "fraco"}, {"de": "P", "para": "Q", "cor": "fraco"}],
        "rotulos": [{"xy": [1.5, 3.5], "texto": r"\text{cadernos}", "tam": 13},
                    {"xy": [4.5, 3.5], "texto": r"\text{reais}", "tam": 13},
                    {"xy": [1.5, 2.2], "texto": "3", "tam": 18},
                    {"xy": [4.5, 2.2], "texto": "24", "tam": 18},
                    {"xy": [1.5, 0.7], "texto": "5", "tam": 18},
                    {"xy": [4.5, 0.7], "texto": v22, "cor": "destaque", "tam": 18}],
        "mostrar_pontos": False, "nomear_pontos": False}}


REGRA_DE_TRES: dict = {
    "titulo": "Regra de três — a proporção",
    "topico": "regra_de_tres",
    "dados": {"a": 3, "b": 24, "c": 5, "x": 40},
    "blocos": [
        {"diz": "Três cadernos iguais custam vinte e quatro reais. Quanto custam cinco?",
         "figura": _tabela_prop("?"),
         "espera": "media"},
        {"diz": "Monto uma tabela: cadernos de um lado, reais do outro. Três pra vinte "
                "e quatro, cinco pra o que eu quero achar.",
         "figura": _tabela_prop("?"),
         "espera": "media"},
        {"diz": "Antes da conta: se cinco cadernos é mais que três, o preço vai ser "
                "maior ou menor que vinte e quatro?",
         "figura": _tabela_prop("?"),
         "pergunta": {"escuta_s": 12, "senao": "por_que",
                      "acerta": ["maior", "mais caro", "aumenta", "cresce", "sobe", "fica caro"],
                      "confirma": "Isso — mais cadernos, mais caro. É proporção direta: "
                                  "as duas coisas crescem juntas."}},
        {"diz": "Como as duas colunas crescem juntas, eu multiplico em cruz e divido.",
         "calc": {"gerador": "regra_de_tres", "params": {"a": 3, "b": 24, "c": 5}},
         "mostra_passos": True,
         "diz_passos": ["Três está para vinte e quatro assim como cinco está para x.",
                        "Multiplico cruzado: x igual a vinte e quatro vezes cinco, sobre três.",
                        "Cento e vinte sobre três: quarenta reais."],
         "espera": "longa"},
        {"diz": "Quarenta reais. Cada caderno custa oito, e cinco vezes oito é quarenta.",
         "figura": _tabela_prop("40"),
         "espera": "media"},
    ],
    "ramos": {
        "por_que": [
            {"diz": "Os cadernos são todos iguais, então o preço por caderno é fixo. "
                    "Vinte e quatro dividido por três dá oito reais cada.",
             "figura": _tabela_prop("?"), "espera": "media"},
            {"diz": "Aí cinco cadernos é só cinco vezes oito. Quarenta. A regra de três "
                    "faz essa mesma conta de uma vez.",
             "figura": _tabela_prop("40"), "espera": "longa"},
        ],
        "nao_entendi": [
            {"diz": "Vou pelo caminho simples. Um caderno primeiro: vinte e quatro "
                    "dividido por três, oito reais.",
             "espera": "media"},
            {"diz": "Agora cinco cadernos: oito vezes cinco. Quarenta reais.",
             "espera": "longa"},
        ],
        "e_se_menos": [
            {"diz": "Se fosse o contrário — vinte e quatro reais dão pra quantos "
                    "cadernos, se cada um é oito? Vinte e quatro sobre oito: três. "
                    "A proporção funciona nos dois sentidos.",
             "espera": "longa"},
        ],
    },
}

_CATALOGO = {"trapezio": TRAPEZIO, "pitagoras": PITAGORAS,
             "eq_primeiro_grau": EQ_PRIMEIRO_GRAU, "regra_de_tres": REGRA_DE_TRES}


def carregar(nome: str) -> Aula:
    return Aula.de_json(_CATALOGO[nome])


def disponiveis() -> list[str]:
    return list(_CATALOGO)
