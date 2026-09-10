# AutoTuto — professor de matemática interativo

Um professor de matemática por IA que **explica, desenha e conversa em tempo real**.
Não é um chatbot que cospe a resposta, nem um vídeo que você não pode interromper:
é uma aula onde o aluno **interrompe**, o professor **para**, **responde no desenho**
e **retoma de onde parou**.

> **Aluno:** *"Peraí, por que dividido por dois?"*
> *(o professor para de falar na hora)*
> **Professor:** *"Boa. Olha: se fosse um retângulo com a base maior seria 18×6; com a
> menor, 10×6. O trapézio fica no meio — por isso a média das bases."* *(desenha os
> dois retângulos)*
> **Professor:** *"Beleza? Então voltando: soma as bases, vezes a altura, sobre dois."*

Alvo: **Maratona Tech** → GitHub open source → kit reproduzível. 100% local (voz,
renderização e — opcionalmente — o LLM rodam na máquina do aluno).

---

## Como a IA e a renderização conversam

O LLM **não desenha e não faz conta**. Ele escreve um **plano** (JSON): uma lista de
*beats*, cada um = uma coisa pra falar + (opcional) uma figura pra pedir + (opcional)
uma conta pra pedir. Um `Player` (o `Tocador`) executa: fala no TTS enquanto a figura
aparece, espera acabar (ou o aluno interromper), próximo beat.

```
problema (voz ou texto)
   │
   ▼  professor/planejador.py      LLM → JSON        (qwen2.5:7b local, ou Claude API)
PLANO estruturado (Aula: blocos + ramos)
   │
   ▼  professor/validador.py       2 níveis          estrutural + matemático
Aula validada  ── erros voltam pro LLM, ele corrige (loop) ──┐
   │                                                          │
   ▼  professor/tocador.py         orquestra                  │
figura (PNG) + passos (LaTeX) + fala + espera                 │
   │         ▲                                                │
   │         └── aluno interrompe → classifica → ramo → retoma┘
   ▼
professor/visor.py                 a tela (http.server, zero dep)
```

- **beats** `{diz, figura?, calc?, espera, pergunta?}` — worked-example, um passo por vez.
  `calc` com `diz_passos` narra cada linha da conta enquanto ela aparece (dual coding).
- **ramos** — mini-sequências indexadas por gatilho (`por_que_div_2`, `nao_entendi`,
  `e_triangulo`, `decompor`). O aluno interrompe → o agente escolhe um ramo → toca →
  o `EstadoAula` retoma o beat onde parou.
- **beat `pergunta`** `{pergunta: {escuta_s, senao, confirma?}}` — o professor devolve a
  pergunta e **espera** o aluno tentar explicar antes de dar a resposta
  (*self-explanation*). Se o aluno acerta, `confirma` dá um retorno curto e **pula a
  derivação** (*fading* — worked example atrapalha quem já sabe).
- os 5 princípios que guiam tudo isso: `PESQUISA_matematica-de-gente.md`.

---

## Rodar

```bash
python3 -m venv .venv && .venv/bin/pip install matplotlib numpy pillow

# 1. renderizador — bate a lista das ~100 figuras geométricas (97/98)
.venv/bin/python treinar.py                # → COBERTURA.md + out/treinar/*

# 2. o Ciclo do Trapézio no terminal (sem áudio)
.venv/bin/python demo.py

# 3. problema → LLM → aula, em 5 exemplos reais  (precisa do Ollama + qwen2.5:7b)
.venv/bin/python exemplos.py

# 4. shootout: qual LLM local escolhe o método certo
.venv/bin/python cerebro_shootout.py
```

### Modo web (backend + frontend) — chat no navegador

Mesmo `professor/` de sempre, exposto por HTTP em vez de voz/terminal: um backend
FastAPI toca a aula um passo por vez, um frontend React mostra o chat, as figuras e os
passos da conta (renderizados com KaTeX).

```bash
# backend
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
.venv/bin/uvicorn backend.app:app --reload          # http://localhost:8000

# frontend (outro terminal)
cd frontend && npm install && npm run dev            # http://localhost:5173
```

Ou os dois de uma vez com Docker: `cp .env.example .env` (preenche a `ANTHROPIC_API_KEY`),
depois `docker compose up --build` → `http://localhost:8080`.

### Com voz e visor (precisa do stack de áudio do jarvis)

```bash
# o venv do jarvis tem Piper + faster-whisper; instale matplotlib+pillow lá
PYTHONPATH=$PWD ~/jarvis/.venv/bin/python demo_voz.py trapezio loop   # voz + barge-in
PYTHONPATH=$PWD ~/jarvis/.venv/bin/python demo_voz.py aluno           # o aluno fala o problema
PYTHONPATH=$PWD ~/jarvis/.venv/bin/python demo_texto.py               # o aluno DIGITA (sem STT, ~1GB leve)
```

Abre `http://localhost:8080`. Interrompe por voz, ou pelas teclas na página
(`1` por quê · `2` não entendi · `3` triângulo · `0` responder) — **contingência**
pra quando o microfone do local falhar.

Áudio: com `echo_cancel_source`/`sink` do PipeWire como default, o barge-in funciona
com **caixa de som, sem fone**. Cérebro: `PROF_LLM=claude` (rápido, ~4s) ou
`qwen2.5:7b` local (default, ~20-40s).

---

## Mapa dos arquivos

| arquivo | o quê |
|---|---|
| `professor/esquema.py` | fonte única: catálogo dos ~21 geradores + dataclass `Aula`. `catalogo_para_prompt()` gera a seção do prompt do próprio dict |
| `professor/figuras/primitivas.py` | renderizador **universal**: `figura(spec)` compõe pontos/segmentos/polígonos/círculos/ângulos/marcas/cotas. `funcao(expr)`, `reta_numerica()`, `passo(latex)` |
| `professor/figuras/formas.py` | 2D por tipo: `triangulo`, `quadrilatero`, `poligono_regular(n)` (até 10⁶ lados), `estrela(n,k)`, `curva`, `parte_circulo` |
| `professor/figuras/solidos.py` | 3D wireframe: platônicos, corpos redondos, prismas, `_truncar()` = os 6 sólidos de Arquimedes |
| `professor/calc.py` | Python faz a aritmética (o 8B erra), devolve `Resultado(valor, passos_em_LaTeX)` |
| `professor/planejador.py` | problema → LLM → `Aula`. Loop de correção (4×), reparo, `_saneia`. `PROF_LLM=claude` ou `ollama` |
| `professor/validador.py` | 2 níveis: gerador existe / params batem, **e** as propriedades da figura conferem (nº de lados, ângulo reto, área > 0) |
| `professor/estado.py` | `EstadoAula` — pilha de trilhas. Interrupção empilha ramo, `drena_ramo()` toca e desempilha, a principal retoma |
| `professor/tocador.py` | orquestra figura → fala → passos. `settle` 0.4s (figura antes da voz) |
| `professor/classificador.py` | fala do aluno → gatilho de ramo (regex; LLM depois) |
| `professor/fillers.py` | "estou aqui" instantâneo por gatilho (frase fixa — não precisa de "LLM pequeno") |
| `professor/aulas.py` | **aulas de ouro** escritas à mão: `trapezio`, `pitagoras`, `eq_primeiro_grau` (balança), `regra_de_tres` (proporção) — o MVP e o few-shot dirigido do planejador |
| `professor/voz.py` | ponte pro jarvis (Piper + faster-whisper + barge-in). `falar` com cão-de-guarda; `ouvir` limitado; injeção por teclado |
| `professor/visor.py` | a tela: `http.server` stdlib, tema lousa, caixa de texto, teclas de contingência |
| `backend/app.py` + `backend/services/sessao.py` | API HTTP do mesmo `professor/` — um beat por request (sessão em memória), pro modo web |
| `frontend/` | chat em React+TypeScript: mostra a fala, a figura e os passos da conta (KaTeX) |
| `PROJETO.md` | a arquitetura e o MVP em detalhe |
| `COBERTURA.md` | relatório do renderizador contra as ~100 figuras |
| `PESQUISA_matematica-de-gente.md` | 5 princípios de pesquisa educacional mapeados pro código |
| `PESQUISA_pedagogia-llm.md` | datasets + shootout de cérebro local (qwen2.5:7b venceu 8/8) |

---

## Estado

- ✅ renderizador (97/98 figuras) · pipeline problema→aula · validador 2 níveis
- ✅ máquina de estado (interrompe/retoma) · beat `pergunta` + fading · classificador · fillers
- ✅ 4 aulas de ouro · passos narrados · few-shot dirigido por tópico
- ✅ voz (Piper + faster-whisper + barge-in + AEC) · visor · modo voz / texto / o-aluno-começa
- ✅ contingência de teclado (mic ruim no palco)
- ✅ modo web: backend FastAPI (`backend/`) + frontend React/KaTeX (`frontend/`) + Docker
- ⏳ mais aulas de ouro · renderer: caprichar toro + Arquimedes · versão celular
