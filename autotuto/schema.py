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
        onde = f"bloco[{i}]"
        if not (b.get("diz") or b.get("figura") or b.get("calc")):
            erros.append(f"{onde}: vazio (precisa de diz, figura ou calc)")
        pg = b.get("pergunta")
        if pg is not None:
            if not isinstance(pg, dict):
                erros.append(f"{onde}.pergunta: tem que ser objeto")
                continue
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
    for nome, blocos in ramos.items():
        if not isinstance(blocos, list) or not blocos:
            erros.append(f"ramo '{nome}': lista não-vazia de beats")
    return erros
