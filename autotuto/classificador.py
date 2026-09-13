from __future__ import annotations
import re, unicodedata

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


# ────────────────────────────────────────────── avaliador numérico (P1)
# autópsia 2026-09-12: "4", "quatro" e "o mdc é 4" são a MESMA resposta —
# comparar substring de frase inteira não enxerga isso. Camada determinística
# pequena (não precisa de IA pra número): acha o primeiro número na fala, em
# dígito ou por extenso (0-100, o suficiente pra resposta curta de aluno).
_UNIDADES = {"zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3,
             "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9,
             "dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14,
             "quatorze": 14, "quinze": 15, "dezesseis": 16, "dezessete": 17,
             "dezoito": 18, "dezenove": 19}
_DEZENAS = {"vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50,
            "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90}


def extrai_numero(texto: str) -> float | None:
    """Primeiro número em `texto` — dígito ('4', '20.5') ou por extenso
    ('quatro', 'vinte e cinco'). None se não achar nenhum."""
    d = _norm(texto)
    m = re.search(r"-?\d+(?:\.\d+)?", d)
    if m:
        return float(m.group())
    m = re.search(rf"\b({'|'.join(_DEZENAS)})\b(?:\s+e\s+({'|'.join(_UNIDADES)}))?", d)
    if m:
        v = _DEZENAS[m.group(1)]
        return float(v + _UNIDADES[m.group(2)]) if m.group(2) else float(v)
    m = re.search(rf"\b({'|'.join(_UNIDADES)})\b", d)
    if m:
        return float(_UNIDADES[m.group(1)])
    if re.search(r"\bcem\b|\bcento\b", d):
        return 100.0
    return None


def mesma_resposta_numerica(a: str, b: str) -> bool:
    """True se as duas falas carregam o MESMO número (dígito ou por extenso)."""
    na, nb = extrai_numero(a), extrai_numero(b)
    return na is not None and nb is not None and na == nb

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
