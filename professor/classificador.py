"""classificador.py — fala do aluno → gatilho de ramo.

Regra de palavra-chave agora (rápido, offline, testável). Trocar por um classificador
LLM depois é isolado: só esta função muda.

    gat = classificar("por que que divide por dois?", aula.ramos)
    -> "por_que_div_2"
"""
from __future__ import annotations

import re
import unicodedata


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


# ordem importa: o primeiro que casar ganha. cada entrada é (gatilho, [regex...]).
_REGRAS: list[tuple[str, tuple[str, ...]]] = [
    ("por_que_div_2", (r"\b(por ?que|pq).*(divid|sobre|barra|\bdois\b|\b2\b|meio|metade)",
                       r"(divid\w*|sobre|barra).*(dois|\b2\b)",
                       r"de onde (vem|saiu|sai).*(dois|\b2\b)",
                       r"(dividir|dividido|divide) por (dois|2)")),
    ("e_triangulo", (r"\b(e se|se fosse|e um|e o|vira|virasse|fosse).{0,12}triangulo",
                     r"\btriangulo\b")),
    ("decompor", (r"outr[oa] (jeito|forma|maneira)", r"n[aã]o (decorei|lembro|sei).*(formula|conta)",
                  r"sem (a )?formula", r"sem decorar")),
    ("nao_entendi", (r"n[aã]o (entend|peguei|ficou claro|to entendendo|consegui)",
                     r"\b(de novo|mais devagar|repete|repetir|como assim|me perdi|confus)",
                     r"explica (melhor|de novo)", r"n[aã]o captei")),
    ("por_que", (r"\b(por ?que|pq|porqu[eê])\b", r"qual (o|e o) motivo", r"por qual (razao|motivo)")),
]
_COMPILADAS = [(g, [re.compile(p) for p in ps]) for g, ps in _REGRAS]


def classificar(fala: str, ramos: list[str] | dict | None = None) -> str | None:
    """Devolve o gatilho de ramo, ou None. Se `ramos` vier, só considera gatilhos
    presentes nele — e um 'por que...' genérico rebaixa pro primeiro 'por_que*'
    que a aula tiver (ex.: 'por_que_div_2')."""
    t = _norm(fala)
    disp = list(ramos) if ramos else None
    for gat, res in _COMPILADAS:
        alvo = gat
        if disp is not None and gat not in disp:
            alvo = next((r for r in disp if r.startswith("por_que")), None) if gat == "por_que" else None
            if alvo is None:
                continue
        if any(r.search(t) for r in res):
            return alvo
    return None


if __name__ == "__main__":
    testes = [
        ("Peraí, por que que divide por dois?", "por_que_div_2"),
        ("não entendi essa parte", "nao_entendi"),
        ("e se fosse um triângulo?", "e_triangulo"),
        ("tem outro jeito? não decorei a fórmula", "decompor"),
        ("por que a altura é perpendicular?", "por_que"),
        ("beleza, entendi", None),
    ]
    ramos = ["por_que_div_2", "nao_entendi", "e_triangulo", "decompor", "por_que"]
    for fala, esp in testes:
        got = classificar(fala, ramos)
        print(f"  {'ok ' if got == esp else 'XX '} {fala!r} -> {got}  (esperado {esp})")
