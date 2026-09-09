"""aula.py — como o modelo e a renderização conversam.

A resposta pra "como eles se falam": o professor (LLM) NÃO desenha. Ele escreve
uma LISTA DE BEATS. Cada beat = uma coisa pra falar + (opcional) uma figura pra
desenhar. O player executa: fala o texto no TTS enquanto a figura aparece, espera
acabar (ou o aluno interromper), próximo beat.

    beat = {
      "diz":    "Esse terreno é um trapézio...",      # vai pro TTS
      "lousa":  {"fn": "trapezio", "B": 18, "b": 10}, # chama professor.figuras.lousa.trapezio(...)
      "espera": "curta" | "media" | "longa",          # pausa depois de falar (deixa o aluno pensar)
    }

Uma AULA é uma lista de beats + RAMOS: mini-listas de beats indexadas por gatilho
("por_que_div_2", "e_triangulo", "nao_entendi"). Quando o aluno interrompe, o
agente escolhe um ramo, o player toca, e depois RETOMA do beat onde parou.

O LLM produz exatamente essa estrutura (JSON). Nada de "desenhar" solto no texto.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from professor.figuras import lousa

_ESPERA = {"curta": 0.4, "media": 1.0, "longa": 2.0, None: 0.6}


@dataclass
class Aula:
    titulo: str
    beats: list[dict]
    ramos: dict[str, list[dict]] = field(default_factory=dict)

    @classmethod
    def de_json(cls, obj: dict) -> "Aula":
        return cls(obj["titulo"], obj["beats"], obj.get("ramos", {}))


class Player:
    """Executa uma aula. `falar` e `desenhar` são injetados — no MVP são print +
    salvar PNG; no produto viram Piper + a tela."""

    def __init__(self, falar=None, desenhar=None, out_dir="out/aula"):
        self.falar = falar or self._falar_stub
        self.desenhar = desenhar or self._desenhar_stub
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self._n = 0

    def _falar_stub(self, txt: str) -> None:
        print(f"  🔊 {txt}")

    def _desenhar_stub(self, png: bytes, rotulo: str) -> None:
        self._n += 1
        p = self.out / f"{self._n:02d}_{rotulo}.png"
        p.write_bytes(png)
        print(f"  🖼  {p.name}")

    def _render(self, spec: dict) -> None:
        fn = lousa.CATALOGO.get(spec["fn"])
        if fn is None:
            print(f"  ⚠  figura desconhecida: {spec['fn']}")
            return
        params = {k: v for k, v in spec.items() if k != "fn"}
        self.desenhar(fn(**params), spec["fn"])

    def toca_beats(self, beats: list[dict], *, interrompivel=True) -> str | None:
        """Toca uma sequência. Retorna o gatilho da interrupção, ou None se acabou."""
        for i, b in enumerate(beats):
            if b.get("lousa"):
                self._render(b["lousa"])
            if b.get("diz"):
                gatilho = self.falar(b["diz"])   # o stub retorna None; o real pode
                if interrompivel and gatilho:     # devolver o gatilho do barge-in
                    return gatilho
            time.sleep(_ESPERA[b.get("espera")] if _ESPERA.get(b.get("espera")) else 0.6)
        return None

    def toca(self, aula: Aula) -> None:
        print(f"\n═══ {aula.titulo} ═══")
        self.toca_beats(aula.beats)


# ─────────────────────────────────── AULA DE EXEMPLO (escrita à mão pra fixar o formato)
# É o problema do Antonio: terreno-trapézio, casa com área equivalente a parte dele.
TERRENO = {
    "titulo": "Área do trapézio — a casa e o quintal",
    "beats": [
        {"diz": "Vamos por partes. O terreno inteiro tem forma de trapézio.",
         "lousa": {"fn": "trapezio", "B": 18, "b": 10, "h": 6, "destacar": "bases"},
         "espera": "media"},
        {"diz": "A base de baixo, a maior, mede dezoito. A de cima, a menor, mede dez.",
         "lousa": {"fn": "trapezio", "B": 18, "b": 10, "h": 6, "destacar": "bases"}},
        {"diz": "A distância entre as duas bases é a altura.",
         "lousa": {"fn": "trapezio", "B": 18, "b": 10, "h": 6, "destacar": "h"},
         "espera": "media"},
        {"diz": "A fórmula da área do trapézio é: soma das bases, vezes a altura, dividido por dois.",
         "lousa": {"fn": "passo", "latex": r"A = \dfrac{(B + b)\cdot h}{2}"},
         "espera": "longa"},
        {"diz": "Trocando os números: dezoito mais dez dá vinte e oito, vezes a altura, dividido por dois.",
         "lousa": {"fn": "passo", "latex": r"A = \dfrac{(18 + 10)\cdot h}{2} = 14\,h"}},
    ],
    "ramos": {
        "por_que_div_2": [
            {"diz": "Boa pergunta. Olha: se fosse um retângulo com a base maior, a área seria dezoito vezes a altura. Com a base menor, dez vezes a altura.",
             "lousa": {"fn": "trapezio_como_media", "B": 18, "b": 10, "h": 6}, "espera": "media"},
            {"diz": "O trapézio fica no meio dos dois. Por isso a gente soma e divide por dois: é a média das bases.",
             "lousa": {"fn": "trapezio_como_media", "B": 18, "b": 10, "h": 6}, "espera": "longa"},
        ],
        "e_triangulo": [
            {"diz": "Se a base menor fosse encolhendo até virar zero, o trapézio vira um triângulo.",
             "lousa": {"fn": "trapezio", "B": 18, "b": 10, "h": 6, "fechar": 1.0, "destacar": "B"}},
            {"diz": "E a fórmula bate: base mais zero, vezes a altura, dividido por dois. Base vezes altura sobre dois.",
             "lousa": {"fn": "passo", "latex": r"A_{\triangle} = \dfrac{(B + 0)\cdot h}{2} = \dfrac{B\,h}{2}"}, "espera": "longa"},
        ],
        "jeito_dificil": [
            {"diz": "Dá pra resolver com equação do primeiro grau também. Chama o comprimento da casa de x, e o do quintal de dez menos x.",
             "lousa": {"fn": "passo", "latex": r"\text{casa} = x \qquad \text{quintal} = 10 - x"}, "espera": "media"},
            {"diz": "Aí você impõe que a área da casa seja igual à do quintal, e resolve pra x. Chega no mesmo resultado, dá mais volta.",
             "lousa": {"fn": "passo", "latex": r"18x = 10(10 - x) \;\Rightarrow\; x = \tfrac{100}{28}"}, "espera": "longa"},
        ],
    },
}


if __name__ == "__main__":
    aula = Aula.de_json(TERRENO)
    p = Player()
    p.toca(aula)
    print("\n--- aluno interrompe: 'por que dividido por dois?' ---")
    p.toca_beats(aula.ramos["por_que_div_2"])
    print("\n--- professor retoma ---")
    p.falar("Beleza? Então, voltando: vinte e oito vezes a altura, dividido por dois.")
    print("\n--- aluno: 'e se fosse um triângulo?' ---")
    p.toca_beats(aula.ramos["e_triangulo"])
    print(f"\nfiguras em: {p.out}/")
