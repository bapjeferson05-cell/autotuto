from __future__ import annotations
import re, unicodedata

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()

_REGRAS = [
    ("por_que_div_2", (r"\b(por ?que|pq).*(divid|sobre|metade|media|\bdois\b|\b2\b)",
                       r"(dividir|dividido|divide) por (dois|2)",
                       r"de onde (vem|saiu).*(dois|2)")),
    ("e_triangulo", (r"\b(e se|se fosse|virasse|vira).{0,14}triangulo", r"\btriangulo\b")),
    ("achar_hipotenusa", (r"\bhipotenusa\b", r"lado (maior|comprido)")),
    ("outro_numero", (r"\boutro numero\b", r"e se (fosse|desse) (outro|-?\d)")),
    ("e_se_menos", (r"\b(menos|menor|diminui|cai)\b.*\b(preco|valor|custa)",)),
    ("decompor", (r"outr[oa] (jeito|forma)", r"sem (a )?formula", r"nao decorei")),
    ("repete", (r"\b(repete|repetir|repetiu|de novo|outra vez|mais uma vez)\b",
                r"\b(nao ouvi|nao escutei|fala de novo)\b",
                r"^\s*(que|h[aã]n?|como|oi|hein)\s*\??\s*$")),
    ("nao_entendi", (r"nao (entend|peguei|ficou claro|consegui|captei)",
                     r"\b(mais devagar|como assim|me perdi|confus|perdid)",
                     r"explica (melhor|diferente)")),
    ("por_que", (r"\b(por ?que|pq|porqu[eê])\b", r"qual (o|e o) motivo")),
]
_COMPILADAS = [(g, [re.compile(p) for p in ps]) for g, ps in _REGRAS]

def classificar(fala: str, ramos) -> str | None:
    t = _norm(fala)
    disp = list(ramos) if ramos is not None else None
    for gat, res in _COMPILADAS:
        alvo = gat
        if disp is not None and gat not in disp:
            alvo = next((r for r in disp if r.startswith("por_que")), None) if gat == "por_que" else None
            if alvo is None:
                continue
        if any(r.search(t) for r in res):
            return alvo
    return None
