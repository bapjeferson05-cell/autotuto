"""Validação matemática de aulas (checagem não-fatal de avisos).

Valida geradores de cálculos e figuras, execução de parâmetros,
e valores esperados (ex: áreas não-negativas).
"""
from __future__ import annotations

import inspect

from autotuto import calc
from autotuto.figuras import catalogo as figuras_catalogo


def _params_desconhecidos(fn, params: dict) -> list[str]:
    """Chaves de `params` que `fn` nem aceita (contrato mínimo e explícito:
    a ASSINATURA de verdade é a fonte, sem duplicar uma lista à parte que
    pode ficar desatualizada). Não checa tipo nem obrigatoriedade — só pega
    o "gerador certo, kwarg errado" que a autópsia mostrou (eq_primeiro_grau
    com `x=...`), ANTES de chamar a função."""
    parametros = inspect.signature(fn).parameters
    if any(p.kind is p.VAR_KEYWORD for p in parametros.values()):
        return []  # a função aceita **kwargs livremente
    return sorted(set(params) - set(parametros))


def _é_gerador_area_ou_comprimento(nome: str) -> bool:
    """Verifica se nome refere-se a um gerador de área ou comprimento."""
    return nome.startswith(("area_", "comprimento_", "perimetro_"))


# GRAVE = uma etapa do plano simplesmente NÃO aconteceu (ferramenta que não
# existe, ou existe mas explodiu com os params que o LLM mandou) — o aluno
# ficaria sem aquele passo. Diferente de "valor negativo": aí a conta rodou,
# só o número que saiu é suspeito — o passo aconteceu, só merece uma segunda
# olhada. Autópsia de 2026-09-12: um plano com "gerador de figura desconhecido"
# saía com `rel.ok=True` — o contrato mentia que deu tudo certo.
_PREFIXOS_GRAVES = ("gerador de calc desconhecido", "gerador de figura desconhecido")


def _é_grave(aviso: str) -> bool:
    return (aviso.startswith(_PREFIXOS_GRAVES)
            or " falhou:" in aviso
            or "argumento desconhecido" in aviso)


def avisos_graves(avisos: list[str]) -> list[str]:
    """Só os avisos graves (ferramenta ausente ou que falhou ao rodar) — o
    subconjunto que vale a pena mandar de volta pro LLM corrigir. P1.1:
    autópsia mostrou o modelo escolher o gerador certo (eq_primeiro_grau) e
    mandar um kwarg que não existe na assinatura — isso merece a MESMA
    chance de correção que um erro de schema, não só virar `ok=False` depois."""
    return [a for a in avisos if _é_grave(a)]


def houve_falha_grave(avisos: list[str]) -> bool:
    """True se algum aviso é grave (ferramenta ausente ou que falhou ao rodar)."""
    return bool(avisos_graves(avisos))


def checar_matematica(aula: dict) -> list[str]:
    """Valida cálculos e figuras de uma aula, retornando avisos não-fatais.

    Itera beats em blocos e ramos, checando:
    - Geradores de calc existem e não explodem
    - Valores de área/comprimento são não-negativos
    - Geradores de figura (nomeados) existem

    Args:
        aula: dicionário com 'blocos' e 'ramos'

    Returns:
        Lista de avisos (string), vazia se tudo OK
    """
    avisos: list[str] = []

    # Itera beats em blocos
    for beat in aula.get("blocos", []):
        avisos.extend(_validar_beat(beat))

    # Itera beats em ramos
    for nome_ramo, beats in aula.get("ramos", {}).items():
        for beat in beats:
            avisos.extend(_validar_beat(beat))

    return avisos


def _validar_beat(beat: dict) -> list[str]:
    """Valida um beat individual (pode ter calc e/ou figura)."""
    avisos: list[str] = []

    # Valida calc se presente
    if "calc" in beat:
        avisos.extend(_validar_calc(beat["calc"]))

    # Valida figura se presente
    if "figura" in beat:
        avisos.extend(_validar_figura(beat["figura"]))

    return avisos


def _validar_calc(calc_spec: dict) -> list[str]:
    """Valida um spec de cálculo."""
    avisos: list[str] = []
    gerador = calc_spec.get("gerador")

    if not gerador:
        return avisos

    # Checa se gerador existe
    if gerador not in calc.CATALOGO:
        avisos.append(f"gerador de calc desconhecido: {gerador}")
        return avisos

    fn = calc.CATALOGO[gerador]
    params = calc_spec.get("params") or {}

    # contrato explícito: rejeita kwarg que a assinatura nem tem ANTES de
    # rodar (autópsia 2026-09-12: eq_primeiro_grau(a, b) chamado com um
    # `x` extra). A mensagem tem que dizer exatamente o que tirar e o que
    # é aceito — é ela que vai voltar pro LLM corrigir no retry.
    ruins = _params_desconhecidos(fn, params)
    if ruins:
        aceitos = ", ".join(inspect.signature(fn).parameters)
        avisos.append(
            f"{gerador}: argumento desconhecido {ruins} — {gerador} só aceita "
            f"({aceitos}). Remova {ruins} da chamada.")
        return avisos

    try:
        resultado = fn(**params)
    except Exception as e:
        avisos.append(f"{gerador} falhou: {e}")
        return avisos

    # Checa se o valor é um número negativo (para geradores de área/comprimento)
    if isinstance(resultado.valor, (int, float)):
        if resultado.valor < 0 and _é_gerador_area_ou_comprimento(gerador):
            avisos.append(f"{gerador}: valor negativo ({resultado.valor})")

    return avisos


def _validar_figura(figura_spec: dict) -> list[str]:
    """Valida um spec de figura."""
    avisos: list[str] = []
    gerador = figura_spec.get("gerador")

    if not gerador:
        return avisos

    # Specs inline (gerador="figura") não são validados aqui
    if gerador == "figura":
        return avisos

    # Checa se gerador nomeado existe
    if gerador not in figuras_catalogo.GERADORES:
        avisos.append(f"gerador de figura desconhecido: {gerador}")

    return avisos
