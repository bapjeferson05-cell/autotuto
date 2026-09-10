"""Validação matemática de aulas (checagem não-fatal de avisos).

Valida geradores de cálculos e figuras, execução de parâmetros,
e valores esperados (ex: áreas não-negativas).
"""
from __future__ import annotations

from autotuto import calc
from autotuto.figuras import catalogo as figuras_catalogo


def _é_gerador_area_ou_comprimento(nome: str) -> bool:
    """Verifica se nome refere-se a um gerador de área ou comprimento."""
    return nome.startswith(("area_", "comprimento_", "perimetro_"))


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

    # Tenta executar o gerador com os params
    fn = calc.CATALOGO[gerador]
    params = calc_spec.get("params") or {}

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
