# Professor de Matemática Interativo

*2026-09-09. Ideia: pegar as peças que a gente já tem separadas — renderização
matemática, voz, agente — e juntar num professor de matemática com IA que
**explica, desenha e conversa em tempo real**. Alvo: Maratona Tech → GitHub open
source → kit reproduzível.*

---

## 1. O que é (e o que NÃO é)

**NÃO é** um vídeo com IA narrando. **NÃO é** "uma IA que responde matemática".

**É** uma aula interativa:

> **Professor:** "Pra calcular a área desse trapézio, primeiro a gente soma as duas bases—"
> **Aluno:** "Peraí! Por que dividiu por dois?"
> *(o professor PARA de falar)*
> **Professor:** "Boa. Porque a gente quer a média das duas bases..." *(desenha as duas bases lado a lado, mostra a média no meio)*
> **Professor:** "Beleza? Então voltando: soma as bases, multiplica pela altura, divide por dois."

O aluno **interrompe**, o professor **para**, **entende**, **responde no desenho**,
e **retoma de onde parou**. E a explicação **não é fixa**:

| o aluno faz | o professor faz |
|---|---|
| pergunta "por quê?" | volta uma etapa, explica o *motivo* daquele passo |
| não entendeu | troca a explicação (fórmula → equação → geometria) |
| quer mais fundo | aprofunda |
| "mostra aí" | manda o renderizador desenhar |

Isso vem direto da tua sacada do trapézio: **uma questão tem várias explicações**
(fórmula direta, equação + equivalência, geometria). O professor escolhe a certa
pro aluno naquele momento.

---

## 2. As peças — **você já tem quase tudo**

| peça | onde está hoje | estado |
|---|---|---|
| **Renderização matemática** | `~/projetos-ssd/projetos/mathtok/` — Manim 0.21, formato `conta` (equação morphando passo a passo), cenas 2D e 3D, sonificação | ✅ funciona |
| **STT** (ouvir o aluno) | `~/jarvis/jarvis/stt/engine.py` — faster-whisper | ✅ funciona |
| **TTS** (professor falar) | `~/jarvis/jarvis/tts/piper.py` — Piper pt-BR | ✅ funciona |
| **Barge-in** (interromper e retomar) | `~/jarvis/jarvis/audio/monitor.py` + `core/speaker.py` — **o mecanismo EXATO**: fala em stream, o mic vigia, voz sustentada → corta o TTS, devolve `interrupted` | ✅ funciona |
| **Agente ReAct** (raciocinar + usar ferramenta) | `~/jarvis/jarvis/core/assistant.py` — loop hermes3:8b, tools nativas do Ollama | ✅ funciona |
| **Pesquisa de render em tempo real** | `~/projetos-ssd/PESQUISA_render-matematica-e-holograma.md` — Manim OpenGL, Motion Canvas, etc. | 📄 feita |

**O projeto é juntar isso numa arquitetura só.** O trabalho novo é a cola, não as peças.

---

## 3. Arquitetura

```
   ┌─ aluno fala ──────────────────────────────────────────────┐
   │                                                            │
   ▼                                                            │
[STT whisper] ──texto──▶ ┌──────────────────────────────┐       │
                         │   PROFESSOR (agente)          │       │
   ┌─ barge-in ─────────▶│   - lê o "plano de aula"      │       │
   │  (corta a fala)     │   - decide o próximo passo    │       │
   │                     │   - responde pergunta do aluno│       │
   │                     │   - escolhe QUAL explicação   │       │
   │                     └──────┬──────────────┬─────────┘       │
   │                            │              │                 │
   │                       fala │              │ desenha          │
   │                            ▼              ▼                 │
   │                    [TTS Piper]     [RENDERIZADOR]           │
   │                            │              │                 │
   │                            ▼              ▼                 │
   └──────────────────── alto-falante        tela ──────────────┘
                         (sincronizados)
```

**Estado da aula** (o que a versão do jarvis não tem): o professor guarda
*"onde eu estava"* — passo atual, o que já foi dito, qual explicação está usando.
Quando o aluno interrompe e volta, ele sabe retomar.

### O renderizador é uma FERRAMENTA do agente
Igual `buscar_arquivo` no jarvis, mas pra desenhar:

```
desenhar_figura(tipo, params)     → trapézio, triângulo, círculo, eixos, gráfico de f(x)
mostrar_passo(latex)              → uma linha de equação (formato `conta`)
destacar(elemento)                → pisca/colore uma parte da figura atual
comparar(a, b)                    → duas figuras lado a lado
limpar()                         → tela limpa
```

O agente **fala e desenha ao mesmo tempo**: emite texto pro TTS e chama a tool
de desenho no mesmo turno.

---

## 4. O renderizador — 3 níveis (fazer o 1, planejar o 2)

O Manim renderiza pra **arquivo de vídeo** — lento demais pra interação. Opções:

| nível | como | quando |
|---|---|---|
| **1 — templates paramétricos** (MVP) | ~15 figuras pré-programadas (trapézio, triângulo, círculo, eixos, f(x)…) desenhadas na hora com **matplotlib** ou **SVG** ou **Manim OpenGL still**. Rápido (<0,3 s), cobre o 1º ano de geometria e álgebra | **agora** |
| **2 — Manim OpenGL ao vivo** | `--renderer=opengl` faz preview interativo. Tem buracos de doc mas anima de verdade | Fase 2, se o demo pedir |
| **3 — canvas no browser** (Motion Canvas / web) | professor vira uma página web, desenha com JS, preview instantâneo. Melhor pra "morphing" | Fase 3, pra virar produto |

O **`conta`** do mathtok (equação serif morphando) é o modelo do `mostrar_passo` —
dá pra portar a lógica pro nível 1.

---

## 5. MVP — o que demonstrar na Maratona Tech

**Um tópico, redondo: área do trapézio.**

1. Aluno (voz): *"como calcula a área de um trapézio?"*
2. Professor: desenha o trapézio + fala *"tem duas bases, uma maior e uma menor, e a altura entre elas"* (destaca cada uma)
3. Professor: *"a fórmula é: soma das bases, vezes a altura, dividido por dois"* — `mostrar_passo`
4. Aluno **interrompe**: *"por que dividido por dois?"*
5. Professor **para**, desenha os dois retângulos (base maior × h e base menor × h), mostra que a área real é a **média** → *"por isso divide por dois: é a média das duas bases"*
6. Professor: *"beleza? então: (B + b) × h ÷ 2"* — **retoma**
7. Aluno: *"e se fosse um triângulo?"* → professor: *"triângulo é um trapézio com a base menor = zero"* — desenha o trapézio "fechando" num triângulo

Se **isso** funcionar ao vivo, é uma apresentação forte: voz natural + desenho
que responde + adapta + retoma. É "ambiente de ensino generativo", não chatbot.

---

## 6. Cérebro: local ou nuvem?

| | local (hermes3:8b) | Claude API |
|---|---|---|
| pedagogia / raciocínio | fraco (errou história no bench) | forte |
| offline / "roda em qualquer PC" | ✅ (história boa pro open source) | ❌ |
| custo | zero | por chamada |

**Recomendação:** demo da Maratona = **Claude API** (a qualidade da explicação é o
que impressiona). Open source / kit = **local por padrão, nuvem opcional**. Os dois
cabem — é trocar o `client.py`.

---

## 7. Decisões (você responde)

1. **Quando é a Maratona Tech?** — o prazo define tudo.
2. **Nome do projeto.** "Matemática em Movimento" é o canal. Ideias pro professor:
   **Mateus** (Matemática + tutor), **Tales** (o geômetra), **Régua** (simples/BR),
   ou algo teu.
3. **MVP: trapézio** (o teu exemplo) ou outro tópico?
4. **Repositório:** começo em `~/professor-matematica/` (git desde o commit 1,
   como no relógio). Ok?
