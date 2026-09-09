"""fillers.py — o "estou aqui" imediato, enquanto o resto carrega.

Sistemas de voz profissionais põem um LLM rápido pra isso. No nosso caso, pro MVP,
NÃO precisa de LLM: os ramos da aula de ouro já estão na memória (latência zero), e
o classificador roda em <5 ms. Então o filler é um banco de frases fixas, escolhido
pelo gatilho. Instantâneo.

    falar(filler_para("por_que_div_2"))   # "Boa pergunta."
    ... aí toca o ramo (que já está pronto)

Onde um LLM rápido REALMENTE ajudaria: o cold start — aluno faz uma pergunta nova,
sem aula pronta, e o planejador (Claude, 2-5 s) tem que montar tudo. Aí `GENERICO`
cobre a espera. Mas isso não é o caminho crítico da demo.
"""
from __future__ import annotations

import random

_BANCO: dict[str, tuple[str, ...]] = {
    "por_que_div_2": ("Boa pergunta.", "Ó só.", "Deixa eu te mostrar de onde vem esse dois."),
    "por_que": ("Boa pergunta.", "Deixa eu explicar o porquê.", "Então..."),
    "nao_entendi": ("Sem problema.", "Calma, vamos de novo.", "Deixa eu refazer essa parte."),
    "e_triangulo": ("Boa.", "Olha que legal.", "Deixa eu te mostrar."),
    "decompor": ("Tem sim.", "Claro, tem outro jeito.", "Ó, dá pra fazer assim também."),
    # cold start: aluno pediu algo que não tem aula pronta — cobre a espera do planejador
    "_planejando": ("Deixa eu montar isso aqui.", "Só um segundo, já vou te mostrar.",
                    "Boa. Peraí que eu desenho isso."),
}
GENERICO = ("Certo.", "Deixa eu ver.", "Um instante.")


def filler_para(gatilho: str | None) -> str:
    return random.choice(_BANCO.get(gatilho or "", GENERICO))
