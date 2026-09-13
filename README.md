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

Alvo: **Maratona Tech** (Fase 1 até 20/09/2026) → GitHub open source → kit reproduzível.
100% local (voz, desenho e — opcionalmente — o LLM rodam na máquina do aluno).

A **regra única** do projeto (ver `docs/SPEC.md`): **o professor nunca mente pro aluno.**
Ou responde de verdade, ou admite que não preparou aquilo e segue — nunca finge que
respondeu.

---

## Arquitetura

O LLM **não desenha e não faz conta**. Ele escreve um **plano** (JSON): uma lista de
*beats*, cada um = uma coisa pra falar + (opcional) uma figura pra pedir + (opcional)
uma conta pra pedir. O `Tocador` executa: fala enquanto a figura aparece, espera acabar
(ou o aluno interromper), próximo beat.

```
problema (voz ou texto)
   │
   ▼  autotuto/planejador.py       LLM → JSON        (qwen2.5:7b local, ou Claude API)
PLANO estruturado (Aula: blocos + ramos)
   │
   ▼  autotuto/schema.py           validação estrutural
   ▼  autotuto/validador.py        validação matemática (avisos)
Aula validada  ── erros voltam pro LLM, ele corrige (loop) ──┐
   │                                                          │
   ▼  autotuto/tocador.py          orquestra                  │
figura (PNG) + passos (LaTeX) + fala + espera                 │
   │         ▲                                                │
   │         └── aluno interrompe → 3 camadas → ramo → retoma─┘
   ▼
autotuto/visor.py                  a tela (http.server, zero dep)
```

- **beats** `{diz, figura?, calc?, espera, pergunta?}` — worked-example, um passo por vez.
  `calc` com `diz_passos` narra cada linha da conta enquanto ela aparece (dual coding).
- **ramos** — mini-sequências indexadas por gatilho (`por_que_div_2`, `nao_entendi`,
  `e_triangulo`, `repete`...). O aluno interrompe → o tocador escolhe um ramo → toca →
  o `EstadoAula` retoma o beat onde parou.
- **interrupção em 3 camadas** (`autotuto/tocador.py`): regex (`classificador.py`, <5ms)
  → LLM curto (`cerebro.py`, só se a regex não casou) → **fallback honesto** ("essa eu
  não tinha preparado, sigo daqui") se nenhuma camada souber. Nunca força um gatilho
  que a aula não tem.
- **beat `pergunta`** `{pergunta: {escuta_s, senao, acerta?, confirma?}}` — o professor
  devolve a pergunta e **espera** o aluno tentar explicar antes de dar a resposta
  (*self-explanation*). Se o aluno acerta (`acerta`), `confirma` dá um retorno curto e
  **pula a derivação** (*fading* — worked example atrapalha quem já sabe).
- **ramos genéricos obrigatórios** — toda aula tem `por_que`/`nao_entendi`/`repete`
  (`aulas.RAMOS_GENERICOS`), então o fallback sempre tem pra onde ir.

---

## Perfis de hardware

A máquina de quem vai rodar isso varia muito — de um notebook velho de 4GB até uma
máquina boa de 16GB. `AUTOTUTO_PERFIL` ajusta o *default* de LLM e do modelo de STT;
qualquer knob setado explicitamente (`AUTOTUTO_LLM`, `AUTOTUTO_STT`) sempre ganha do
perfil, seja qual for.

| perfil | RAM alvo | LLM padrão | voz (TTS/STT) | como rodar |
|---|---|---|---|---|
| `leve`   | ~4GB  | nuvem (`claude`, precisa `ANTHROPIC_API_KEY`) | não recomendada | `demo_texto.py` |
| `medio`  | ~8GB  | nuvem (`claude`) — `ollama` local ainda cabe | local cabe (STT `tiny`) | `demo_texto.py` ou `demo_voz.py` |
| `pesado` | ~16GB | local (`ollama` + `qwen2.5:7b`) — **default de sempre** | local (STT `base`) | `demo_voz.py` |

```bash
AUTOTUTO_PERFIL=leve ANTHROPIC_API_KEY=sk-... .venv/bin/python demos/demo_texto.py
```

Sem `AUTOTUTO_PERFIL`, nada muda — continua exatamente o comportamento de sempre
(`pesado`: `ollama` local). Detecção automática de RAM não existe de propósito (não dá
pra fazer direito sem depender de `psutil`, e SPEC.md já veta dependência sem
justificativa) — a escolha do perfil é sua.

As duas chamadas curtas de LLM (classificação de interrupção e avaliação semântica de
resposta) também são desligáveis individualmente — `Tocador(cerebro=None,
avaliador=None)`, como `demo_roteiro.py` já faz — pra quem quiser o caminho mais leve
possível, sem LLM nenhum (perde a inteligência de interrupção/resposta, então não é o
que `leve` recomenda por padrão).

---

## Rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -e .

# 1. os testes (120 — cobrem cada módulo + a regra "nunca mentir")
.venv/bin/pytest

# 2. o Ciclo do Trapézio, determinístico, sem LLM nem STT — pro vídeo/ensaio
.venv/bin/python demos/demo_roteiro.py roteiros/trapezio.json

# 3. modo texto — o aluno digita o assunto ou cola a questão (leve, sem voz)
.venv/bin/python demos/demo_texto.py

# 4. modo voz — com Piper (TTS) + faster-whisper (STT), zero jarvis
.venv/bin/python demos/demo_voz.py
```

Abre `http://localhost:8080`. **Teclado é o caminho principal de interrupção** — teclas
`1` (por quê) · `2` (não entendi) · `3` (e se fosse um triângulo) · `0` (responder) — ou
a caixa de texto. Voz é bônus: `AUTOTUTO_BARGE_IN=0` por padrão (o mic não interrompe
sozinho — liga com `AUTOTUTO_BARGE_IN=1` se o ambiente tiver echo-cancel).

Cérebro: `AUTOTUTO_LLM=claude` (precisa de `ANTHROPIC_API_KEY`, rápido) ou `ollama` +
`qwen2.5:7b` local (default) — ver "Perfis de hardware" acima pra qual escolher. Todos
os knobs (timings, modelo, portas, cores da lousa) vivem em `autotuto/config.py`.

---

## Mapa dos arquivos

| arquivo | o quê |
|---|---|
| `autotuto/config.py` | todo knob do projeto — timings, modelo de LLM/STT, porta do visor, cores da lousa |
| `autotuto/schema.py` | `Aula`/beat/ramo (dataclasses) + `validar_estrutura()` |
| `autotuto/calc.py` | Python faz a aritmética (LLM pequeno erra conta), devolve `Resultado(valor, passos_em_LaTeX)` |
| `autotuto/figuras/canvas.py` | renderizador **universal**: `figura(spec)` compõe pontos/segmentos/polígonos/ângulos/marcas/rótulos |
| `autotuto/figuras/lousa.py` | tema (cores da lousa) + `passo_latex(latex)` |
| `autotuto/figuras/catalogo.py` | geradores nomeados (trapézio, balança, tabela de proporção...) usados pelo planejador |
| `autotuto/estado.py` | `EstadoAula` — pilha de trilhas. Interrupção empilha ramo, `drena_ramo()` toca e desempilha, a principal retoma |
| `autotuto/aulas.py` | **4 aulas de ouro** escritas à mão: `trapezio`, `pitagoras`, `eq_primeiro_grau`, `regra_de_tres` — o MVP e o few-shot do planejador |
| `autotuto/classificador.py` | fala do aluno → gatilho de ramo (regex; nunca devolve gatilho que a aula não tem) |
| `autotuto/llm.py` | uma função — `perguntar(mensagens, timeout)` — Ollama local ou Claude API |
| `autotuto/cerebro.py` | LLM **curto**, só na interrupção: fala + contexto + ramos disponíveis → escolhe um ramo real ou `None` |
| `autotuto/validador.py` | checagem matemática (avisos não-fatais: gerador desconhecido, params ruins, valor negativo) |
| `autotuto/planejador.py` | problema → LLM → `Aula`. Few-shot dirigido por tópico + loop de correção |
| `autotuto/tocador.py` | o loop: figura → fala → passos → **as 3 camadas de interrupção** → fallback honesto |
| `autotuto/visor.py` | a tela: `http.server` stdlib, tema lousa, caixa de texto, teclas de contingência |
| `autotuto/voz.py` | adapter fino: Piper (TTS) + faster-whisper (STT) direto — **zero jarvis**, pré-aquece no boot |
| `demos/demo_texto.py` / `demo_voz.py` / `demo_roteiro.py` | os 3 pontos de entrada |
| `roteiros/trapezio.json` | modo gravação — interrupções e respostas scriptadas, pro vídeo não depender de STT |
| `docs/SPEC.md` | a spec: a regra única, as ideias que sobrevivem, o que NÃO fazer, arquitetura completa |
| `docs/superpowers/plans/2026-09-10-autotuto-v2.md` | o plano de 15 tasks (TDD) que reescreveu o projeto do zero |

---

## Estado

- ✅ regra "nunca mentir" verificada por 2 rounds de review + testes dedicados
- ✅ pipeline problema→aula (planejador + schema + validador) · interrupção em 3 camadas
- ✅ máquina de estado (interrompe/retoma) · beat `pergunta` + fading · ramos genéricos
- ✅ 4 aulas de ouro · passos narrados (dual coding) · few-shot dirigido por tópico
- ✅ voz (Piper + faster-whisper, adapter próprio) · visor · modo voz / texto / roteiro
- ✅ teclado como caminho principal de interrupção (mic é bônus, `BARGE_IN=0` por padrão)
- ✅ 121 testes, 0 warnings
- ⏳ primitiva de círculo nas figuras · mais aulas de ouro · renderer ao vivo no navegador
  (Fase 2) · teste do caminho de mic (`BARGE_IN=1`) com hardware real
