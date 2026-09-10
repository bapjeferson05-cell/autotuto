"""validador.py — o portão entre o LLM e os geradores.

Dois níveis:
  1. ESTRUTURAL — o gerador existe? os params batem com a assinatura (nome, tipo,
     faixa, enum)? o bloco tem 'diz'?
  2. MATEMÁTICO — a figura/conta que vai sair está matematicamente coerente com o
     que foi pedido? (nº de lados, ângulo reto onde tem que ter, área > 0, passos
     terminam em '='...). Calcula as propriedades de forma INDEPENDENTE do gerador
     — se o gerador tiver bug, o validador acusa.

    rel = valida_aula(aula)
    if rel.ok: ...
    else: print(rel.problemas)   # lista de strings, prontas pra devolver ao LLM
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from professor import calc as _calc
from professor.esquema import CALCULOS, ESPERAS, FIGURAS, GERADORES, Aula, Param
from professor.figuras import formas


@dataclass
class Relatorio:
    problemas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problemas

    def __iadd__(self, outro: "Relatorio") -> "Relatorio":
        self.problemas += outro.problemas
        self.avisos += outro.avisos
        return self


# ─────────────────────────────────────────────── coerção / checagem de params
def _coage(valor, p: Param):
    """Devolve (valor_coagido, erro|None)."""
    try:
        if p.tipo == "int":
            v = int(valor)
        elif p.tipo == "float":
            v = float(valor)
        elif p.tipo == "bool":
            v = valor if isinstance(valor, bool) else str(valor).lower() in ("true", "1", "sim")
        elif p.tipo == "str":
            v = str(valor)
        elif p.tipo in ("dict", "list"):
            if p.tipo == "dict" and not isinstance(valor, dict):
                return None, f"esperava objeto, veio {type(valor).__name__}"
            if p.tipo == "list" and not isinstance(valor, (list, tuple)):
                return None, f"esperava lista, veio {type(valor).__name__}"
            v = valor
        else:
            v = valor
    except (TypeError, ValueError):
        return None, f"não converte pra {p.tipo}: {valor!r}"
    if p.opcoes and v not in p.opcoes:
        return None, f"valor {v!r} fora do conjunto {list(p.opcoes)}"
    if p.faixa and isinstance(v, (int, float)) and not (p.faixa[0] <= v <= p.faixa[1]):
        return None, f"{v} fora da faixa {p.faixa[0]}..{p.faixa[1]}"
    return v, None


def _valida_chamada(spec: dict, familia: str) -> tuple[dict, list[str]]:
    """spec = {"gerador": ..., "params"/"spec": {...}}. Devolve (params_coagidos, erros)."""
    erros: list[str] = []
    nome = spec.get("gerador")
    if nome not in GERADORES:
        return {}, [f"gerador '{nome}' não existe. Use um de: {sorted(GERADORES)}"]
    g = GERADORES[nome]
    if g.familia != familia:
        erros.append(f"'{nome}' é da família '{g.familia}', não cabe em bloco['{familia}']")
    brutos = spec.get("spec") if nome == "figura" else spec.get("params", {})
    brutos = brutos or {}
    if nome == "figura":
        return {"spec": brutos}, erros + _valida_spec_figura(brutos)
    out = {}
    for pn, p in g.params.items():
        if pn not in brutos:
            if p.obrig:
                erros.append(f"{nome}: falta o parâmetro obrigatório '{pn}' ({p.descreve()})")
            elif p.default is not None:
                out[pn] = p.default
            continue
        v, e = _coage(brutos[pn], p)
        if e:
            erros.append(f"{nome}.{pn}: {e}")
        else:
            out[pn] = v
    extras = set(brutos) - set(g.params)
    if extras:
        erros.append(f"{nome}: parâmetros desconhecidos {sorted(extras)}")
    return out, erros


_CHAVES_FIGURA = {"pontos", "poligonos", "segmentos", "circulos", "angulos", "marcas",
                  "cotas", "rotulos", "mostrar_pontos", "nomear_pontos"}
_LISTAS_FIGURA = ("poligonos", "segmentos", "circulos", "angulos", "marcas", "cotas", "rotulos")


def _valida_spec_figura(spec: dict) -> list[str]:
    e: list[str] = []
    if not isinstance(spec, dict):
        return ["figura.spec tem que ser um objeto com 'pontos' e elementos "
                "(poligonos/segmentos/circulos/...)"]
    desconhecidas = set(spec) - _CHAVES_FIGURA
    if desconhecidas:
        dica = {"circulo": "circulos", "poligono": "poligonos", "segmento": "segmentos",
                "angulo": "angulos", "cota": "cotas", "rotulo": "rotulos", "ponto": "pontos"}
        sug = "; ".join(f"'{k}'→'{dica[k]}'" for k in desconhecidas if k in dica)
        e.append(f"figura.spec: chaves desconhecidas {sorted(desconhecidas)}"
                 + (f" (talvez {sug})" if sug else "")
                 + f". Válidas: {sorted(_CHAVES_FIGURA)}")
    pts = spec.get("pontos", {})
    if not isinstance(pts, dict):
        e.append("figura.spec.pontos tem que ser um objeto {nome: [x, y]}")
        pts = {}
    for nome, xy in pts.items():
        if not (isinstance(xy, (list, tuple)) and len(xy) == 2
                and all(isinstance(c, (int, float)) for c in xy)):
            e.append(f"ponto '{nome}' tem que ser [x, y] numérico")
    for chave in _LISTAS_FIGURA:
        if chave in spec and not isinstance(spec[chave], list):
            e.append(f"figura.spec.{chave} tem que ser uma lista")
    tem_elemento = bool(pts) or any(isinstance(spec.get(c), list) and spec[c] for c in _LISTAS_FIGURA)
    if not tem_elemento:
        e.append("figura.spec não desenha nada — precisa de 'pontos' e/ou "
                 "'poligonos'/'segmentos'/'circulos'. Para uma forma simples, use antes "
                 "um gerador específico (parte_circulo, poligono_regular, triangulo, curva…).")
    for pg in spec.get("poligonos", []) if isinstance(spec.get("poligonos"), list) else []:
        faltando = [v for v in pg.get("vs", []) if not isinstance(v, str) or v not in pts]
        if faltando:
            e.append(f"polígono.vs deve ser nomes de pontos definidos; problema em: {faltando}")
    for s in spec.get("segmentos", []) if isinstance(spec.get("segmentos"), list) else []:
        for lado in ("de", "para"):
            if s.get(lado) not in pts:
                e.append(f"segmento.{lado}='{s.get(lado)}' não é um ponto definido")
    for c in spec.get("circulos", []) if isinstance(spec.get("circulos"), list) else []:
        if "r" not in c:
            e.append("circulo precisa de 'r'")
        if "centro" not in c:
            e.append("circulo precisa de 'centro' (nome de ponto ou [x, y])")
        elif isinstance(c["centro"], str) and c["centro"] not in pts:
            e.append(f"circulo.centro='{c['centro']}' não é um ponto definido")
    return e


# ─────────────────────────────────────────────── nível 2: matemática
def _ang(a, b, c) -> float:
    """ângulo em b, em graus."""
    u, v = np.array(a) - np.array(b), np.array(c) - np.array(b)
    cosv = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12)
    return math.degrees(math.acos(max(-1, min(1, cosv))))


def _mat_figura(nome: str, params: dict) -> list[str]:
    """Recalcula as propriedades e confere com o que o nome promete."""
    p: list[str] = []
    if nome == "poligono_regular":
        n = int(params["n"])
        m = min(n, 4000)
        ang = math.pi / 2 + np.linspace(0, 2 * math.pi, m, endpoint=False)
        V = np.c_[np.cos(ang), np.sin(ang)]
        raios = np.linalg.norm(V, axis=1)
        lados = np.linalg.norm(np.diff(np.vstack([V, V[0]]), axis=0), axis=1)
        if raios.std() > 1e-6:
            p.append("poligono_regular: vértices não equidistantes do centro")
        if lados.std() / (lados.mean() + 1e-12) > 1e-3:
            p.append("poligono_regular: lados desiguais — não é regular")
    elif nome == "estrela":
        n, k = int(params["n"]), int(params["k"])
        if not (2 <= k < n / 2 or math.gcd(n, k) > 1):
            p.append(f"estrela {{{n}/{k}}}: k tem que estar entre 2 e n/2 (ou compor um composto)")
    elif nome == "triangulo":
        tipo = params["tipo"]
        A, B, C = (np.array(formas._TRI[tipo][v], float) for v in ("A", "B", "C"))
        angs = sorted([_ang(B, A, C), _ang(A, B, C), _ang(A, C, B)])
        lados = sorted([np.linalg.norm(B - A), np.linalg.norm(C - B), np.linalg.norm(A - C)])
        reto = any(abs(a - 90) < 1.0 for a in angs)
        if tipo == "retangulo" and not reto:
            p.append("triangulo retangulo: nenhum ângulo é 90°")
        if tipo == "obtusangulo" and angs[-1] <= 90 + 1e-6:
            p.append("triangulo obtusangulo: maior ângulo não passa de 90°")
        if tipo == "acutangulo" and angs[-1] >= 90:
            p.append("triangulo acutangulo: tem ângulo ≥ 90°")
        if tipo == "equilatero" and (lados[-1] - lados[0]) / lados[-1] > 0.02:
            p.append("triangulo equilatero: lados diferentes")
        if tipo == "isosceles" and abs(lados[1] - lados[2]) / lados[2] > 0.02 \
                and abs(lados[0] - lados[1]) / lados[1] > 0.02:
            p.append("triangulo isosceles: não tem dois lados iguais")
        if tipo == "escaleno" and (abs(lados[0] - lados[1]) < 1e-3 or abs(lados[1] - lados[2]) < 1e-3):
            p.append("triangulo escaleno: tem lados iguais")
    elif nome == "quadrilatero":
        tipo = params["tipo"]
        P = {k: np.array(v, float) for k, v in formas._quad_pts(tipo).items()}
        A, B, C, D = P["A"], P["B"], P["C"], P["D"]
        def par(u, v, w, x):
            d1, d2 = v - u, x - w
            cruz = abs(d1[0] * d2[1] - d1[1] * d2[0])
            return cruz < 0.06 * np.linalg.norm(d1) * np.linalg.norm(d2)
        ab_dc = par(A, B, D, C)
        ad_bc = par(A, D, B, C)
        if tipo.startswith("trapezio") and not (ab_dc or ad_bc):
            p.append(f"{tipo}: nenhum par de lados é paralelo")
        if tipo in ("quadrado", "retangulo", "paralelogramo", "losango") and not (ab_dc and ad_bc):
            p.append(f"{tipo}: precisa dos dois pares de lados paralelos")
        if tipo in ("quadrado", "retangulo") and abs(_ang(A, B, C) - 90) > 1.0:
            p.append(f"{tipo}: ângulo em B não é reto")
        if tipo in ("quadrado", "losango"):
            L = [np.linalg.norm(B - A), np.linalg.norm(C - B), np.linalg.norm(D - C), np.linalg.norm(A - D)]
            if (max(L) - min(L)) / max(L) > 0.02:
                p.append(f"{tipo}: lados desiguais")
    elif nome == "funcao":
        env = {**primitivas_env(), "x": np.linspace(params.get("x0", -5), params.get("x1", 5), 50)}
        try:
            y = eval(params["expr"], {"__builtins__": {}}, env)  # noqa: S307
            if not np.isfinite(np.asarray(y, float)).any():
                p.append(f"funcao: '{params['expr']}' não dá nenhum valor finito no intervalo")
        except Exception as e:  # noqa: BLE001
            p.append(f"funcao: expr inválida — {e}")
    return p


def primitivas_env():
    return {"sin": np.sin, "cos": np.cos, "tan": np.tan, "sqrt": np.sqrt,
            "exp": np.exp, "log": np.log, "pi": np.pi, "abs": np.abs, "e": math.e}


_NAO_NEGATIVOS = {"area_trapezio", "area_triangulo", "area_circulo", "area_retangulo",
                  "mmc", "mdc", "velocidade_media", "juros_simples",
                  "comprimento_circunferencia", "perimetro_poligono_regular"}


def _mat_calc(nome: str, params: dict) -> list[str]:
    p: list[str] = []
    g = CALCULOS[nome]
    try:
        r = g.fn(**params)
    except Exception as e:  # noqa: BLE001
        return [f"{nome}: estourou ao calcular — {e}"]
    if not r.passos or not any("=" in s for s in r.passos):
        p.append(f"{nome}: os passos não mostram nenhuma igualdade")
    v = r.valor
    if isinstance(v, (int, float)):
        if not math.isfinite(v):
            p.append(f"{nome}: resultado não finito")
        if nome in _NAO_NEGATIVOS and v < 0:
            p.append(f"{nome}: resultado negativo ({v}) não faz sentido")
    if nome == "pitagoras" and sum(x is not None for x in (params.get("a"), params.get("b"), params.get("c"))) != 2:
        p.append("pitagoras: passe exatamente 2 dos 3 lados")
    return p


# ─────────────────────────────────────────────── entrada
def valida_bloco(bloco: dict, *, onde: str = "bloco", ramos_validos: set | None = None) -> Relatorio:
    rel = Relatorio()
    if not isinstance(bloco, dict):
        rel.problemas.append(f"{onde}: não é um objeto")
        return rel
    if not str(bloco.get("diz", "")).strip():
        rel.problemas.append(f"{onde}: falta 'diz' (o texto que o professor fala)")
    esp = bloco.get("espera")
    if esp is not None and esp not in ESPERAS:
        rel.problemas.append(f"{onde}: espera='{esp}' inválida (use {list(ESPERAS)} ou omita)")

    if "pergunta" in bloco and bloco["pergunta"]:
        pg = bloco["pergunta"]
        if not isinstance(pg, dict):
            rel.problemas.append(f"{onde}.pergunta: tem que ser um objeto {{escuta_s, senao}}")
        else:
            senao = pg.get("senao")
            if not senao:
                rel.problemas.append(f"{onde}.pergunta: falta 'senao' (ramo se o aluno não responder)")
            elif ramos_validos is not None and senao not in ramos_validos:
                rel.problemas.append(f"{onde}.pergunta.senao='{senao}' não é um ramo da aula "
                                     f"({sorted(ramos_validos)})")
            es = pg.get("escuta_s", 12)
            if not isinstance(es, (int, float)) or not (3 <= es <= 60):
                rel.problemas.append(f"{onde}.pergunta.escuta_s deve ser um número de 3 a 60")

    if "figura" in bloco and bloco["figura"]:
        params, erros = _valida_chamada(bloco["figura"], "figura")
        rel.problemas += [f"{onde}.figura: {e}" for e in erros]
        if not erros and bloco["figura"].get("gerador") != "figura":
            rel.problemas += [f"{onde}.figura: {e}"
                              for e in _mat_figura(bloco["figura"]["gerador"], params)]
    if "calc" in bloco and bloco["calc"]:
        params, erros = _valida_chamada(bloco["calc"], "calc")
        rel.problemas += [f"{onde}.calc: {e}" for e in erros]
        if not erros:
            rel.problemas += [f"{onde}.calc: {e}"
                              for e in _mat_calc(bloco["calc"]["gerador"], params)]
    if not bloco.get("figura") and not bloco.get("calc") and not bloco.get("diz"):
        rel.problemas.append(f"{onde}: bloco vazio")
    return rel


def valida_aula(aula: Aula | dict) -> Relatorio:
    if isinstance(aula, dict):
        aula = Aula.de_json(aula)
    rel = Relatorio()
    if not str(aula.titulo).strip():
        rel.problemas.append("aula: falta 'titulo'")
    if not aula.blocos:
        rel.problemas.append("aula: 'blocos' está vazio")
    rv = set(aula.ramos or {})
    for i, b in enumerate(aula.blocos):
        rel += valida_bloco(b, onde=f"blocos[{i}]", ramos_validos=rv)
    for gatilho, blist in (aula.ramos or {}).items():
        if not isinstance(blist, list) or not blist:
            rel.problemas.append(f"ramos['{gatilho}']: tem que ser uma lista não vazia de blocos")
            continue
        for i, b in enumerate(blist):
            rel += valida_bloco(b, onde=f"ramos['{gatilho}'][{i}]", ramos_validos=rv)
    return rel
