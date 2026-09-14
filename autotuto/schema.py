from __future__ import annotations
from dataclasses import dataclass, field

_ESPERAS = {"curta", "media", "longa"}

@dataclass
class Aula:
    titulo: str
    blocos: list[dict]
    ramos: dict[str, list[dict]] = field(default_factory=dict)
    topico: str = ""
    dados: dict = field(default_factory=dict)

    @classmethod
    def de_json(cls, o: dict) -> "Aula":
        return cls(o.get("titulo", "Aula"), o.get("blocos", []), o.get("ramos", {}),
                   o.get("topico", ""), o.get("dados", {}))

    def para_json(self) -> dict:
        return {"titulo": self.titulo, "topico": self.topico, "dados": self.dados,
                "blocos": self.blocos, "ramos": self.ramos}


def _valida_beat(b: dict, onde: str, ramos: dict) -> list[str]:
    """Checagem de forma de UM beat. Usada tanto pros `blocos` de topo quanto
    pros beats de dentro de cada `ramo` — antes só os de topo passavam por
    aqui, e um `figura`/`calc` malformado num ramo só estourava (AttributeError)
    lá na frente, no `validador.checar_matematica` (bug do code-review)."""
    erros: list[str] = []
    # achado ao vivo 2026-09-13: uma aula do LLM pode mandar um item de
    # `blocos`/ramo como STRING CRUA em vez de objeto — sem este guarda,
    # `b.get(...)` estoura AttributeError aqui dentro, derrubando o thread do
    # planejador (e, sem try/except lá em cima, o processo inteiro do demo).
    # Mesma classe de bug do F7 (figura/calc crus), um nível acima: o BEAT
    # inteiro, não só um campo dele.
    if not isinstance(b, dict):
        erros.append(f"{onde}: precisa ser objeto (beat), veio {type(b).__name__}")
        return erros
    if not (b.get("diz") or b.get("figura") or b.get("calc")):
        erros.append(f"{onde}: vazio (precisa de diz, figura ou calc)")
    # F7: sem estes checks, uma `figura`/`calc` como string crua passa aqui e
    # só estoura lá no tocador (TypeError). Trava a forma no schema.
    if "figura" in b:
        fig = b["figura"]
        if not isinstance(fig, dict):
            erros.append(f"{onde}.figura: tem que ser objeto")
        elif not isinstance(fig.get("gerador"), str):
            erros.append(f"{onde}.figura.gerador: falta ou não é texto")
        elif fig["gerador"] == "figura":
            if fig.get("spec") is not None and not isinstance(fig["spec"], dict):
                erros.append(f"{onde}.figura.spec: objeto ou omita")
        elif fig.get("params") is not None and not isinstance(fig["params"], dict):
            erros.append(f"{onde}.figura.params: objeto ou omita")
    if "calc" in b:
        cl = b["calc"]
        if not isinstance(cl, dict):
            erros.append(f"{onde}.calc: tem que ser objeto")
        elif not isinstance(cl.get("gerador"), str):
            erros.append(f"{onde}.calc.gerador: falta ou não é texto")
        elif cl.get("params") is not None and not isinstance(cl["params"], dict):
            erros.append(f"{onde}.calc.params: objeto ou omita")
    pg = b.get("pergunta")
    if pg is not None:
        if not isinstance(pg, dict):
            erros.append(f"{onde}.pergunta: tem que ser objeto")
            return erros
        if not pg.get("senao"):
            erros.append(f"{onde}.pergunta: falta 'senao'")
        elif pg["senao"] not in ramos:
            erros.append(f"{onde}.pergunta.senao='{pg['senao']}' não é um ramo")
        es = pg.get("escuta_s", 12)
        if not isinstance(es, (int, float)) or not (3 <= es <= 60):
            erros.append(f"{onde}.pergunta.escuta_s: 3 a 60")
        ac = pg.get("acerta")
        if ac is not None and (not isinstance(ac, list) or not all(isinstance(x, str) for x in ac)):
            erros.append(f"{onde}.pergunta.acerta: lista de textos ou omita")
        cf = pg.get("confirma")
        if cf is not None and not isinstance(cf, str):
            erros.append(f"{onde}.pergunta.confirma: texto ou omita")
    esp = b.get("espera")
    if esp is not None and esp not in _ESPERAS:
        erros.append(f"{onde}.espera: {sorted(_ESPERAS)} ou omita")
    return erros


def validar_estrutura(o: dict) -> list[str]:
    erros: list[str] = []
    if not isinstance(o.get("blocos"), list) or not o["blocos"]:
        erros.append("aula sem 'blocos'")
        return erros
    ramos = o.get("ramos", {})
    if not isinstance(ramos, dict):
        erros.append("'ramos' tem que ser um objeto")
        ramos = {}
    for i, b in enumerate(o["blocos"]):
        erros += _valida_beat(b, f"bloco[{i}]", ramos)
    for nome, blocos in ramos.items():
        if not isinstance(blocos, list) or not blocos:
            erros.append(f"ramo '{nome}': lista não-vazia de beats")
            continue
        for i, b in enumerate(blocos):
            erros += _valida_beat(b, f"ramo['{nome}'][{i}]", ramos)
    return erros


# ────────────────────────────────── esquema JSON pro constrained decoding
# O ollama aceita um JSON Schema em `format` desde a 0.3.0 (llama.cpp: GBNF).
# Com ele o decoder é OBRIGADO a respeitar a forma — em vez de a gente pedir
# JSON, receber torto e mandar corrigir num retry.
#
# DE PROPÓSITO RASO. Levantamento de 2026 sobre geração declarativa por LLM
# relata que modelo quantizado pequeno "às vezes retorna arrays vazios em
# schemas aninhados 3+ níveis". Nossa Aula vai a 5 (blocos → beat → figura →
# spec → pontos). Então aqui a gente trava só o que quebrava de verdade — que
# `blocos` é lista, que beat é objeto, que `senao` é texto — e deixa `spec` e
# `params` como objeto livre. Travar fundo demais é trocar um erro por outro.
#
# O schema do `format` NÃO é injetado no prompt: o modelo não o enxerga. Então
# ele não substitui a descrição da estrutura em `planejador._SISTEMA` — soma.
_BEAT = {
    "type": "object",
    "properties": {
        "diz": {"type": "string"},
        "espera": {"type": "string", "enum": sorted(x for x in _ESPERAS if x)},
        "mostra_passos": {"type": "boolean"},
        "diz_passos": {"type": "array", "items": {"type": "string"}},
        "figura": {
            "type": "object",
            "properties": {"gerador": {"type": "string"},
                           "spec": {"type": "object"},      # livre: é fundo demais
                           "params": {"type": "object"}},
            "required": ["gerador"],
        },
        "calc": {
            "type": "object",
            "properties": {"gerador": {"type": "string"},
                           "params": {"type": "object"}},
            "required": ["gerador"],
        },
        "pergunta": {
            "type": "object",
            "properties": {
                "escuta_s": {"type": "integer", "minimum": 3, "maximum": 60},
                "senao": {"type": "string"},
                "acerta": {"type": "array", "items": {"type": "string"}},
                "confirma": {"type": "string"},
            },
            "required": ["senao"],
        },
    },
}


def esquema_json() -> dict:
    """JSON Schema da Aula, raso, pra `format` do ollama / GBNF."""
    import copy
    return {
        "type": "object",
        "properties": {
            "titulo": {"type": "string"},
            "topico": {"type": "string"},
            "dados": {"type": "object"},
            "blocos": {"type": "array", "items": copy.deepcopy(_BEAT), "minItems": 1},
            "ramos": {"type": "object",
                      "additionalProperties": {"type": "array",
                                               "items": copy.deepcopy(_BEAT),
                                               "minItems": 1}},
        },
        "required": ["titulo", "blocos"],
    }
