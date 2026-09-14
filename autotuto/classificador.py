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


def _numero_atomico(texto: str) -> float | None:
    """Como `extrai_numero`, mas só se o texto INTEIRO (normalizado) É o
    número — nada mais. 'quatro' e '4' contam; 'três triângulos' e 'dividido
    por dois' NÃO (o número aí é só uma peça de uma frase maior, não a
    resposta inteira). P1.1 (achado 2026-09-12): sem essa restrição, um
    'acerta' conceitual que menciona um número de passagem ('três
    triângulos') aceitava qualquer resposta que citasse o MESMO número por
    coincidência ('triângulo tem três lados') — falso positivo grotesco."""
    d = _norm(texto)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", d):
        return float(d)
    if d in _UNIDADES:
        return float(_UNIDADES[d])
    if d in _DEZENAS:
        return float(_DEZENAS[d])
    m = re.fullmatch(rf"({'|'.join(_DEZENAS)}) e ({'|'.join(_UNIDADES)})", d)
    if m:
        return float(_DEZENAS[m.group(1)] + _UNIDADES[m.group(2)])
    if d in ("cem", "cento"):
        return 100.0
    return None


def mesma_resposta_numerica(esperado: str, resposta: str) -> bool:
    """True só se `esperado` (um item de 'acerta') é uma resposta numérica
    ATÔMICA (o item inteiro é o número — ver `_numero_atomico`) e `resposta`
    (o que o aluno disse, livre) carrega o mesmo número em qualquer forma."""
    ne = _numero_atomico(esperado)
    if ne is None:
        return False
    nr = extrai_numero(resposta)
    return nr is not None and ne == nr

_REGRAS = [
    ("por_que_div_2", (r"\b(por ?que|pq).*(divid|sobre|metade|media|\bdois\b|\b2\b)",
                       r"(dividir|dividido|divide) por (dois|2)",
                       r"de onde (vem|saiu).*(dois|2)")),
    ("e_triangulo", (r"\b(e se|se fosse|virasse|vira).{0,14}triangulo", r"\btriangulo\b")),
    ("achar_hipotenusa", (r"\bhipotenusa\b", r"lado (maior|comprido)")),
    ("outro_numero", (r"\boutro numero\b", r"e se (fosse|desse) (outro|-?\d)")),
    ("e_se_menos", (r"\b(menos|menor|diminui|cai)\b.*\b(preco|valor|custa)",)),
    # fração: "e se cortasse em mais pedaços?" é a pergunta que leva à
    # equivalência (3/4 = 6/8), o pulo do gato do assunto.
    ("e_se_outro_corte", (r"(corta|cortar|cortasse|dividir|dividisse|partir)\b.{0,20}\b(mais|outro|outra|oito|8|dobro|metade) ",
                          r"\b(mais|outro|outra|menos) (peda[cç]os?|fatias?|partes?)\b",
                          r"\b(seis oitavos|6 ?/ ?8)\b",
                          r"\b(equivalent|mesma fracao|da na mesma|mesma coisa)\b")),
    ("e_se_metade", (r"\bmetade\b", r"\b(um meio|1 ?/ ?2)\b")),
    ("comeca_pelo_de_baixo", (r"come[cç]a\b.{0,20}\b(por onde|qual|de baixo|de cima|pelo)",
                              r"\b(qual|quem) (vem|entra) primeiro\b",
                              r"\b(de cima|de baixo|numerador|denominador)\b.{0,20}\b(primeiro|antes)\b")),
    # "de onde veio isso?" — vem ANTES do por_que genérico, senão a regra larga
    # do por_que engole a pergunta e o aluno recebe outra resposta.
    ("de_onde_veio", (r"de onde (veio|vem|saiu|surgiu|tiraram)",
                      r"quem (inventou|criou|descobriu|bolou|fez) (isso|essa|esse|a |o )",
                      r"quem foi que (inventou|criou|descobriu)",
                      r"como (foi que )?(inventaram|descobriram|chegaram nisso)",
                      r"hist[óo]ria (dessa|desta|desse|deste|da|do) (formula|conta|regra)",
                      r"por que (essa|esta) formula existe")),
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
