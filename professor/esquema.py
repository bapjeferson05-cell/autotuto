"""esquema.py — fonte única da verdade: o catálogo de geradores + o formato do
plano que o LLM produz.

O LLM NÃO desenha e NÃO faz conta. Ele produz um PLANO (JSON):

    {
      "titulo": "Área do trapézio",
      "topico": "area_trapezio",
      "dados":  {"B": 18, "b": 10, "h": 10},
      "blocos": [
        {"diz": "Esse terreno é um trapézio...",
         "figura": {"gerador": "figura", "spec": {...}},
         "espera": "media"},
        {"diz": "A fórmula é...",
         "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 10}},
         "mostra_passos": true}
      ],
      "ramos": {
        "por_que_div_2": [ {...blocos...} ],
        "nao_entendi":   [ {...blocos...} ]
      }
    }

`ramos` são mini-sequências indexadas por gatilho. Quando o aluno interrompe, o
agente escolhe um ramo, toca, e o Player retoma do bloco onde parou.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from professor import calc
from professor.figuras import formas, primitivas, solidos

ESPERAS = ("curta", "media", "longa")


# ────────────────────────────────────────────────────────── declaração de params
@dataclass
class Param:
    tipo: str                       # "int" | "float" | "str" | "bool" | "dict" | "list"
    obrig: bool = True
    opcoes: tuple = ()              # enum de valores válidos
    faixa: tuple = ()              # (min, max) para números
    default: Any = None
    nota: str = ""

    def descreve(self) -> str:
        if self.opcoes:
            vs = " | ".join(f'"{o}"' for o in self.opcoes)
            base = vs
        elif self.faixa:
            base = f"{self.tipo} ({self.faixa[0]}..{self.faixa[1]})"
        else:
            base = self.tipo
        if not self.obrig:
            base += f"  (opcional, default {self.default!r})"
        if self.nota:
            base += f"  — {self.nota}"
        return base


@dataclass
class Gerador:
    nome: str
    familia: str                    # "figura" | "calc"
    fn: Callable
    params: dict[str, Param]
    resumo: str
    exemplo: dict = field(default_factory=dict)
    descritor: Callable | None = None   # params -> dict de propriedades matemáticas


# ────────────────────────────────────────────────────────── FIGURAS
_TIPOS_TRI = ("equilatero", "isosceles", "escaleno", "retangulo", "acutangulo", "obtusangulo")
_TIPOS_QUAD = ("quadrado", "retangulo", "losango", "paralelogramo", "trapezio_isosceles",
               "trapezio_retangulo", "trapezio_escaleno", "deltoide")
_NOMES_CURVA = ("elipse", "parabola", "hiperbole", "cardioide", "lemniscata", "espiral", "cassini")
_NOMES_PARTE = ("circulo", "circunferencia", "semicirculo", "setor", "segmento", "coroa")
_NOMES_SOLIDO = ("tetraedro", "cubo", "octaedro", "dodecaedro", "icosaedro",
                 "esfera", "hemisferio", "cilindro", "cone", "tronco_cone", "toro",
                 "elipsoide", "paraboloide", "hiperboloide", "paralelepipedo",
                 "prisma", "piramide", "tronco_piramide", "antiprisma", "bipiramide",
                 "tetraedro_truncado", "cuboctaedro", "cubo_truncado",
                 "octaedro_truncado", "icosidodecaedro", "icosaedro_truncado")

FIGURAS: dict[str, Gerador] = {
    "figura": Gerador(
        "figura", "figura", primitivas.figura,
        {"spec": Param("dict", nota="pontos/segmentos/poligonos/circulos/angulos/marcas/cotas/rotulos")},
        "composição livre de primitivas — a figura geométrica genérica",
        {"gerador": "figura", "spec": {
            "pontos": {"A": [0, 0], "B": [18, 0], "C": [14, 6], "D": [4, 6]},
            "poligonos": [{"vs": ["A", "B", "C", "D"], "preenche": True}],
            "cotas": [{"de": "A", "para": "B", "texto": "18", "lado": -1}]}},
    ),
    "funcao": Gerador(
        "funcao", "figura", primitivas.funcao,
        {"expr": Param("str", nota="ex.: 'x**2 - 2*x - 3', 'sin(x)'"),
         "x0": Param("float", False, default=-5.0), "x1": Param("float", False, default=5.0),
         "raiz": Param("bool", False, default=False), "vertice": Param("bool", False, default=False),
         "area": Param("list", False, nota="[a, b] pinta a área sob a curva"),
         "ponto": Param("float", False), "titulo": Param("str", False)},
        "gráfico de y = f(x)",
        {"gerador": "funcao", "params": {"expr": "x**2 - 2*x - 3", "raiz": True, "vertice": True}},
    ),
    "reta_numerica": Gerador(
        "reta_numerica", "figura", primitivas.reta_numerica,
        {"x0": Param("int", False, default=-5), "x1": Param("int", False, default=5),
         "pontos": Param("list", False, nota="[{x, rotulo}]"),
         "intervalo": Param("dict", False, nota="{de, para, fechado_esq, fechado_dir}")},
        "reta numérica com pontos e intervalos",
        {"gerador": "reta_numerica", "params": {"x0": -5, "x1": 5,
                                                "intervalo": {"de": -1, "para": 3, "fechado_dir": False}}},
    ),
    "triangulo": Gerador(
        "triangulo", "figura", formas.triangulo,
        {"tipo": Param("str", opcoes=_TIPOS_TRI)},
        "triângulo por classificação (lados/ângulos)",
        {"gerador": "triangulo", "params": {"tipo": "retangulo"}},
    ),
    "quadrilatero": Gerador(
        "quadrilatero", "figura", formas.quadrilatero,
        {"tipo": Param("str", opcoes=_TIPOS_QUAD)},
        "quadrilátero por classificação",
        {"gerador": "quadrilatero", "params": {"tipo": "trapezio_isosceles"}},
    ),
    "poligono_regular": Gerador(
        "poligono_regular", "figura", formas.poligono_regular,
        {"n": Param("int", faixa=(3, 1_000_000)),
         "r": Param("float", False, default=4.0)},
        "polígono regular de n lados (pentágono … megágono)",
        {"gerador": "poligono_regular", "params": {"n": 6}},
    ),
    "estrela": Gerador(
        "estrela", "figura", formas.estrela,
        {"n": Param("int", faixa=(5, 24)), "k": Param("int", faixa=(2, 11)),
         "r": Param("float", False, default=4.0)},
        "polígono estrelado {n/k} (pentagrama {5/2}, hexagrama {6/2}, …)",
        {"gerador": "estrela", "params": {"n": 5, "k": 2}},
    ),
    "curva": Gerador(
        "curva", "figura", formas.curva,
        {"nome": Param("str", opcoes=_NOMES_CURVA)},
        "curva por equação (cônicas e clássicas)",
        {"gerador": "curva", "params": {"nome": "elipse"}},
    ),
    "parte_circulo": Gerador(
        "parte_circulo", "figura", formas.parte_circulo,
        {"nome": Param("str", opcoes=_NOMES_PARTE),
         "r": Param("float", False, default=4.0),
         "ang": Param("float", False, default=75.0, nota="ângulo do setor/segmento em graus")},
        "círculo e seus recortes (setor, segmento, coroa, semicírculo)",
        {"gerador": "parte_circulo", "params": {"nome": "setor", "ang": 60}},
    ),
    "solido": Gerador(
        "solido", "figura", solidos.solido,
        {"nome": Param("str", opcoes=_NOMES_SOLIDO),
         "n": Param("int", False, faixa=(3, 12), nota="nº de lados (prisma/pirâmide/…)"),
         "obliquo": Param("bool", False, default=False)},
        "sólido 3D em wireframe (platônicos, corpos redondos, prismas, pirâmides, arquimedianos)",
        {"gerador": "solido", "params": {"nome": "prisma", "n": 6}},
    ),
}


# ────────────────────────────────────────────────────────── CÁLCULOS
def _p(*names, tipo="float"):
    return {n: Param(tipo) for n in names}


CALCULOS: dict[str, Gerador] = {
    "area_trapezio": Gerador("area_trapezio", "calc", calc.area_trapezio,
                             _p("B", "b", "h"), "área do trapézio",
                             {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 10}}),
    "area_triangulo": Gerador("area_triangulo", "calc", calc.area_triangulo,
                              _p("base", "altura"), "área do triângulo",
                              {"gerador": "area_triangulo", "params": {"base": 8, "altura": 5}}),
    "area_circulo": Gerador("area_circulo", "calc", calc.area_circulo,
                            _p("r"), "área do círculo",
                            {"gerador": "area_circulo", "params": {"r": 4}}),
    "area_retangulo": Gerador("area_retangulo", "calc", calc.area_retangulo,
                              _p("base", "altura"), "área do retângulo",
                              {"gerador": "area_retangulo", "params": {"base": 6, "altura": 4}}),
    "pitagoras": Gerador("pitagoras", "calc", calc.pitagoras,
                         {"a": Param("float", False), "b": Param("float", False),
                          "c": Param("float", False, nota="hipotenusa; passe 2 dos 3")},
                         "teorema de Pitágoras (passe 2 dos 3 lados)",
                         {"gerador": "pitagoras", "params": {"a": 3, "b": 4}}),
    "eq_primeiro_grau": Gerador("eq_primeiro_grau", "calc", calc.eq_primeiro_grau,
                                _p("a", "b"), "resolve a·x + b = 0",
                                {"gerador": "eq_primeiro_grau", "params": {"a": 2, "b": -10}}),
    "bhaskara": Gerador("bhaskara", "calc", calc.bhaskara,
                        _p("a", "b", "c"), "resolve a·x² + b·x + c = 0",
                        {"gerador": "bhaskara", "params": {"a": 1, "b": -2, "c": -3}}),
    "porcentagem": Gerador("porcentagem", "calc", calc.porcentagem,
                           {"parte": Param("float", False), "todo": Param("float", False),
                            "pct": Param("float", False)},
                           "porcentagem (passe 2 dos 3: parte, todo, pct)",
                           {"gerador": "porcentagem", "params": {"todo": 240, "pct": 15}}),
    "regra_de_tres": Gerador("regra_de_tres", "calc", calc.regra_de_tres,
                             _p("a", "b", "c"), "regra de três: a/b = c/x",
                             {"gerador": "regra_de_tres", "params": {"a": 3, "b": 12, "c": 5}}),
    "mdc": Gerador("mdc", "calc", calc.mdc, _p("a", "b", tipo="int"), "máximo divisor comum",
                   {"gerador": "mdc", "params": {"a": 12, "b": 18}}),
    "mmc": Gerador("mmc", "calc", calc.mmc, _p("a", "b", tipo="int"), "mínimo múltiplo comum",
                   {"gerador": "mmc", "params": {"a": 4, "b": 6}}),
}

GERADORES: dict[str, Gerador] = {**FIGURAS, **CALCULOS}


# ────────────────────────────────────────────────────────── dataclasses do plano
@dataclass
class Aula:
    titulo: str
    blocos: list[dict]
    ramos: dict[str, list[dict]] = field(default_factory=dict)
    topico: str = ""
    dados: dict = field(default_factory=dict)

    @classmethod
    def de_json(cls, obj: dict) -> "Aula":
        return cls(
            titulo=obj.get("titulo", "Aula"),
            blocos=obj.get("blocos", []),
            ramos=obj.get("ramos", {}),
            topico=obj.get("topico", ""),
            dados=obj.get("dados", {}),
        )

    def para_json(self) -> dict:
        return {"titulo": self.titulo, "topico": self.topico, "dados": self.dados,
                "blocos": self.blocos, "ramos": self.ramos}


# ────────────────────────────────────────────────────────── catálogo → prompt
def catalogo_para_prompt() -> str:
    linhas = ["FIGURAS  (bloco[\"figura\"] = {\"gerador\": <nome>, \"params\": {...}}  "
              "— exceto 'figura', que usa {\"gerador\": \"figura\", \"spec\": {...}}):"]
    for g in FIGURAS.values():
        linhas.append(f"  • {g.nome} — {g.resumo}")
        for pn, pv in g.params.items():
            linhas.append(f"      {pn}: {pv.descreve()}")
    linhas.append("")
    linhas.append("CÁLCULOS  (bloco[\"calc\"] = {\"gerador\": <nome>, \"params\": {...}}):")
    for g in CALCULOS.values():
        ps = ", ".join(f"{pn}: {pv.tipo}" for pn, pv in g.params.items())
        linhas.append(f"  • {g.nome} — {g.resumo}   [{ps}]")
    return "\n".join(linhas)
