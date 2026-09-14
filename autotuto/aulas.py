"""aulas.py — as 5 aulas de ouro, escritas à mão.

Não são geradas por LLM. São a referência: a pedagogia que a gente QUER, no
schema do projeto. Servem pra três coisas:
  1. o MVP da Maratona (o Ciclo do Trapézio roda daqui);
  2. few-shot no prompt do planejador (o LLM copia o padrão);
  3. teste de fogo do renderizador — se `figura(spec)` desenha isso, desenha o resto.

    from autotuto.aulas import carregar
    aula = carregar("trapezio")

Convenções destes dicts:
  - beat de desenho: `"figura": {"gerador": "figura", "spec": {<spec inline>}}`
    (spec = pontos/segmentos/poligonos/angulos/marcas/rotulos — o que
    `figuras.canvas.figura` consome). NÃO usa geradores nomeados.
  - beat de conta: `"calc": {"gerador": "<nome em calc.CATALOGO>", "params": {...}}`.
  - `diz` narra a DECISÃO ("divide por dois porque é a média"), nunca o passo
    cru, nunca LaTeX.

Dependência: só `autotuto.schema`. Nomes de gerador/calc entram como string.
"""
from __future__ import annotations

import copy

from autotuto.schema import Aula

# ───────────────────────────────────────────────────────── ramos genéricos
# Todo `carregar()` mergeia isto na aula (a aula sobrescreve por chave). É a
# garantia da SPEC §7: o fallback honesto sempre tem pra onde ir.
RAMOS_GENERICOS: dict = {
    "por_que": [
        {"diz": "Boa pergunta. A ideia por trás disso é simples: cada passo aqui "
                "só existe pra deixar a conta mais fácil, sem mudar o valor. "
                "Se algum passo te incomodou, me diz qual que eu abro ele."},
    ],
    "nao_entendi": [
        {"diz": "Sem problema, a culpa é da explicação. Vou de novo, mais devagar "
                "e por partes menores — pode me parar em qualquer ponto."},
    ],
    "repete": [
        {"diz": "Claro, deixa eu repetir. Presta atenção só na última parte, "
                "que é onde costuma escapar."},
    ],
}


def _com_genericos(aula: dict) -> dict:
    """Devolve a aula com os ramos genéricos mergeados (a aula vence por chave)."""
    return {**aula, "ramos": {**RAMOS_GENERICOS, **aula.get("ramos", {})}}


# ═══════════════════════════════════════════════ TRAPÉZIO — o terreno (o MVP)
# trapézio isósceles: base maior 18 embaixo, base menor 10 em cima, altura 6.
_TA, _TB, _TC, _TD = [0, 0], [18, 0], [14, 6], [4, 6]

_TRAP_SPEC = {
    "pontos": {"A": _TA, "B": _TB, "C": _TC, "D": _TD, "H": [4, 0]},
    "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
    # linha de altura tracejada (D->base), pra o "6" cotar a ALTURA e não o lado oblíquo
    "segmentos": [{"de": "D", "para": "H", "tracejado": True}],
    "angulos": [{"vertice": "H", "de": "A", "para": "D"}],
    "marcas": [{"tipo": "par", "de": "A", "para": "B"},
               {"tipo": "par", "de": "D", "para": "C"}],
    "rotulos": [{"xy": [9, -1.2], "texto": "18"},
                {"xy": [9, 6.9], "texto": "10"},
                {"xy": [3.3, 3], "texto": "6"}],
}

TRAPEZIO: dict = {
    "titulo": "Área do trapézio — o terreno",
    "topico": "area_trapezio",
    "dados": {"B": 18, "b": 10, "h": 6, "area": 84},
    "blocos": [
        {"diz": "Olha esse terreno. Quatro lados, e o de baixo corre paralelo ao de "
                "cima. Sempre que dois lados são paralelos assim, a figura é um trapézio.",
         "figura": {"gerador": "figura", "spec": _TRAP_SPEC},
         "espera": "media"},
        {"diz": "As duas bases são esses lados paralelos: a de baixo tem dezoito "
                "metros, a de cima tem dez. E a distância entre elas, medida em linha "
                "reta, é a altura: seis metros.",
         "figura": {"gerador": "figura", "spec": {
             "pontos": {"A": _TA, "B": _TB, "C": _TC, "D": _TD,
                        "P": [9, 0], "Q": [9, 6]},
             "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
             "segmentos": [["P", "Q"]],
             "angulos": [{"vertice": "P", "de": "B", "para": "Q"}],
             "rotulos": [{"xy": [9, -1.2], "texto": "18"},
                         {"xy": [9, 6.9], "texto": "10"},
                         {"xy": [10.2, 3], "texto": "6"}]}},
         "espera": "media"},
        # beat PERGUNTA — o aluno pensa antes de a fórmula aparecer (self-explanation)
        {"diz": "Antes de eu te dar a fórmula, pensa comigo: e se a base de cima "
                "fosse encolhendo, até virar zero? Que figura o trapézio viraria?",
         "figura": {"gerador": "figura", "spec": _TRAP_SPEC},
         "pergunta": {"escuta_s": 12, "senao": "e_triangulo",
                      "acerta": ["triangulo", "triângulo"],
                      "confirma": "Isso, vira um triângulo. Guarda essa ideia: a "
                                  "fórmula do trapézio já traz a do triângulo dentro."}},
        {"diz": "A fórmula soma as duas bases, multiplica pela altura e divide por "
                "dois. Esse dividir por dois é o coração: a gente quer a MÉDIA das "
                "bases, não a soma delas.",
         "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
         "mostra_passos": True,
         "diz_passos": ["Essa é a fórmula geral, valendo pra qualquer trapézio.",
                        "Agora entram os números do terreno: dezoito e dez nas bases, "
                        "seis na altura.",
                        "Vinte e oito vezes seis dá cento e sessenta e oito, e a "
                        "metade disso é oitenta e quatro."],
         "espera": "longa"},
        {"diz": "Oitenta e quatro metros quadrados. Esse é o tamanho do terreno.",
         "espera": "media"},
    ],
    "ramos": {
        # "por que divide por dois?" — os dois retângulos
        "por_que_div_2": [
            {"diz": "Divide por dois porque a gente troca o trapézio por um retângulo "
                    "de mesma área. Um retângulo na base maior, dezoito por seis, "
                    "seria área demais; na base menor, dez por seis, seria de menos.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": [0, 0], "B": [18, 0], "C": [18, 6], "D": [0, 6],
                            "E": [24, 0], "F": [34, 0], "G": [34, 6], "H": [24, 6]},
                 "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True},
                               {"vs": ["E", "F", "G", "H"], "preenche": True}],
                 "rotulos": [{"xy": [9, 3], "texto": "18 x 6"},
                             {"xy": [9, -1.2], "texto": "demais"},
                             {"xy": [29, 3], "texto": "10 x 6"},
                             {"xy": [29, -1.2], "texto": "de menos"}]}},
             "espera": "media"},
            {"diz": "A média fica no meio: dezoito mais dez dá vinte e oito, dividido "
                    "por dois dá quatorze. Um retângulo de quatorze por seis tem "
                    "exatamente a área do trapézio.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": _TA, "B": _TB, "C": _TC, "D": _TD,
                            "G": [2, 0], "H": [16, 0], "I": [16, 6], "J": [2, 6]},
                 "poligonos": [{"vs": ["G", "H", "I", "J"], "preenche": True},
                               {"vs": ["A", "B", "C", "D"], "preenche": False}],
                 "rotulos": [{"xy": [9, -1.2], "texto": "14"},
                             {"xy": [9, 3], "texto": "14 x 6"}]}},
             "espera": "longa"},
        ],
        # "e se fosse um triângulo?"
        "e_triangulo": [
            {"diz": "É isso: a base de cima encolhe até zero e o trapézio vira um "
                    "triângulo, com a mesma base de dezoito e a mesma altura de seis.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"A": [0, 0], "B": [18, 0], "T": [9, 6]},
                 "poligonos": [{"vs": ["A", "B", "T"], "preenche": True}],
                 "rotulos": [{"xy": [9, -1.2], "texto": "18"},
                             {"xy": [3.5, 3], "texto": "6"}]}},
             "espera": "media"},
            {"diz": "E a fórmula do trapézio continua certa: com a base menor igual a "
                    "zero, sobra só base maior vezes altura dividido por dois. Que é, "
                    "letra por letra, a fórmula do triângulo.",
             "calc": {"gerador": "area_triangulo", "params": {"base": 18, "altura": 6}},
             "mostra_passos": True,
             "diz_passos": ["Base vezes altura, sobre dois.",
                            "Dezoito vezes seis dá cento e oito, e a metade é cinquenta "
                            "e quatro."],
             "espera": "longa"},
        ],
    },
}

# ═══════════════════════════════════════════════ PITÁGORAS — a escada na parede
# triângulo retângulo: canto P na quina parede/chão, B é o pé da escada (chão 3),
# T é onde a escada toca a parede (altura 4). Hipotenusa B→T = escada = 5.
_PP, _PB, _PT = [0, 0], [3, 0], [0, 4]

_ESCADA_SPEC = {
    "pontos": {"P": _PP, "B": _PB, "T": _PT},
    "poligonos": [{"vs": ["P", "B", "T"], "preenche": True}],
    "angulos": [{"vertice": "P", "de": "B", "para": "T"}],
    "rotulos": [{"xy": [1.5, -0.5], "texto": "3"},
                {"xy": [-0.6, 2], "texto": "?"},
                {"xy": [2.1, 2.4], "texto": "5"}],
}

PITAGORAS: dict = {
    "titulo": "Teorema de Pitágoras — a escada na parede",
    "topico": "pitagoras",
    "dados": {"chao": 3, "escada": 5, "altura": 4},
    "blocos": [
        {"diz": "Uma escada de cinco metros encostada na parede. O pé dela está a "
                "três metros da parede. A pergunta é a que altura ela chega.",
         "figura": {"gerador": "figura", "spec": _ESCADA_SPEC},
         "espera": "media"},
        {"diz": "A parede e o chão se encontram num ângulo reto, então esse é um "
                "triângulo retângulo. A escada fica de frente pro ângulo reto: ela é "
                "a hipotenusa, o lado mais comprido dos três.",
         "figura": {"gerador": "figura", "spec": _ESCADA_SPEC},
         "espera": "media"},
        {"diz": "O teorema de Pitágoras diz que a hipotenusa ao quadrado é a soma "
                "dos quadrados dos outros dois lados. Como o que falta é a altura, "
                "a gente vira a conta pra isolar ela.",
         "calc": {"gerador": "pitagoras", "params": {"a": 3, "c": 5}},
         "mostra_passos": True,
         "diz_passos": ["A altura ao quadrado é o quadrado da escada menos o quadrado "
                        "do chão.",
                        "Vinte e cinco menos nove dá dezesseis.",
                        "A altura é a raiz de dezesseis, que é quatro."],
         "espera": "longa"},
        {"diz": "Quatro metros. A escada toca a parede a quatro metros do chão.",
         "figura": {"gerador": "figura", "spec": {
             "pontos": {"P": _PP, "B": _PB, "T": _PT},
             "poligonos": [{"vs": ["P", "B", "T"], "preenche": True}],
             "angulos": [{"vertice": "P", "de": "B", "para": "T"}],
             "rotulos": [{"xy": [1.5, -0.5], "texto": "3"},
                         {"xy": [-0.6, 2], "texto": "4"},
                         {"xy": [2.1, 2.4], "texto": "5"}]}},
         "espera": "media"},
    ],
    "ramos": {
        # override do genérico: por que a2 + b2 = c2
        "por_que": [
            {"diz": "Desenha um quadrado sobre cada lado. O quadrado do chão tem área "
                    "nove, o da parede tem área dezesseis.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"P": _PP, "B": _PB, "T": _PT,
                            "c1": [3, -3], "c2": [0, -3],
                            "w1": [-4, 0], "w2": [-4, 4]},
                 "poligonos": [{"vs": ["P", "B", "c1", "c2"], "preenche": True},
                               {"vs": ["P", "T", "w2", "w1"], "preenche": True},
                               {"vs": ["P", "B", "T"], "preenche": True}],
                 "rotulos": [{"xy": [1.5, -1.5], "texto": "9"},
                             {"xy": [-2, 2], "texto": "16"}]}},
             "espera": "media"},
            {"diz": "O quadrado sobre a escada tem área vinte e cinco. E nove mais "
                    "dezesseis dá vinte e cinco. Isso não é coincidência: nesse "
                    "triângulo os dois quadrados menores sempre enchem o maior.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"P": _PP, "B": _PB, "T": _PT,
                            "h1": [7, 3], "h2": [4, 7]},
                 "poligonos": [{"vs": ["B", "T", "h2", "h1"], "preenche": True},
                               {"vs": ["P", "B", "T"], "preenche": True}],
                 "rotulos": [{"xy": [3.7, 3.3], "texto": "25"}]}},
             "espera": "longa"},
        ],
        # "e pra achar a escada (a hipotenusa)?"
        "achar_hipotenusa": [
            {"diz": "Se o que falta fosse a escada, e você já tivesse o chão e a "
                    "altura, é o mesmo teorema — só que agora você SOMA os dois "
                    "quadrados em vez de subtrair.",
             "figura": {"gerador": "figura", "spec": {
                 "pontos": {"P": _PP, "B": _PB, "T": _PT},
                 "poligonos": [{"vs": ["P", "B", "T"], "preenche": True}],
                 "angulos": [{"vertice": "P", "de": "B", "para": "T"}],
                 "rotulos": [{"xy": [1.5, -0.5], "texto": "3"},
                             {"xy": [-0.6, 2], "texto": "4"},
                             {"xy": [2.1, 2.4], "texto": "?"}]}},
             "espera": "media"},
            {"diz": "Some os quadrados dos catetos e tire a raiz.",
             "calc": {"gerador": "pitagoras", "params": {"a": 3, "b": 4}},
             "mostra_passos": True,
             "diz_passos": ["A escada ao quadrado é nove mais dezesseis.",
                            "Isso dá vinte e cinco.",
                            "A raiz de vinte e cinco é cinco: a escada tem cinco metros."],
             "espera": "longa"},
        ],
    },
}

# ═══════════════════════════════════════════════ EQUAÇÃO DO 1º GRAU — a balança
# "pensei num número, multipliquei por 3, somei 5, deu 20" → 3x + 5 = 20.
# resolvido como 3x - 15 = 0 → x = 5. Âncora concreta: balança de dois pratos.
def _balanca(esq: str, dir_: str) -> dict:
    return {"gerador": "figura", "spec": {
        "pontos": {"P": [0, 0], "T": [0, 2],
                   "L": [-4, 2], "R": [4, 2],
                   "LP": [-4, 0.6], "RP": [4, 0.6],
                   "F1": [-1.3, -1.2], "F2": [1.3, -1.2]},
        "segmentos": [["P", "T"], ["L", "R"],
                      ["L", "LP"], ["R", "RP"], ["P", "F1"], ["P", "F2"]],
        "poligonos": [{"vs": ["LP", [-5.1, 0.1], [-2.9, 0.1]], "preenche": True},
                      {"vs": ["RP", [5.1, 0.1], [2.9, 0.1]], "preenche": True}],
        "rotulos": [{"xy": [-4, -0.6], "texto": esq},
                    {"xy": [4, -0.6], "texto": dir_},
                    {"xy": [0, 2.6], "texto": "="}],
    }}


EQ_PRIMEIRO_GRAU: dict = {
    "titulo": "Equação do 1º grau — a balança",
    "topico": "eq_primeiro_grau",
    "dados": {"a": 3, "b": 5, "resultado": 20, "x": 5},
    "blocos": [
        {"diz": "Pensei num número, multipliquei por três, somei cinco, e deu vinte. "
                "Qual era o número?",
         "figura": _balanca("3x + 5", "20"),
         "espera": "media"},
        {"diz": "Chama o número de x. De um lado da balança fica três x mais cinco, "
                "do outro fica vinte. A balança está equilibrada porque os dois "
                "lados valem a mesma coisa: é isso que o sinal de igual quer dizer.",
         "figura": _balanca("3x + 5", "20"),
         "espera": "media"},
        # beat PERGUNTA — self-explanation antes de resolver
        {"diz": "Pra achar o x eu quero tirar esse mais cinco da esquerda. Se eu "
                "tiro cinco só de um lado, o que eu preciso fazer pra balança não "
                "desequilibrar?",
         "figura": _balanca("3x + 5", "20"),
         "pergunta": {"escuta_s": 12, "senao": "por_que",
                      "acerta": ["dois lados", "nos dois", "dos dois", "os dois",
                                 "ambos", "outro lado", "mesma coisa", "tira dos dois",
                                 "tirar dos dois"],
                      "confirma": "Exato: tiro cinco dos DOIS lados ao mesmo tempo. "
                                  "O que eu faço de um lado, faço do outro."}},
        {"diz": "Então tiro cinco dos dois lados e depois divido os dois lados por "
                "três. Cada operação mantém a igualdade porque atinge os dois lados "
                "igual.",
         "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 3, "b": -15}},
         "mostra_passos": True,
         "diz_passos": ["Tirando cinco dos dois lados, três x mais cinco igual a "
                        "vinte vira três x menos quinze igual a zero.",
                        "Isso é o mesmo que três x igual a quinze.",
                        "Dividindo os dois lados por três, x é igual a cinco."],
         "espera": "longa"},
        {"diz": "O número era cinco. Confere: cinco vezes três é quinze, mais cinco "
                "dá vinte.",
         "figura": _balanca("3 . 5 + 5", "20"),
         "espera": "media"},
    ],
    "ramos": {
        # override do genérico: por que mexer nos dois lados
        "por_que": [
            {"diz": "A balança só fica reta enquanto os dois pratos pesam igual. "
                    "Se eu mexo em um prato só, ela pende, e a igualdade quebra. "
                    "Por isso toda operação vai nos dois lados junto.",
             "figura": _balanca("3x + 5", "20"),
             "espera": "media"},
            {"diz": "Tirando cinco de cada lado sobra três x de um lado e quinze do "
                    "outro. Ainda equilibrado, e agora bem mais fácil de resolver.",
             "figura": _balanca("3x", "15"),
             "espera": "longa"},
        ],
        # "e se o resultado fosse outro número?"
        "outro_numero": [
            {"diz": "Se em vez de vinte tivesse dado oito, muda só o número da "
                    "direita: três x mais cinco igual a oito. Tira cinco dos dois "
                    "lados, sobra três x igual a três, e dividindo por três o x é um. "
                    "O caminho é sempre o mesmo.",
             "calc": {"gerador": "eq_primeiro_grau", "params": {"a": 3, "b": -3}},
             "mostra_passos": True,
             "diz_passos": ["Tirando cinco dos dois lados, sobra três x menos três "
                            "igual a zero.",
                            "Isso é três x igual a três.",
                            "Dividindo por três, x é igual a um."],
             "espera": "longa"},
        ],
    },
}

# ═══════════════════════════════════════════════ REGRA DE TRÊS — a proporção
# "3 cadernos custam 24 reais. Quanto custam 5?" → 24 * 5 / 3 = 40.
def _tabela(v_x: str) -> dict:
    return {"gerador": "figura", "spec": {
        "pontos": {"A": [0, 0], "B": [6, 0], "C": [0, 3], "D": [6, 3],
                   "M": [3, 0], "N": [3, 3], "P": [0, 1.5], "Q": [6, 1.5]},
        "segmentos": [["A", "B"], ["C", "D"], ["A", "C"], ["B", "D"],
                      ["M", "N"], ["P", "Q"]],
        "rotulos": [{"xy": [1.5, 3.4], "texto": "cadernos"},
                    {"xy": [4.5, 3.4], "texto": "reais"},
                    {"xy": [1.5, 2.25], "texto": "3"},
                    {"xy": [4.5, 2.25], "texto": "24"},
                    {"xy": [1.5, 0.75], "texto": "5"},
                    {"xy": [4.5, 0.75], "texto": v_x}],
    }}


REGRA_DE_TRES: dict = {
    "titulo": "Regra de três — a proporção",
    "topico": "regra_de_tres",
    "dados": {"a": 3, "b": 24, "c": 5, "x": 40},
    "blocos": [
        {"diz": "Três cadernos iguais custam vinte e quatro reais. Quanto custam cinco?",
         "figura": _tabela("?"),
         "espera": "media"},
        {"diz": "Monto uma tabela com duas colunas: cadernos de um lado, reais do "
                "outro. Três linha com vinte e quatro, cinco linha com o preço que "
                "eu quero achar.",
         "figura": _tabela("?"),
         "espera": "media"},
        # beat PERGUNTA — antecipa o sentido da proporção
        {"diz": "Antes da conta, um palpite: como cinco cadernos é mais que três, o "
                "preço vai dar maior ou menor que vinte e quatro?",
         "figura": _tabela("?"),
         "pergunta": {"escuta_s": 12, "senao": "por_que",
                      "acerta": ["maior", "mais caro", "aumenta", "cresce", "sobe",
                                 "mais", "fica caro"],
                      "confirma": "Isso: mais cadernos, mais caro. As duas colunas "
                                  "crescem juntas — é proporção direta."}},
        {"diz": "Como as duas colunas crescem juntas, eu multiplico em cruz e divido: "
                "vinte e quatro vezes cinco, sobre três.",
         "calc": {"gerador": "regra_de_tres", "params": {"a": 3, "b": 24, "c": 5}},
         "mostra_passos": True,
         "diz_passos": ["Três está pra vinte e quatro assim como cinco está pro preço "
                        "que eu quero.",
                        "Multiplicando cruzado, é vinte e quatro vezes cinco dividido "
                        "por três: cento e vinte sobre três dá quarenta reais."],
         "espera": "longa"},
        {"diz": "Quarenta reais. Dá pra conferir pelo preço de um caderno: vinte e "
                "quatro sobre três é oito, e cinco vezes oito é quarenta.",
         "figura": _tabela("40"),
         "espera": "media"},
    ],
    "ramos": {
        # override do genérico: por que a proporção funciona
        "por_que": [
            {"diz": "Os cadernos são todos iguais, então o preço de cada um é fixo. "
                    "Vinte e quatro dividido por três dá oito reais por caderno.",
             "figura": _tabela("?"),
             "espera": "media"},
            {"diz": "Sabendo que cada um custa oito, cinco cadernos é só cinco vezes "
                    "oito, quarenta. A regra de três faz esse mesmo raciocínio de "
                    "uma vez só, sem precisar achar o preço de um.",
             "figura": _tabela("40"),
             "espera": "longa"},
        ],
        # "e se fosse menos cadernos / o caminho inverso?"
        "e_se_menos": [
            {"diz": "Funciona nos dois sentidos. Se a pergunta fosse quantos cadernos "
                    "dá pra comprar com vinte e quatro reais, sendo cada um oito, é "
                    "vinte e quatro dividido por oito: três cadernos.",
             "espera": "longa"},
        ],
    },
}

# ═══════════════════════════════════════════════ FRAÇÃO — a pizza e os brigadeiros
# A aula que o círculo destravou. Fração é o assunto onde o desenho não é enfeite:
# "três quartos" só vira ideia quando o aluno VÊ três pedaços de quatro pintados.
# Duas representações de propósito (dual coding): a pizza (parte de UMA coisa) e
# os doze brigadeiros (parte de uma QUANTIDADE) — é a ponte entre as duas que
# costuma faltar, e é onde o aluno trava na hora de calcular 3/4 de 12.

def _pizza(num, den, centro=(0.0, 0.0), raio=3.0):
    """Spec inline de uma pizza `num`/`den`: `den` fatias iguais, `num` pintadas."""
    passo = 360.0 / den
    return [{"centro": list(centro), "raio": raio,
             "setor": [90 + i * passo, 90 + (i + 1) * passo],
             "pintado": i < num}
            for i in range(den)]


def _brigadeiros(levados=9, total=12, por_grupo=3):
    """Os 12 brigadeiros em 4 grupos de 3 — os `levados` primeiros pintados."""
    circulos, rotulos = [], []
    for n in range(total):
        g, i = divmod(n, por_grupo)
        x = g * 4.0 + i * 1.1
        circulos.append({"centro": [x, 0.0], "raio": 0.45, "pintado": n < levados})
    for g in range(total // por_grupo):
        meio = g * 4.0 + (por_grupo - 1) * 1.1 / 2
        rotulos.append({"xy": [meio, -1.3],
                        "texto": "levou" if g * por_grupo < levados else "ficou"})
    return circulos, rotulos


_BRIG_CIRC, _BRIG_ROT = _brigadeiros()
_BRIG_VAZIO, _ = _brigadeiros(levados=0)

FRACAO: dict = {
    "titulo": "Fração — a pizza e os doze brigadeiros",
    "topico": "fracao_de",
    "dados": {"num": 3, "den": 4, "todo": 12, "resultado": 9},
    "blocos": [
        {"diz": "Olha essa pizza. Alguém cortou ela em quatro pedaços, e repara numa "
                "coisa: os quatro pedaços são do mesmo tamanho. Esse detalhe é o que "
                "quase todo mundo pula, e sem ele fração nenhuma funciona.",
         "figura": {"gerador": "figura", "spec": {
             "circulos": _pizza(0, 4),
             "rotulos": [{"xy": [0, -4.2], "texto": "4 pedacos iguais"}]}},
         "espera": "media"},
        {"diz": "Agora imagina que você comeu três desses quatro pedaços. Foi isso "
                "que você comeu: tres quartos da pizza. O número de baixo conta em "
                "quantos pedaços a pizza foi cortada; o de cima conta quantos você "
                "pegou.",
         "figura": {"gerador": "figura", "spec": {
             "circulos": _pizza(3, 4),
             "rotulos": [{"xy": [0, -4.2], "texto": "3/4"}]}},
         "espera": "media"},
        # beat PERGUNTA — o aluno decide o caminho antes de ver a conta
        {"diz": "Peraí, antes de eu continuar. Agora não é mais pizza: é uma caixa "
                "com doze brigadeiros, e você vai levar três quartos dela. Pensa "
                "comigo: pra começar, você olha primeiro pro três ou pro quatro?",
         "figura": {"gerador": "figura", "spec": {
             "circulos": _BRIG_VAZIO,
             "rotulos": [{"xy": [7.1, -2.6], "texto": "12 brigadeiros"}]}},
         "pergunta": {"escuta_s": 12, "senao": "comeca_pelo_de_baixo",
                      "acerta": ["quatro", "4", "de baixo", "dividir", "dividindo",
                                 "denominador"],
                      "confirma": "Isso. Começa pelo de baixo: ele é quem parte a "
                                  "caixa em grupos iguais. Só depois o de cima diz "
                                  "quantos grupos você leva."}},
        {"diz": "O quatro parte os doze em quatro grupos iguais, e cada grupo fica "
                "com três brigadeiros. Aí o três manda levar três desses grupos. "
                "Três grupos de três: nove brigadeiros.",
         "figura": {"gerador": "figura", "spec": {
             "circulos": _BRIG_CIRC, "rotulos": _BRIG_ROT}},
         "calc": {"gerador": "fracao_de", "params": {"num": 3, "den": 4, "todo": 12}},
         "mostra_passos": True,
         "diz_passos": ["Três quartos de doze — é isso que a gente quer.",
                        "Três vezes doze dá trinta e seis, dividido por quatro dá nove."],
         "espera": "longa"},
        {"diz": "Nove brigadeiros. E repara que é a mesma pizza de antes: três "
                "pedaços de quatro, só que agora cada pedaço vale três brigadeiros "
                "em vez de uma fatia.",
         "espera": "media"},
    ],
    "ramos": {
        # sobrescreve o genérico: aqui o "por que" tem resposta própria
        "por_que": [
            {"diz": "Porque o de baixo é o tamanho do pedaço e o de cima é quantos "
                    "pedaços. Se você só multiplicasse por três, ia levar trinta e "
                    "seis brigadeiros — três caixas, não três quartos de uma.",
             "espera": "media"},
        ],
        "comeca_pelo_de_baixo": [
            {"diz": "Começa pelo de baixo, o quatro. Ele é quem corta: doze "
                    "brigadeiros em quatro grupos iguais dá três em cada grupo. "
                    "Esse é o tamanho do pedaço.",
             "figura": {"gerador": "figura", "spec": {
                 "circulos": _BRIG_VAZIO,
                 "rotulos": [{"xy": [1.1, -1.3], "texto": "3"},
                             {"xy": [5.1, -1.3], "texto": "3"},
                             {"xy": [9.1, -1.3], "texto": "3"},
                             {"xy": [13.1, -1.3], "texto": "3"},
                             {"xy": [7.1, -2.6], "texto": "4 grupos de 3"}]}},
             "espera": "media"},
            {"diz": "Só depois entra o de cima: leva três dos quatro grupos. "
                    "Nove brigadeiros.",
             "figura": {"gerador": "figura", "spec": {
                 "circulos": _BRIG_CIRC, "rotulos": _BRIG_ROT}},
             "espera": "longa"},
        ],
        # "e se o corte fosse outro?" — equivalência, o pulo do gato da fração
        "e_se_outro_corte": [
            {"diz": "Boa, olha as duas juntas. À esquerda a pizza cortada em quatro "
                    "com três pedaços comidos; à direita a mesma pizza cortada em "
                    "oito, com seis comidos. É exatamente a mesma pizza faltando.",
             "figura": {"gerador": "figura", "spec": {
                 "circulos": _pizza(3, 4, centro=(-3.6, 0), raio=3.0)
                             + _pizza(6, 8, centro=(3.6, 0), raio=3.0),
                 "rotulos": [{"xy": [-3.6, -4.2], "texto": "3/4"},
                             {"xy": [3.6, -4.2], "texto": "6/8"},
                             {"xy": [0, 0], "texto": "="}]}},
             "espera": "media"},
            {"diz": "Cortar em mais pedaços não muda quanto você comeu: muda só o "
                    "tamanho de cada pedaço. Por isso três quartos e seis oitavos "
                    "são a mesma fração escrita de dois jeitos.",
             "espera": "longa"},
        ],
        # "e se fosse a metade?" — o caso mais fácil, âncora pra quem travou
        "e_se_metade": [
            {"diz": "Metade é a fração mais fácil: um de dois. Corta em dois pedaços "
                    "iguais e leva um. Dos doze brigadeiros, metade é seis.",
             "figura": {"gerador": "figura", "spec": {
                 "circulos": _pizza(1, 2),
                 "rotulos": [{"xy": [0, -4.2], "texto": "1/2"}]}},
             "espera": "media"},
        ],
    },
}


# ═══════════════════════════════════ EXEMPLO DE ESTRUTURA (few-shot de emergência)
# NÃO é uma aula de ouro e NÃO entra em `_CATALOGO` — `disponiveis()` não muda.
# Existe por um motivo só: quando o problema do aluno não casa com nenhuma pista
# de tópico, o planejador mandava o prompt pro modelo SEM NENHUM exemplo de JSON.
# Medido: de 11 tópicos de uma bateria real, 7 caíam nesse caminho — e era
# justamente neles que o plano voltava quebrado e a aula virava fallback.
# Um modelo de 7B não acerta um schema aninhado só pela descrição em prosa.
#
# Propositalmente o assunto mais simples possível, e usando só gerador que
# existe de verdade: exemplo que inventa ferramenta ensina o modelo a inventar.
EXEMPLO_ESTRUTURA: dict = {
    "titulo": "Área do retângulo — o piso da sala",
    "topico": "area_retangulo",
    "dados": {"base": 12, "altura": 7, "area": 84},
    "blocos": [
        {"diz": "Olha o piso dessa sala. Quatro cantos retos, doze metros de um "
                "lado e sete do outro. Área é quanto de piso cabe aqui dentro.",
         "figura": {"gerador": "retangulo", "params": {"base": 12, "altura": 7}},
         "espera": "media"},
        {"diz": "Antes de eu fazer a conta, pensa comigo: pra saber quantos "
                "quadradinhos de um metro cabem aí, você soma doze com sete ou "
                "multiplica um pelo outro?",
         "pergunta": {"escuta_s": 10, "senao": "por_que_multiplica",
                      "acerta": ["multiplica", "vezes", "multiplicar"],
                      "confirma": "Isso mesmo, multiplica. Somar daria o contorno, "
                                  "não o que cabe dentro."}},
        {"diz": "Multiplica a base pela altura, e o resultado já sai em metros "
                "quadrados porque você contou quadradinhos de um metro por um metro.",
         "calc": {"gerador": "area_retangulo", "params": {"base": 12, "altura": 7}},
         "mostra_passos": True,
         "diz_passos": ["Doze vezes sete dá oitenta e quatro."],
         "espera": "longa"},
        {"diz": "Oitenta e quatro metros quadrados de piso.", "espera": "media"},
    ],
    "ramos": {
        "por_que_multiplica": [
            {"diz": "Multiplica porque a sala é uma grade: sete fileiras de doze "
                    "quadradinhos cada uma. Somar doze com sete só te daria dois "
                    "lados, não a grade inteira.",
             "figura": {"gerador": "retangulo", "params": {"base": 12, "altura": 7}},
             "espera": "media"},
        ],
    },
}


# ═══════════════════════════════════════════ SEM PLANO — o fallback que não mente
# Quando o planejador não consegue montar a aula, a saída antiga era devolver a
# aula de ouro do TRAPÉZIO. O aluno perguntava de porcentagem e o professor
# começava a falar de terreno, sem avisar: exatamente o "professor passa conteúdo
# que não tem nada a ver" que a regra única proíbe. Trocar de assunto calado é
# mentir. Aqui ele diz o que aconteceu e devolve a vez pro aluno.
AULA_SEM_PLANO: dict = {
    "titulo": "Não consegui preparar essa aula",
    "topico": "sem_plano",
    "dados": {},
    "blocos": [
        {"diz": "Vou ser sincero com você: eu não consegui montar a aula sobre "
                "isso agora. E eu não vou te empurrar outro assunto no lugar.",
         "espera": "media"},
        {"diz": "Tenta de novo, ou me diz a mesma coisa com outras palavras — "
                "às vezes na segunda eu pego. Se quiser, manda um exemplo com "
                "números que fica mais fácil pra mim.",
         "espera": "media"},
    ],
    "ramos": {
        "por_que": [
            {"diz": "Porque eu monto a aula antes de falar, e dessa vez a montagem "
                    "não fechou. Prefiro te dizer isso a inventar uma explicação."},
        ],
        "nao_entendi": [
            {"diz": "É simples: eu falhei em preparar essa aula. Não é você. "
                    "Me manda o assunto de novo, com outras palavras."},
        ],
        "repete": [
            {"diz": "Não consegui preparar essa aula agora. Manda de novo que "
                    "eu tento outra vez."},
        ],
    },
}

_CATALOGO = {"trapezio": TRAPEZIO, "pitagoras": PITAGORAS,
             "eq_primeiro_grau": EQ_PRIMEIRO_GRAU, "regra_de_tres": REGRA_DE_TRES,
             "fracao": FRACAO}


def carregar(nome: str) -> Aula:
    """A aula de ouro `nome`, já com os ramos genéricos mergeados.

    Deep copy: o tocador escreve `_resultado`/`_resp_scriptada` nos beats, e os
    dicts aqui são de módulo — sem a cópia, uma execução contamina a próxima.
    """
    return Aula.de_json(copy.deepcopy(_com_genericos(_CATALOGO[nome])))


def disponiveis() -> list[str]:
    return list(_CATALOGO)
