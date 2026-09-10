"""
Cerebro: Roteador de interrupção.

Módulo responsável por rotear dúvidas de alunos que interrompem a aula
para um dos tópicos já preparados pelo professor, ou para "nenhum" se não
houver ramo adequado.
"""
from __future__ import annotations
import json
from autotuto.config import CEREBRO_TIMEOUT_S
from autotuto import llm as _llm

_SIS = ('Você roteia a dúvida de um aluno que INTERROMPEU uma aula para UM tópico já '
        'preparado pelo professor. Se nenhum resolve, responda "nenhum" — não invente. '
        'Responda só: {"ramo": "<nome exato da lista>"} ou {"ramo": "nenhum"}.')


def _catalogo(ramos: dict) -> str:
    """
    Constrói um catálogo legível dos ramos disponíveis.

    Formata cada ramo como: "- <nome>: <primeiro 80 chars do diz>"

    Args:
        ramos: Dicionário de ramos com estrutura {nome: [{"diz": "..."}, ...]}

    Returns:
        String formatada com um ramo por linha
    """
    return "\n".join(f"- {n}: {(b[0].get('diz','') if b else '')[:80]}" for n, b in ramos.items())


def roteia_interrupcao(fala, contexto, ramos, *, perguntar=_llm.perguntar) -> str | None:
    """
    Roteia uma interrupção do aluno para um ramo preparado ou "nenhum".

    Usa um LLM para determinar qual dos tópicos preparados (ramos) é mais
    relevante para a dúvida do aluno. Se nenhum for adequado, retorna None.

    Função "blindada": qualquer exceção durante a chamada ao LLM, falha de
    parse JSON, ou ramo inválido resultam em None (não propaga exceções).

    Args:
        fala: Texto da interrupção do aluno
        contexto: Contexto de onde a aula estava (o que o professor vinha dizendo)
        ramos: Dicionário de ramos disponíveis com estrutura {nome: [{"diz": "..."}, ...]}
        perguntar: Função injetável de chamada ao LLM (padrão: llm.perguntar).
                   Assinatura: perguntar(mensagens, *, timeout, json_mode=True) -> str

    Returns:
        Nome do ramo escolhido (string) se válido e em ramos.
        None se: LLM diz "nenhum", ramo não existe, LLM falha, ou JSON é inválido.
    """
    usr = (f"O professor vinha dizendo:\n{contexto or '(começo)'}\n\n"
           f'O aluno interrompeu: "{fala}"\n\nTópicos preparados:\n{_catalogo(ramos)}')
    try:
        txt = perguntar([{"role": "system", "content": _SIS},
                         {"role": "user", "content": usr}], timeout=CEREBRO_TIMEOUT_S)
        ini, fim = txt.find("{"), txt.rfind("}")
        ramo = json.loads(txt[ini:fim + 1]).get("ramo", "nenhum") if ini >= 0 else "nenhum"
    except Exception:
        return None
    return ramo if ramo in ramos else None
