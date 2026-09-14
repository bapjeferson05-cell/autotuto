"""fala_formula.py — LaTeX que o projeto gera → frase em português falado.

Por que existe: o aluno VÊ o passo na lousa, mas se não houver `diz_passos`
escrito à mão ele aparece MUDO. Dual coding pela metade não é dual coding — e
escrever a narração de cada passo de cada conta na mão não escala.

Por que NÃO é o Speech Rule Engine do MathJax (a recomendação do levantamento):
o SRE resolve LaTeX arbitrário e custa um runtime Node inteiro. Aqui o LaTeX não
é arbitrário — quem escreve é o `calc.py`, e o vocabulário INTEIRO do projeto são
7 comandos (\\dfrac \\cdot \\sqrt \\pi \\approx \\mathrm \\text) e 5 símbolos.
Para esse alvo fechado, stdlib puro resolve, sem dep nova e sem Node.

A regra do projeto manda aqui também: na dúvida, CALA. Qualquer coisa fora do
vocabulário conhecido devolve None, e o tocador fica em silêncio em vez de
narrar uma fórmula errada com voz de professor.

Depende de: nada. Nem de `config`.
"""
from __future__ import annotations

import re

# comando LaTeX -> como um professor lê em voz alta
_COMANDOS = {
    r"\cdot": "vezes",
    r"\pi": "pi",
    r"\approx": "é aproximadamente",
    r"\%": "por cento",
}
_SIMBOLOS = {
    "=": "é igual a",
    "+": "mais",
    "-": "menos",
    "(": "abre parênteses",
    ")": "fecha parênteses",
    "%": "por cento",
}
# `\mathrm{mdc}` e afins: a sigla lida por extenso é mais clara que soletrada
_SIGLAS = {"mdc": "o máximo divisor comum", "mmc": "o mínimo múltiplo comum"}
_EXPOENTES = {"2": "ao quadrado", "3": "ao cubo"}


def _chaves(s: str, i: int) -> tuple[str, int]:
    """Conteúdo do bloco `{...}` que começa em `s[i]`, e o índice depois dele."""
    if i >= len(s) or s[i] != "{":
        raise ValueError("esperava '{'")
    nivel, j = 0, i
    while j < len(s):
        if s[j] == "{":
            nivel += 1
        elif s[j] == "}":
            nivel -= 1
            if nivel == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("chave não fechada")


def fala(latex: str) -> str | None:
    """Frase falada em PT-BR, ou None se aparecer algo fora do vocabulário."""
    try:
        return _limpa(_traduz(latex.strip()))
    except (ValueError, IndexError):
        return None


def _traduz(s: str) -> str:
    saida: list[str] = []
    i = 0
    # `\%` abrindo a fórmula é o NOME da grandeza, não a unidade: "a porcentagem
    # é igual a parte sobre todo", nunca "por cento é igual a...".
    if s.startswith(r"\%"):
        saida.append("a porcentagem")
        i = 2
    while i < len(s):
        c = s[i]

        if c.isspace():
            i += 1
            continue

        if c == "\\":
            m = re.match(r"\\[a-zA-Z]+|\\%", s[i:])
            if not m:
                raise ValueError(f"comando LaTeX ilegível em {s[i:i+8]!r}")
            cmd = m.group()
            i += len(cmd)
            if cmd in (r"\dfrac", r"\frac", r"\tfrac"):
                num, i = _chaves(s, i)
                den, i = _chaves(s, i)
                saida.append(f"{_traduz(num)} sobre {_traduz(den)}")
            elif cmd == r"\sqrt":
                dentro, i = _chaves(s, i)
                saida.append(f"raiz quadrada de {_traduz(dentro)}")
            elif cmd in (r"\mathrm", r"\text"):
                dentro, i = _chaves(s, i)
                t = dentro.strip()
                saida.append(_SIGLAS.get(t, t))
                # sigla seguida de (a, b): professor diz "de 4 e 6", não
                # "abre parênteses 4 vírgula 6 fecha parênteses".
                if t in _SIGLAS:
                    m = re.match(r"\s*\(([^()]*)\)", s[i:])
                    if m:
                        args = [a.strip() for a in m.group(1).split(",") if a.strip()]
                        saida.append("de " + " e ".join(_traduz(a) for a in args))
                        i += len(m.group())
            elif cmd in _COMANDOS:
                saida.append(_COMANDOS[cmd])
            else:
                raise ValueError(f"comando desconhecido: {cmd}")
            continue

        if c == "^":
            i += 1
            if i < len(s) and s[i] == "{":
                exp, i = _chaves(s, i)
            else:
                exp, i = s[i], i + 1
            exp = exp.strip()
            saida.append(_EXPOENTES.get(exp, f"elevado a {_traduz(exp)}"))
            continue

        if c in _SIMBOLOS:
            saida.append(_SIMBOLOS[c])
            i += 1
            continue

        m = re.match(r"\d+(?:[.,]\d+)?", s[i:])
        if m:                                   # número: o TTS lê melhor cru
            saida.append(m.group().replace(".", ","))
            i += len(m.group())
            continue

        if c.isalpha():                          # nome de variável (A, b, h, x…)
            saida.append(c)
            i += 1
            continue

        if c in ",":                             # separador: vira pausa
            saida.append(",")
            i += 1
            continue

        raise ValueError(f"símbolo fora do vocabulário: {c!r}")

    return " ".join(saida)


def _limpa(t: str) -> str:
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t
