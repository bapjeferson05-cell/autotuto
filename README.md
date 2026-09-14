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
- **ramos genéricos obrigatórios** — toda aula tem `por_que`/`nao_entendi`/`repete`/
  `de_onde_veio` (`aulas.RAMOS_GENERICOS`), então o fallback sempre tem pra onde ir.
- **`de_onde_veio`** — de onde a fórmula saiu. Cada aula de ouro conta a história
  dela (o Nilo, as tabuinhas da Babilônia, al-Khwarizmi); o genérico **admite que
  não sabe** em vez de inventar origem pra uma aula que o LLM montou.

---

## Rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -e .

# 1. os testes (294 — cobrem cada módulo + a regra "nunca mentir")
.venv/bin/pytest

# 2. o Ciclo do Trapézio, determinístico, sem LLM nem STT — pro vídeo/ensaio
.venv/bin/python demos/demo_roteiro.py roteiros/trapezio.json
#    (ou roteiros/fracao.json — a pizza, os brigadeiros e a equivalência 3/4 = 6/8)

# 3. modo texto — o aluno digita o assunto ou cola a questão (leve, sem voz)
.venv/bin/python demos/demo_texto.py

# 4. modo voz — com Piper (TTS) + faster-whisper (STT), zero jarvis
.venv/bin/python demos/demo_voz.py
#    (antes, uma vez: python -m piper.download_voices pt_BR-faber-medium \
#       --download-dir ~/.local/share/autotuto/vozes
#     vozes pt-BR disponíveis: faber · cadu · edresson · jeff)

# 5. a régua: 11 tópicos pelo planejador, mede quantos ele planeja de verdade
#    (quantos caem no fallback, quantos saem com aviso, e quanto tempo leva)
.venv/bin/python demos/bateria.py
```

Abre `http://localhost:8080`. **Teclado é o caminho principal de interrupção** — teclas
`1` (por quê) · `2` (não entendi) · `3` (e se fosse um triângulo) · `0` (responder) · `4` (de onde veio) — ou
a caixa de texto. Voz é bônus: `AUTOTUTO_BARGE_IN=0` por padrão (o mic não interrompe
sozinho — liga com `AUTOTUTO_BARGE_IN=1` se o ambiente tiver echo-cancel).

Cérebro: `ollama` + `qwen2.5:7b` local (default) ou **qualquer provedor de nuvem** —
inclusive os grátis sem cartão (groq, gemini, openrouter, github, nvidia):

```bash
python -m autotuto.chaves      # escolhe o provedor, cola a chave, pronto
```

Grava num `.env` (permissão 600, já no `.gitignore`) que o `config.py` carrega sozinho.
Quase todo provedor fala a API OpenAI-compatível, então trocar é só mudar
`AUTOTUTO_LLM` — ver **[docs/PROVEDORES.md](docs/PROVEDORES.md)** pra tabela de tiers
grátis, armadilhas e como apontar pro seu próprio endpoint (vLLM/LM Studio). Todos os
knobs (timings, modelo, portas, cores da lousa) vivem em `autotuto/config.py`.

---

## Mapa dos arquivos

| arquivo | o quê |
|---|---|
| `autotuto/config.py` | todo knob do projeto — timings, modelo de LLM/STT, porta do visor, cores da lousa |
| `autotuto/schema.py` | `Aula`/beat/ramo (dataclasses) + `validar_estrutura()` |
| `autotuto/fala_formula.py` | LaTeX do projeto → frase falada em PT-BR (o passo não fica mudo quando falta `diz_passos`); na dúvida, cala |
| `autotuto/calc.py` | Python faz a aritmética (LLM pequeno erra conta), devolve `Resultado(valor, passos_em_LaTeX)` |
| `autotuto/figuras/canvas.py` | renderizador **universal**: `figura(spec)` compõe pontos/segmentos/polígonos/ângulos/marcas/rótulos/círculos (e fatias de círculo) |
| `autotuto/figuras/lousa.py` | tema (cores da lousa) + `passo_latex(latex)` |
| `autotuto/figuras/catalogo.py` | geradores nomeados (trapézio, balança, tabela de proporção, círculo, a pizza da fração...) usados pelo planejador |
| `autotuto/estado.py` | `EstadoAula` — pilha de trilhas. Interrupção empilha ramo, `drena_ramo()` toca e desempilha, a principal retoma |
| `autotuto/aulas.py` | **5 aulas de ouro** escritas à mão: `trapezio`, `pitagoras`, `eq_primeiro_grau`, `regra_de_tres`, `fracao` — o MVP e o few-shot do planejador |
| `autotuto/classificador.py` | fala do aluno → gatilho de ramo (regex; nunca devolve gatilho que a aula não tem) |
| `autotuto/llm.py` | uma função — `perguntar(mensagens, timeout)` — Ollama local ou Claude API |
| `autotuto/cerebro.py` | LLM **curto**, só na interrupção: fala + contexto + ramos disponíveis → escolhe um ramo real ou `None` |
| `autotuto/validador.py` | checagem matemática (avisos não-fatais: gerador desconhecido, params ruins, valor negativo) |
| `autotuto/planejador.py` | problema → LLM → `Aula`. Few-shot dirigido por tópico + loop de correção |
| `autotuto/tocador.py` | o loop: figura → fala → passos → **as 3 camadas de interrupção** → fallback honesto |
| `autotuto/visor.py` | a tela: `http.server` stdlib, tema lousa, caixa de texto, teclas de contingência |
| `autotuto/voz.py` | adapter fino: Piper (TTS) + faster-whisper (STT) direto — **zero jarvis**, pré-aquece no boot |
| `demos/demo_texto.py` / `demo_voz.py` / `demo_roteiro.py` | os 3 pontos de entrada |
| `demos/bateria.py` | régua do planejador: N tópicos → quantos planejam, quantos caem no fallback, tempo por tópico |
| `roteiros/trapezio.json` · `roteiros/fracao.json` | modo gravação — interrupções e respostas scriptadas, pro vídeo não depender de STT |
| `docs/SPEC.md` | a spec: a regra única, as ideias que sobrevivem, o que NÃO fazer, arquitetura completa |
| `docs/superpowers/plans/2026-09-10-autotuto-v2.md` | o plano de 15 tasks (TDD) que reescreveu o projeto do zero |

---

## Estado

- ✅ regra "nunca mentir" verificada por 2 rounds de review + testes dedicados
- ✅ pipeline problema→aula (planejador + schema + validador) · interrupção em 3 camadas
- ✅ máquina de estado (interrompe/retoma) · beat `pergunta` + fading · ramos genéricos
- ✅ passo de conta narrado automático quando o plano não traz `diz_passos`
- ✅ 5 aulas de ouro (a de fração usa a pizza e os brigadeiros) · passos narrados (dual coding) · few-shot dirigido por tópico
- ✅ voz (Piper + faster-whisper, adapter próprio) · visor · modo voz / texto / roteiro
- ✅ teclado como caminho principal de interrupção (mic é bônus, `BARGE_IN=0` por padrão)
- ✅ 294 testes, 0 warnings
- ✅ círculo, setor de círculo e a pizza da fração · área/circunferência no `calc`
- ⏳ mais aulas de ouro (círculo ainda não tem a dela) · renderer ao vivo no
  navegador (Fase 2) · teste do caminho de mic (`BARGE_IN=1`) com hardware real
