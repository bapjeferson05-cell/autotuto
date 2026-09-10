# AutoTuto v2 — Spec

*2026-09-10. Reescrita limpa. O v1 virou Frankenstein: remendo em cima de remendo,
dependência do jarvis arrastada, timings mágicos espalhados, classificador furado,
fallback mentiroso. Este doc é o projeto **de novo**, sabendo o que a gente quer.*

---

## 1. O que é

Um professor de matemática por IA que **explica, desenha e conversa em tempo real**.
Não é chatbot (não cospe resposta), não é vídeo (dá pra interromper). O aluno
**interrompe**, o professor **para**, **responde no desenho**, e **retoma de onde
parou**. Alvo: **Maratona Tech** (Fase 1 até 20/09/2026) → kit open source.

## 2. A regra única

> **Nunca mentir pro aluno.**

O professor ou responde de verdade, ou **admite que não preparou aquilo** e segue.
Nunca finge que respondeu (o pecado do v1: forçar um gatilho inexistente e falar
"Boa pergunta, deixa eu achar um jeito melhor" sem fazer nada).

## 3. Ideias que sobrevivem do v1 (conceito, não código)

| ideia | por quê |
|---|---|
| **Beats + Ramos + Estado** | o plano da aula é uma lista de *beats*; interrupção empilha um *ramo*; o estado sabe "onde eu estava" e retoma |
| **LLM só planeja** | o LLM escreve o plano (JSON). Nunca desenha, nunca calcula (8B erra aritmética) |
| **Aulas de ouro à mão** | 4 aulas escritas por humano = a pedagogia de referência + few-shot do planejador |
| **Interrupção real de 3 camadas** | regex rápido → LLM curto → fallback honesto |
| **Ramos genéricos obrigatórios** | toda aula tem `por_que`, `nao_entendi`, `repete` — o fallback sempre tem pra onde ir |
| **Teclado é o caminho principal** | teclas + caixa de texto no visor. Voz é bônus, não dependência |
| **Figuras procedurais** | um compositor `figura(spec)` desenha a partir de pontos/segmentos/rótulos |
| **Cálculo em Python** | `calc` faz a conta e devolve os **passos em LaTeX** pra lousa |
| **100% local possível** | voz e desenho sempre locais; LLM local (`qwen2.5:7b`) ou API |
| **Modo gravação** | roteiro scriptado (interrupções + respostas) pro vídeo não depender de STT |

## 4. O que NÃO fazer (anti-Frankenstein)

| não | em vez disso |
|---|---|
| depender do `jarvis` (BargeInMonitor, speak_stream, config) | `voz.py` é um adapter **fino e próprio**: `piper-tts` + `faster-whisper` direto |
| Dual LLM completo / agente ReAct na interrupção | **uma** chamada request/response curta, isolada, opcional |
| 97 figuras | só as ~8 que as 4 aulas de ouro precisam. O compositor é geral; o catálogo é pequeno |
| timings mágicos espalhados (`4.0`, `700`, `30.0`, `settle`, `ritmo`…) | **tudo em `config.py`**, com nome e comentário |
| classificador que força `por_que` quando não casa | camada 1 devolve gatilho existente **ou nada** |
| `validador` de 2 níveis gigante | `schema.validar()` estrutural + `validador.checar_matematica()` — dois arquivos, um foco cada |
| misturar "o que fala" com "como fala" | `tocador` decide a sequência; `falar/ouvir/desenhar` são callbacks injetados |

## 5. Arquitetura

**Regra de dependência:** as setas só apontam pra baixo. `schema`, `calc`, `figuras`,
`estado` **não sabem** que existe LLM ou voz. `tocador` é o único que orquestra.

```
config.py        ← knobs (timings, modelo, portas, cores). Ninguém importa "pra cima".

schema.py        Aula / Beat / Ramo (dataclasses) + validar_estrutura(dict) -> [erros]
calc.py          funções puras: area_trapezio(...) -> Resultado(valor, passos_latex, unidade)
figuras/
  canvas.py      figura(spec: dict) -> PNG bytes   (pontos, segmentos, polígonos, ângulos, rótulos)
  lousa.py       tema (cores/fontes de config) + passo_latex(latex) -> PNG bytes
estado.py        EstadoAula: pilha de trilhas. proximo() / entra_ramo() / drena_ramo() / sai_ramo() / resumo()

aulas.py         AS 4 AULAS DE OURO (dicts) + RAMOS_GENERICOS + carregar(nome) -> Aula
classificador.py classificar(fala, ramos) -> str | None   (regex; nunca inventa gatilho)
llm.py           perguntar(mensagens, timeout) -> str      (Claude API OU Ollama; só isso)
cerebro.py       roteia_interrupcao(fala, contexto, ramos) -> str | None   (usa llm.py; blindado)
validador.py     checar_matematica(aula, geradores) -> [avisos]   (usa calc + figuras)
planejador.py    planeja(problema) -> (Aula, relatorio)   (llm.py + few-shot da aula de ouro + validador)

tocador.py       toca(aula, *, interrupcoes?, respostas?) -> EstadoAula
                 loop: desenha → fala → (ouve) → próximo beat
                 interrupção: classificador → cerebro → fallback honesto
                 injeta: falar(txt)->str|None, ouvir(seg)->str|None, desenhar(png,rot)

voz.py           Voz: adapter FINO. Piper (synth->PCM) + faster-whisper (transcribe).
                 falar(txt) / ouvir(seg). Pré-aquece no __init__. Zero jarvis.
visor.py         Visor: http.server stdlib. Página tema lousa. Polling /estado + /frame.png.
                 Teclas 1/2/3/0 + caixa de texto → POST. É o "primeiro caminho" da interrupção.

demos/
  demo_texto.py    aluno digita; sem voz; ~1 GB mais leve
  demo_voz.py      com voz; JARVIS_BARGE_IN equivalente = off por padrão
  demo_roteiro.py  MODO GRAVAÇÃO: aula scriptada, determinística, pro vídeo
```

## 6. Modelo de dados (schema.py)

```python
Beat  = {
  "diz": str,                       # o que o professor fala (sem LaTeX, sem "\frac")
  "figura": {"gerador": str, ...}?, # opcional: pede um desenho
  "calc":   {"gerador": str, "params": {...}}?,  # opcional: pede uma conta
  "mostra_passos": bool?,           # calc: mostra todos os passos ou só o resultado
  "diz_passos": [str]?,             # 1 frase curta narrada por passo (dual coding)
  "espera": "curta"|"media"|"longa"?,
  "pergunta": {                     # opcional: professor PERGUNTA e ESPERA (self-explanation)
     "escuta_s": int,
     "senao": str,                  # ramo se calar / errar
     "acerta": [str]?,              # substrings que contam como acerto → fading
     "confirma": str?,              # fala curta do fading (pula a derivação)
  }?,
}
Ramo  = [Beat, ...]                 # mini-sequência
Aula  = {"titulo": str, "topico": str, "dados": {...},
         "blocos": [Beat, ...], "ramos": {gatilho: Ramo, ...}}
```

`RAMOS_GENERICOS = {"por_que":[...], "nao_entendi":[...], "repete":[...]}` — merge em
toda aula no `carregar()` (a aula sobrescreve).

## 7. O loop de interrupção (o que estava quebrado)

```
aluno_falou(fala)                       # de voz OU teclado — mesmo caminho, fala é str
  ramos    = aula.ramos                 # sempre tem por_que / nao_entendi / repete
  contexto = ultimos_3_diz

  gat = classificar(fala, ramos)                 # camada 1: regex, <5ms, offline
  if gat is None and cerebro:
      gat = cerebro.roteia_interrupcao(fala, contexto, ramos)   # camada 2: LLM curto (timeout 8s)
      if gat not in ramos: gat = None

  if gat is None:                                 # camada 3: honesto
      falar("Essa eu não preparei agora — sigo daqui, e a gente volta nisso.")
      return                                      # NÃO mexe no estado; retoma a trilha

  entra_ramo(gat) → drena → sai_ramo → retoma
```

Beat `pergunta`: "não sei / sei lá / pode ser" → acolhe ("tranquilo não saber") e vai
pro `senao` (que ensina) — não trata como resposta errada silenciosa.

## 8. config.py — todos os knobs

```python
# LLM
LLM_PROVEDOR   = env("AUTOTUTO_LLM", "ollama")      # ollama | claude
LLM_MODELO     = env("AUTOTUTO_MODELO", "qwen2.5:7b")
LLM_CLAUDE     = "claude-sonnet-5"
CEREBRO_TIMEOUT_S = 8.0                              # LLM curto da interrupção
PLANEJADOR_TIMEOUT_S = 120.0

# Voz
STT_MODELO     = env("AUTOTUTO_STT", "base")         # tiny | base | small
STT_DEVICE     = "cpu"
BARGE_IN       = env("AUTOTUTO_BARGE_IN", "0") == "1" # mic interrompe? padrão NÃO
FALA_TIMEOUT_S = 12.0                                # cão-de-guarda do Piper
GRAVA_RESTO_S  = 2.0                                 # quanto grava após o corte
SILENCIO_MS    = 400                                 # silêncio que fecha a gravação
TTS_LENGTH_SCALE = 1.0

# Ritmo / visor
SETTLE_S       = 0.4                                 # figura aparece ANTES da fala
RITMO_S_POR_CHAR = 0.045                             # "fala" sem TTS (modo texto)
PAUSA = {"curta": 0.35, "media": 0.9, "longa": 1.8, None: 0.55}
VISOR_PORTA    = 8080
VISOR_POLL_MS  = 120

# Lousa (tema)
COR_FUNDO="#0E2A22"; COR_GIZ="#EAEAEA"; COR_FRACO="#8FA79C"
COR_DESTAQUE="#F2B134"; COR_AZUL="#5AB1E0"; COR_VERDE="#7BD88F"
```

## 9. Tech stack e constraints globais

- **Python 3.13**, um venv, `pyproject.toml`.
- **Deps (mínimo):** `matplotlib`, `numpy`, `pillow`, `piper-tts`, `faster-whisper`.
  Nada de `torch` explícito (faster-whisper traz o CT2). Nada de framework web.
- **Visor:** só `http.server` da stdlib. Zero dep de frontend.
- **LLM:** HTTP puro via `urllib` (Ollama local ou Anthropic API). Sem SDK.
- **100% local capaz:** voz e figuras sempre locais; LLM local por padrão.
- **PT-BR** em toda fala. `diz` nunca tem LaTeX.
- **Máquina alvo:** Lenovo LOQ, 16 GB RAM. O caminho de voz tem que caber com o
  navegador aberto → STT `base`, pré-aquecimento, sem carregar modelo que não usa.
- **Determinismo pro vídeo:** `demo_roteiro.py` roda sem STT e sem LLM (cerebro=None,
  aula de ouro).

## 10. O que o vídeo da Maratona mostra (~90s)

1. Professor desenha o trapézio e começa a fórmula.
2. Aluno interrompe (tecla/voz): *"por que divide por dois?"* → professor **para**,
   desenha os dois retângulos, explica a média, **retoma**.
3. Professor pergunta: *"e se a base de cima virasse zero?"* → aluno: *"um triângulo"*
   → fading (pula a derivação).
4. Uma pergunta fora do script → professor **honesto**: "essa eu não preparei, sigo".

## 11. Ordem de construção

Cada passo entrega software que roda e é testável sozinho:

1. `config.py` + `schema.py` (+ testes de validação estrutural)
2. `calc.py` (funções puras — TDD fácil)
3. `figuras/canvas.py` + `figuras/lousa.py` (renderiza PNG, dimensão conhecida)
4. `aulas.py` (4 aulas de ouro, validam no schema)
5. `estado.py` (pilha de trilhas — lógica pura)
6. `classificador.py` (regex + invariante da honestidade)
7. `llm.py` (uma chamada; Ollama + Claude)
8. `cerebro.py` (roteador de interrupção; usa llm)
9. `validador.py` (checagem matemática; usa calc + figuras)
10. `planejador.py` (problema → Aula; few-shot + validador)
11. `tocador.py` (o loop + 3 camadas + fallback honesto)
12. `visor.py` (tela + teclado como 1º caminho)
13. `voz.py` (adapter fino Piper + faster-whisper)
14. `demos/` (texto, voz, roteiro) + `roteiros/trapezio.json`

## 12. Não-objetivos (v2)

- Múltiplas vozes / escolha de voz.
- Renderizador ao vivo no navegador (Fase 2).
- Medir aprendizado / adaptar dificuldade.
- Mais de 4 tópicos.
- Kepler-Poinsot e sólidos de Arquimedes.
- Dual LLM, agente ReAct, memória entre sessões.
