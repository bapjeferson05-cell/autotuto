"""avaliador.py — avaliação semântica de resposta (P1.2).

Os crivos de `pergunta.acerta` em `classificador.py` (substring normalizada e
equivalência numérica) são determinísticos, baratos, e resolvem a maioria dos
casos sem chamar LLM nenhum. Mas nenhum dos dois enxerga o SENTIDO de uma
resposta: nem uma resposta CERTA dita com outras palavras ("porque ela fica
deitada" pra "por que dividir por dois"), nem uma resposta PARCIAL (acertou
um pedaço do raciocínio, mas não fechou a ideia). Só entender sentido resolve
essas duas faixas — por isso, e só por isso, entra o LLM aqui.

Função "blindada" como `cerebro.roteia_interrupcao`: qualquer falha (timeout,
LLM fora do ar, JSON quebrado, veredito fora do vocabulário) devolve None — o
chamador trata None como "sem veredito" e cai no caminho que já existia antes
do P1.2 (nunca trava a aula esperando o LLM, nunca inventa um veredito).

Problema DIFERENTE do P1.1 (`classificador._numero_atomico`): P1.1 evita falso
positivo quando um número aparece só de passagem numa frase; este módulo
avalia o sentido de respostas que os crivos determinísticos já descartaram.
"""
from __future__ import annotations
import json
from autotuto.config import AVALIADOR_TIMEOUT_S
from autotuto import llm as _llm

_VEREDITOS = {"certo", "parcial", "errado"}

# O erro caro aqui é assimétrico, e o modelo local errava justamente pro lado
# caro: reprovou uma definição de triângulo tecnicamente correta só porque não
# era a redação esperada (achado em bateria local). Marcar de errado quem
# acertou faz o professor explicar o que o aluno já sabia — e, pior, dá a
# entender que ele errou. Marcar de parcial quem errou só rende uma entrada
# mais gentil na explicação, que ia acontecer de qualquer jeito. Por isso a
# régua manda empurrar pro lado do aluno em caso de dúvida.
_SIS = ('Você avalia a resposta de um aluno a UMA pergunta de aula. Julgue pelo '
        'SENTIDO, não pelas palavras: a lista de respostas esperadas são '
        'EXEMPLOS de redação, não as únicas formas certas. Uma resposta certa '
        'dita com outras palavras, mais curta, mais longa, ou por outro caminho '
        'válido é CERTA. Responda só com JSON: '
        '{"veredito": "certo"} se o que o aluno disse está correto; '
        '{"veredito": "parcial"} se acertou uma PARTE do raciocínio mas não '
        'fechou a ideia; {"veredito": "errado"} SÓ se a resposta contradiz o '
        'esperado ou não tem nada a ver, ou se o aluno só repetiu a pergunta ou '
        'disse que não sabe. '
        'Na dúvida entre certo e parcial, responda parcial. Na dúvida entre '
        'parcial e errado, responda parcial. "errado" é o último recurso.')


def avalia_resposta(pergunta: str, esperado: list[str], resposta: str, *,
                     perguntar=None) -> str | None:
    """
    Avalia semanticamente `resposta` (o que o aluno disse) contra `esperado`
    (a lista `pergunta.acerta` do beat) para a `pergunta` (o `diz` do beat).

    Só faz sentido chamar isto DEPOIS que os crivos determinísticos já
    disseram que não bateu — é a última chance de reconhecer um acerto (ou
    acerto parcial) dito com outras palavras, antes de tratar como errado.

    Retorna "certo", "parcial", "errado", ou None se o LLM falhar ou devolver
    algo fora desse vocabulário (o chamador trata None como "sem veredito").
    """
    perguntar = perguntar or _llm.perguntar   # late binding — ver planejador.planeja
    if not esperado or not resposta or not resposta.strip():
        return None
    usr = (f'Pergunta do professor: "{pergunta}"\n'
           f'Resposta(s) esperada(s): {", ".join(esperado)}\n'
           f'O aluno respondeu: "{resposta}"')
    try:
        txt = perguntar([{"role": "system", "content": _SIS},
                         {"role": "user", "content": usr}],
                        timeout=AVALIADOR_TIMEOUT_S)
        ini, fim = txt.find("{"), txt.rfind("}")
        veredito = json.loads(txt[ini:fim + 1]).get("veredito") if ini >= 0 else None
    except Exception:
        return None
    return veredito if veredito in _VEREDITOS else None
