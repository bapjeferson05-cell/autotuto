from dataclasses import dataclass, field
from autotuto.schema import Aula


@dataclass
class Trilha:
    """Uma trilha de blocos em uma aula, com índice de progresso."""
    blocos: list[dict]
    i: int = -1
    rotulo: str = "principal"

    def proximo(self) -> dict | None:
        """Avança o índice e retorna o próximo bloco, ou None se acabou."""
        self.i += 1
        if self.i < len(self.blocos):
            return self.blocos[self.i]
        return None

    @property
    def posicao(self) -> str:
        """Retorna a posição no formato 'atual/total'."""
        return f"{min(self.i + 1, len(self.blocos))}/{len(self.blocos)}"


@dataclass
class EstadoAula:
    """Máquina de estado para navegação em uma aula com ramos."""
    aula: Aula
    _pilha: list[Trilha] = field(default_factory=list)
    _historico: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Inicializa a pilha com a trilha principal."""
        if not self._pilha:
            self._pilha = [Trilha(self.aula.blocos, rotulo="principal")]

    def proximo(self) -> dict | None:
        """Retorna o próximo beat da trilha no topo da pilha."""
        return self.trilha.proximo()

    def entra_ramo(self, gatilho: str) -> list[dict]:
        """
        Entra em um ramo se ele existe.
        Empilha a trilha do ramo, registra o gatilho no histórico,
        e retorna a lista de blocos.
        Retorna [] se o ramo não existe.
        """
        if gatilho not in self.aula.ramos:
            return []

        blocos = self.aula.ramos[gatilho]
        self._pilha.append(Trilha(blocos, rotulo=f"ramo:{gatilho}"))
        self._historico.append(gatilho)
        return blocos

    def drena_ramo(self):
        """
        Generator que rende o resto dos beats da trilha no topo
        e depois desempilha. No-op se já está na trilha principal.
        """
        if self.na_principal:
            return
        trilha = self.trilha
        while True:
            beat = trilha.proximo()
            if beat is None:
                break
            yield beat
        # Desempilha após render todos
        self._pilha.pop()

    def sai_ramo(self) -> None:
        """Remove o ramo do topo se não estiver na trilha principal."""
        if not self.na_principal:
            self._pilha.pop()

    @property
    def na_principal(self) -> bool:
        """Verifica se está na trilha principal."""
        return len(self._pilha) == 1

    @property
    def trilha(self) -> Trilha:
        """Retorna a trilha no topo da pilha."""
        return self._pilha[-1]

    @property
    def historico(self) -> list[str]:
        """Retorna uma cópia da lista de gatilhos de ramos visitados."""
        return list(self._historico)

    def resumo(self) -> str:
        """
        Retorna um resumo de uma linha com:
        - titulo ou topico
        - dados
        - posição atual
        - histórico de gatilhos (se houver)
        """
        label = self.aula.topico or self.aula.titulo
        dados_str = f"dados={self.aula.dados}" if self.aula.dados else ""
        posicao = self.trilha.posicao
        historico_str = f"historico={self._historico}" if self._historico else ""

        parts = [label, dados_str, posicao, historico_str]
        return " ".join(p for p in parts if p)
