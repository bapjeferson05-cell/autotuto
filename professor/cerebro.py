"""cerebro.py — o LLM CURTO, só no caminho da interrupção.

Não é o planejador (esse monta a aula toda, uma vez). Aqui é uma pergunta rápida:
"o aluno interrompeu com ISSO; qual dos ramos já preparados responde — ou nenhum?".

Camadas (ver tocador._resolve_interrupcao):
  1. regex (classificador.classificar) — <5 ms, offline, sempre tenta primeiro
  2. este módulo — LLM curto, timeout apertado; se cair, devolve None
  3. fallback honesto (no tocador) — "essa eu não preparei, vou seguir"

Nunca devolve um gatilho que não está em `ramos`.
"""
from __future__ import annotations

import json

# ramos que TODA aula tem que ter (B do pedido). O tocador faz o merge:
#   est.aula.ramos = {**RAMOS_GENERICOS, **est.aula.ramos}   # a aula sempre vence
RAMOS_GENERICOS: dict[str, list[dict]] = {
    "por_que": [{"diz": "Boa pergunta. Aqui nada é regra decorada — cada passo tem um "
                        "motivo. Qual parte te deixou com o porquê?"}],
    "nao_entendi": [{"diz": "Sem problema. Deixa eu refazer essa parte de outro jeito, "
                            "mais devagar."}],
    "repete": [{"diz": "Claro. De novo, com calma:"}],
}


def com_ramos_genericos(ramos: dict | None) -> dict:
    """Garante por_que / nao_entendi / repete. A aula sobrescreve os genéricos."""
    return {**RAMOS_GENERICOS, **(ramos or {})}


def _catalogo(ramos: dict) -> str:
    linhas = []
    for nome, blocos in ramos.items():
        dica = (blocos[0].get("diz", "") if blocos else "")[:80]
        linhas.append(f"- {nome}: {dica}")
    return "\n".join(linhas)


def roteia_interrupcao(fala: str, contexto: str, ramos: dict, *, timeout: float = 8.0) -> str | None:
    """LLM curto: fala do aluno -> nome de um ramo de `ramos`, ou None ('nenhum').

    Blindado: sem LLM configurado / lento / resposta estranha -> None (o tocador
    cai no fallback honesto)."""
    try:
        from professor.planejador import _llm_json   # lazy: sem custo no import, sem ciclo
    except Exception:  # noqa: BLE001
        return None

    sis = ('Você roteia a dúvida de um aluno que INTERROMPEU uma aula para UM tópico '
           'que o professor já preparou. Se nenhum tópico responde a dúvida dele, '
           'responda "nenhum" — não invente. '
           'Responda SÓ um JSON: {"ramo": "<nome exato da lista>"} ou {"ramo": "nenhum"}.')
    usr = (f"O professor vinha dizendo:\n{contexto or '(começo da aula)'}\n\n"
           f'O aluno interrompeu: "{fala}"\n\n'
           f"Tópicos preparados:\n{_catalogo(ramos)}")

    try:
        txt = _llm_json([{"role": "system", "content": sis},
                         {"role": "user", "content": usr}], timeout=timeout)
        ini, fim = txt.find("{"), txt.rfind("}")
        ramo = json.loads(txt[ini:fim + 1]).get("ramo", "nenhum") if ini >= 0 else "nenhum"
    except Exception:  # noqa: BLE001  (timeout, JSON ruim, rede)
        return None
    return ramo if ramo in ramos else None
