# Como adicionar uma aula de ouro

Uma **aula de ouro** é uma aula escrita à mão, com a pedagogia que a gente quer.
Elas moram em `professor/aulas.py` e servem pra: (1) o MVP, (2) few-shot dirigido
do planejador (quando o problema é do mesmo tipo, o LLM copia a estrutura).

## Passo a passo

1. **Escolha o tópico e um problema concreto.** Não "área do círculo" — *"quanto de
   cerca pra um canteiro redondo de raio 4?"*. Unidade e contexto reais.

2. **Escreva o dict** no fim de `aulas.py`, seguindo o padrão:

```python
CANTEIRO = {
    "titulo": "Comprimento da circunferência — a cerca do canteiro",
    "topico": "comprimento_circunferencia",          # = o gerador de calc principal
    "dados": {"r": 4},
    "blocos": [
        {"diz": "<frase falada, narra a DECISÃO não só o passo>",
         "figura": {"gerador": "parte_circulo", "params": {"nome": "circulo"}},
         "espera": "media"},

        # 1 beat PERGUNTA, antes do passo mais importante (self-explanation)
        {"diz": "Antes da fórmula: se eu dobrar o raio, a volta dobra também?",
         "pergunta": {"escuta_s": 12, "senao": "por_que",
                      "acerta": ["dobra", "sim", "o dobro", "duas vezes"],
                      "confirma": "Isso — a volta é proporcional ao raio."}},

        {"diz": "A fórmula é dois pi vezes o raio.",
         "calc": {"gerador": "comprimento_circunferencia", "params": {"r": 4}},
         "mostra_passos": True,
         "diz_passos": ["Dois pi erre.", "Dois pi vezes quatro: oito pi, uns vinte e cinco."],
         "espera": "longa"},

        {"diz": "Vinte e cinco metros de cerca, mais ou menos.", "espera": "media"},
    ],
    "ramos": {
        "por_que": [ {"diz": "...", "figura": {...}, "espera": "longa"} ],
        "nao_entendi": [ {"diz": "..."}, {"diz": "...", "calc": {...}, "mostra_passos": True} ],
    },
}

_CATALOGO = {..., "comprimento_circunferencia": CANTEIRO}
```

3. **Registre no few-shot dirigido** (`professor/planejador.py`, dict `_PISTAS`):

```python
"comprimento_circunferencia": ("circunferência", "circunferencia", "volta do círculo",
                               "cerca .* redond", "quanto anda a roda"),
```

4. **Regras da pedagogia** (as 5 da pesquisa — `PESQUISA_matematica-de-gente.md`):
   - **worked example**: um passo por bloco; `diz_passos` narra cada linha da conta.
   - **concreteness fading**: comece concreto (o canteiro), passe por uma figura, termine no símbolo.
   - **dual coding**: a figura aparece e o `diz` fala sobre ELA — nunca LaTeX no `diz`.
   - **self-explanation**: 1 beat `pergunta` que o aluno responde antes de você dar a resposta.
   - **think-aloud / narra a decisão**: "divide por dois PORQUE é a média", não "divide por dois".
   - **fading**: `pergunta.confirma` + `acerta` — quem acerta pula a derivação.

5. **Valide e rode:**

```bash
.venv/bin/python -c "from professor.aulas import carregar; from professor import validador; \
  print(validador.valida_aula(carregar('comprimento_circunferencia')).problemas or 'OK')"
.venv/bin/python demo.py comprimento_circunferencia
```

## Anatomia do beat

| chave | o quê |
|---|---|
| `diz` | texto falado (obrigatório, sem LaTeX) |
| `figura` | `{gerador, params}` — ou `{gerador: "figura", spec: {...}}` pra composição própria |
| `calc` | `{gerador, params}` — Python faz a conta, devolve os passos em LaTeX |
| `mostra_passos` | `true` = mostra todos os passos; senão só o último |
| `diz_passos` | `["frase", ...]` — 1 por passo, dita enquanto a linha aparece |
| `pergunta` | `{escuta_s, senao, acerta?, confirma?}` — o professor espera a resposta |
| `espera` | `"curta"` / `"media"` / `"longa"` — pausa depois do beat |

## Ramos

`ramos` são mini-sequências (1–3 beats) indexadas por gatilho. O `classificador`
mapeia a fala do aluno pro gatilho. Sempre inclua `nao_entendi` e um `por_que...`.
A trilha principal **retoma** o beat onde parou (o `EstadoAula` cuida disso).
