"""exercicios.py — gera questão NOVA pro aluno tentar. Não explica: cobra.

Por que existe: o projeto inteiro explica. O `pergunta` do tocador pergunta UMA
vez, sobre a aula dele. Ninguém nunca dá cinco questões parecidas pro aluno
fazer — e é isso que instala a memória. Autópsia real: um aluno assistiu 18
minutos de vídeo que cobria 100% da prova, com mnemônico e tudo, e zerou as duas
questões que eram pura definição. Ver não instala; produzir instala.

A regra que manda no desenho: A RESPOSTA NUNCA É ESCRITA À MÃO. O enunciado é
template, mas o gabarito e os passos saem do `calc` — o mesmo motor que o
professor usa na lousa. Assim é impossível o exercício e a resposta discordarem,
e nenhum tópico ganha banco de questão decorada. Tópico novo = uma receita de
3 linhas, não um gerador.

Determinístico por semente: a mesma semente dá a mesma lista, então dá pra
testar e dá pra você refazer a mesma série amanhã.

Depende só de `calc` + stdlib. Sem LLM, sem rede.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from autotuto import calc


@dataclass
class Exercicio:
    topico: str
    enunciado: str                      # o que o aluno lê
    resposta: str                       # o que o Python calculou
    passos: list[str] = field(default_factory=list)   # LaTeX, do próprio calc
    calc: dict = field(default_factory=dict)          # pra o tocador resolver na lousa

    def como_beat(self) -> dict:
        """Vira um beat de aula — o professor resolve na lousa, com passos."""
        return {"diz": self.enunciado, "calc": self.calc,
                "mostra_passos": True, "espera": "longa"}


def _inteiro(rng, a, b, passo=1):
    return rng.randrange(a, b + 1, passo)


def _limpa_num(v):
    """35.0 -> 35. Área com casa decimal zerada é ruído no gabarito."""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def _ternos_pitagoricos(teto: int) -> list[tuple[int, int]]:
    """Pares de catetos com hipotenusa inteira, gerados — não decorados.

    Parametrização de Euclides: a = m²-n², b = 2mn, c = m²+n². Dá infinitos;
    aqui a gente corta no `teto` porque é aluno de 7º ano, não olimpíada.
    Uma lista fixa de seis pares era jukebox: `serie(10)` esgotava e devolvia
    seis em silêncio.
    """
    import math
    fora = set()
    for m in range(2, 12):
        for n in range(1, m):
            if math.gcd(m, n) != 1 or (m - n) % 2 == 0:
                continue
            a, b = m * m - n * n, 2 * m * n
            for k in range(1, teto):
                ka, kb = a * k, b * k
                if max(ka, kb) > teto:
                    break
                fora.add((min(ka, kb), max(ka, kb)))
    return sorted(fora)


# Dificuldade 1 é SÓ a família do 3-4-5. Não é por ser número menor — é por ser
# a que o aluno reconhece: a hipotenusa sai múltipla de 5 e ele confere de
# cabeça. Jogar (5,12,13) e (8,15,17) no nível 1 é dar terno que ele nunca viu
# e chamar de fácil.
_TERNOS = {1: [(3 * k, 4 * k) for k in range(1, 11)],
           2: _ternos_pitagoricos(40),
           3: _ternos_pitagoricos(70)}


# ─────────────────────────────────────────────────────────────── as receitas
# topico -> (gerador do calc, sorteia params, molda o enunciado)
# `dif` 1..3 mexe só no tamanho dos números e em deixar armadilha entrar.

def _p_complemento(rng, dif):
    # dif 3 solta ângulo > 90: o que NÃO TEM complemento. É a pegadinha que
    # derrubou o aluno na prova real, então ela precisa aparecer no treino.
    if dif >= 3 and rng.random() < 0.35:
        return {"angulo": _inteiro(rng, 91, 175)}
    return {"angulo": _inteiro(rng, 5, 88)}


def _p_suplemento(rng, dif):
    if dif >= 3 and rng.random() < 0.25:
        return {"angulo": _inteiro(rng, 181, 300)}
    return {"angulo": _inteiro(rng, 10, 178)}


def _p_eq(rng, dif):
    # raiz inteira sempre: aluno de 7º ano não trabalha fração aqui
    a = rng.choice([2, 3, 4, 5] if dif == 1 else [-5, -4, -3, -2, 2, 3, 4, 5, 6, 7])
    raiz = _inteiro(rng, -12, 12) if dif >= 2 else _inteiro(rng, 1, 12)
    return {"a": a, "b": -a * raiz}


def _p_regra3(rng, dif):
    a = _inteiro(rng, 2, 6 if dif == 1 else 12)
    unit = _inteiro(rng, 2, 9 if dif == 1 else 25)
    return {"a": a, "b": a * unit, "c": _inteiro(rng, 2, 9 if dif == 1 else 20)}


def _p_fracao(rng, dif):
    # fração sempre irredutível: "2/4 de 36" é enunciado que nenhum professor
    # escreve, e ainda entrega meio caminho da resposta de graça.
    import math
    while True:
        den = rng.choice([2, 4] if dif == 1 else [2, 3, 4, 5, 6, 8])
        num = _inteiro(rng, 1, den - 1)
        if math.gcd(num, den) == 1:
            break
    return {"num": num, "den": den, "todo": den * _inteiro(rng, 2, 6 if dif == 1 else 15)}


def _p_pct(rng, dif):
    todo = rng.choice([50, 100, 200] if dif == 1 else [40, 60, 80, 120, 150, 250])
    return {"parte": todo * rng.choice([10, 20, 25, 50]) // 100, "todo": todo}


_RECEITAS: dict[str, tuple] = {
    "complemento": ("complemento", _p_complemento,
                    "Calcule o complemento do ângulo de {angulo} graus."),
    "suplemento": ("suplemento", _p_suplemento,
                   "Calcule o suplemento do ângulo de {angulo} graus."),
    "area_trapezio": ("area_trapezio",
                      lambda r, d: {"B": _inteiro(r, 8, 30, 2), "b": _inteiro(r, 4, 7, 1),
                                    "h": _inteiro(r, 3, 12)},
                      "Um trapézio tem base maior {B}, base menor {b} e altura {h}. "
                      "Qual é a área?"),
    "area_triangulo": ("area_triangulo",
                       lambda r, d: {"base": _inteiro(r, 4, 20, 2),
                                     "altura": _inteiro(r, 3, 15)},
                       "Um triângulo tem base {base} e altura {altura}. Qual é a área?"),
    "area_retangulo": ("area_retangulo",
                       lambda r, d: {"base": _inteiro(r, 3, 20),
                                     "altura": _inteiro(r, 2, 15)},
                       "Um retângulo tem lados {base} e {altura}. Qual é a área?"),
    "area_circulo": ("area_circulo", lambda r, d: {"raio": _inteiro(r, 2, 12)},
                     "Qual é a área de um círculo de raio {raio}?"),
    "comprimento_circunferencia": (
        "comprimento_circunferencia", lambda r, d: {"raio": _inteiro(r, 2, 15)},
        "Qual é o comprimento de uma circunferência de raio {raio}?"),
    "pitagoras": ("pitagoras", lambda r, d: dict(zip(("a", "b"), r.choice(_TERNOS[d]))),
                  "Um triângulo retângulo tem catetos {a} e {b}. "
                  "Quanto mede a hipotenusa?"),
    # "2x + (-10) = 0" é saída de computador. Prova escreve "2x - 10 = 0".
    "eq_primeiro_grau": ("eq_primeiro_grau", _p_eq,
                         lambda p: (f"Resolva a equação: {p['a']}x "
                                    f"{'+' if p['b'] >= 0 else '-'} "
                                    f"{abs(p['b'])} = 0")),
    "regra_de_tres": ("regra_de_tres", _p_regra3,
                      "Se {a} cadernos custam {b} reais, quanto custam {c} cadernos?"),
    "porcentagem": ("porcentagem", _p_pct,
                    "Quantos por cento {parte} é de {todo}?"),
    "fracao_de": ("fracao_de", _p_fracao,
                  "Quanto é {num}/{den} de {todo}?"),
    "mdc": ("mdc", lambda r, d: {"a": _inteiro(r, 8, 40, 2), "b": _inteiro(r, 8, 60, 2)},
            "Qual é o máximo divisor comum de {a} e {b}?"),
    "mmc": ("mmc", lambda r, d: {"a": _inteiro(r, 2, 12), "b": _inteiro(r, 2, 15)},
            "Qual é o mínimo múltiplo comum de {a} e {b}?"),
}


def topicos() -> list[str]:
    return sorted(_RECEITAS)


def gerar(topico: str, dificuldade: int = 2, semente: int | None = None) -> Exercicio:
    """Uma questão nova de `topico`. A resposta vem do `calc`, nunca de template."""
    if topico not in _RECEITAS:
        raise ValueError(f"exercício desconhecido: {topico!r} — "
                         f"tem {', '.join(topicos())}")
    dif = max(1, min(3, int(dificuldade)))
    rng = random.Random(semente)
    gerador, sorteia, molde = _RECEITAS[topico]
    params = sorteia(rng, dif)
    r = calc.CATALOGO[gerador](**params)     # ← o Python resolve. Sempre.
    unidade = f" {r.unidade}" if r.unidade and r.unidade != "°" else ""
    enunciado = molde(params) if callable(molde) else molde.format(**params)
    return Exercicio(
        topico=topico,
        enunciado=enunciado,
        resposta=f"{_limpa_num(r.valor)}{unidade}",
        passos=list(r.passos),
        calc={"gerador": gerador, "params": params},
    )


def serie(topico: str, quantas: int = 5, dificuldade: int = 2,
          semente: int | None = None) -> list[Exercicio]:
    """`quantas` questões DIFERENTES do mesmo tópico.

    Repetir enunciado numa lista de treino é desperdiçar a questão: o aluno
    reconhece e responde de memória, que é exatamente o que a gente quer evitar.
    """
    rng = random.Random(semente)
    vistos: set[str] = set()
    saida: list[Exercicio] = []
    for _ in range(quantas * 40):            # teto: evita laço infinito
        if len(saida) >= quantas:
            break
        e = gerar(topico, dificuldade, semente=rng.randrange(2**31))
        if e.enunciado in vistos:
            continue
        vistos.add(e.enunciado)
        saida.append(e)
    if len(saida) < quantas:
        # devolver menos CALADO é mentir a folha de treino: o aluno pede dez,
        # recebe seis e não fica sabendo. Falha alto dizendo quantas dá.
        raise ValueError(
            f"{topico!r} na dificuldade {dificuldade} só rende {len(saida)} "
            f"questões distintas, e você pediu {quantas}. Sobe a dificuldade "
            f"ou pede menos.")
    return saida


# ─────────────────────────────────────────────────────── folha de treino (CLI)
_AJUDA = """uso:  python -m autotuto.exercicios <tópico> [quantas] [dificuldade]
      python -m autotuto.exercicios prova                 (a folha da prova toda)
      python -m autotuto.exercicios --lista

O gabarito sai DEPOIS, separado. Responde tudo antes de rolar a tela — se você
olhar a resposta antes de tentar, o treino não vale nada: reconhecer não é
lembrar, e a prova cobra lembrar.
"""

# Os tópicos de uma prova de geometria de 7º ano de verdade, na ordem dela.
PROVA_GEOMETRIA = ["complemento", "suplemento", "area_circulo",
                   "comprimento_circunferencia", "pitagoras", "area_triangulo"]


def folha(topicos_: list[str], quantas: int = 3, dificuldade: int = 2,
          semente: int | None = None) -> list[Exercicio]:
    rng = random.Random(semente)
    fora: list[Exercicio] = []
    for t in topicos_:
        fora += serie(t, quantas, dificuldade, semente=rng.randrange(2**31))
    return fora


def main(argv: list[str] | None = None) -> int:
    import sys
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(_AJUDA)
        return 0
    if argv[0] == "--lista":
        print("\n".join(topicos()))
        return 0

    if argv[0] == "prova":
        quantas = int(argv[1]) if len(argv) > 1 else 3
        dif = int(argv[2]) if len(argv) > 2 else 2
        exs = folha(PROVA_GEOMETRIA, quantas, dif)
    else:
        topico = argv[0]
        if topico not in _RECEITAS:
            print(f"não conheço {topico!r}. tem:\n  " + "\n  ".join(topicos()))
            return 2
        quantas = int(argv[1]) if len(argv) > 1 else 5
        dif = int(argv[2]) if len(argv) > 2 else 2
        exs = serie(topico, quantas, dif)

    print(f"\n{len(exs)} questões · dificuldade {dif}\n")
    for i, e in enumerate(exs, 1):
        print(f"{i:2}. {e.enunciado}")
    print("\n" + "─" * 60)
    print("responde TUDO antes de rolar\n" + "─" * 60 + "\n\nGABARITO\n")
    for i, e in enumerate(exs, 1):
        print(f"{i:2}. {e.resposta}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
