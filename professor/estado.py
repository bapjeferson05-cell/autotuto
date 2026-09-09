"""estado.py — o estado estruturado da aula.

Quando o aluno interrompe, o agente NÃO reconstrói a aula do zero. Ele mexe neste
estado: empilha um ramo, toca, desempilha, e continua do bloco onde parou.

    e = EstadoAula(aula)
    while (b := e.proximo()):
        tocar(b)                       # TTS + figura
        if aluno_interrompeu():
            gat = classificar(fala)    # "por_que" | "nao_entendi" | ...
            for rb in e.entra_ramo(gat):
                tocar(rb)
            e.sai_ramo()               # volta pra trilha principal
    print(e.resumo())
"""
from __future__ import annotations

from dataclasses import dataclass, field

from professor.esquema import Aula


@dataclass
class Trilha:
    blocos: list[dict]
    i: int = -1
    rotulo: str = "principal"

    def proximo(self) -> dict | None:
        self.i += 1
        return self.blocos[self.i] if self.i < len(self.blocos) else None

    @property
    def posicao(self) -> str:
        return f"{min(self.i + 1, len(self.blocos))}/{len(self.blocos)}"


@dataclass
class EstadoAula:
    aula: Aula
    dados: dict = field(default_factory=dict)
    _pilha: list[Trilha] = field(default_factory=list)
    figura_atual: dict | None = None
    calc_atual: dict | None = None
    historico: list[str] = field(default_factory=list)   # gatilhos dos ramos usados

    def __post_init__(self):
        self.dados = dict(self.aula.dados)
        self._pilha = [Trilha(self.aula.blocos, rotulo="principal")]

    # ------------------------------------------------------------------ navegação
    @property
    def trilha(self) -> Trilha:
        return self._pilha[-1]

    @property
    def na_principal(self) -> bool:
        return len(self._pilha) == 1

    def proximo(self) -> dict | None:
        """Próximo bloco da trilha do topo (a principal, ou o ramo atual).
        NÃO desce sozinho — quem drena um ramo é `drena_ramo()`."""
        b = self.trilha.proximo()
        if b is not None:
            self._registra(b)
        return b

    def entra_ramo(self, gatilho: str) -> list[dict]:
        """Empilha o ramo do gatilho e devolve seus blocos. Se o gatilho não
        existe, devolve [] e nada muda."""
        blocos = (self.aula.ramos or {}).get(gatilho)
        if not blocos:
            return []
        self.historico.append(gatilho)
        self._pilha.append(Trilha(list(blocos), rotulo=f"ramo:{gatilho}"))
        return list(blocos)

    def drena_ramo(self):
        """Gera o resto dos blocos do ramo do topo e depois desempilha. A trilha
        de baixo (onde o aluno interrompeu) fica intacta."""
        if self.na_principal:
            return
        while (b := self.trilha.proximo()) is not None:
            self._registra(b)
            yield b
        self._pilha.pop()

    def sai_ramo(self) -> None:
        if not self.na_principal:
            self._pilha.pop()

    # ------------------------------------------------------------------ interno
    def _registra(self, bloco: dict) -> None:
        if bloco.get("figura"):
            self.figura_atual = bloco["figura"]
        if bloco.get("calc"):
            self.calc_atual = bloco["calc"]
            for k, v in (bloco["calc"].get("params") or {}).items():
                self.dados.setdefault(k, v)

    # ------------------------------------------------------------------ leitura
    def resumo(self) -> str:
        dados = ", ".join(f"{k}={v}" for k, v in self.dados.items())
        fig = self.figura_atual.get("gerador") if self.figura_atual else "—"
        cam = " › ".join(t.rotulo for t in self._pilha)
        return (f"{self.aula.topico or self.aula.titulo} | {dados or 'sem dados'} | "
                f"figura: {fig} | {cam} ({self.trilha.posicao})"
                + (f" | ramos usados: {self.historico}" if self.historico else ""))
