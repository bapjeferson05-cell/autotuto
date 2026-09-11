# Pitch — AutoTuto na Maratona Tech

*Roteiro do que falar e do que apertar. Alvo: ~5 min de fala + ~90 s de demo ao vivo.
Fase 1 encerra 20/09/2026 · Fase 2 05/10/2026.*

---

## 0. Antes de subir (checklist de 2 min)

- [ ] `free -g` — pelo menos 4 GB livres. Fechar Firefox, Sober e o app Claude desktop.
- [ ] `wpctl status` — `echo_cancel_source` / `echo_cancel_sink` como default (barge-in com caixa de som, sem fone).
- [ ] Visor no **monitor 2**, tela cheia, navegador sem barra.
- [ ] `AUTOTUTO_LLM=claude` no ambiente (a explicação é o que impressiona; o local é o plano B).
- [ ] Rodar `demos/demo_roteiro.py roteiros/trapezio.json` **uma vez** antes — não depende de LLM nem de internet, é o caminho mais seguro pra abrir.
- [ ] Testar as teclas `1 2 3 0` na página — é a contingência se o mic do palco falhar.

---

## 1. Abertura (30 s) — o problema

> "Todo mundo aqui já usou uma IA pra tirar dúvida de matemática. E todo mundo já
> teve a mesma sensação: ela **te dá a resposta**, mas não **te ensina**. Você não
> pode interromper no meio, não pode dizer 'peraí, essa parte eu não entendi', não
> tem um desenho que reage ao que você perguntou.
>
> Um vídeo-aula você não interrompe. Um chatbot não desenha junto com a fala. O
> **AutoTuto** é a terceira coisa: uma aula onde o aluno corta a explicação, o
> professor para na hora, responde **no desenho**, e retoma de onde parou."

---

## 2. Demo ao vivo (90 s) — o Ciclo do Trapézio

**Deixa o AutoTuto começar a aula sozinho.** Ele desenha o trapézio (18 / 10 / 6) e fala.

| t | professor (áudio + tela) | você faz |
|---|---|---|
| 0 s | desenha o trapézio, nomeia as bases e a altura | nada |
| ~12 s | "a fórmula é: soma das bases, vezes a altura, sobre dois" — aparece a linha em LaTeX | nada |
| ~18 s | começa a substituir os números… | **interrompe:** fala *"peraí, por que que divide por dois?"* (ou aperta **1**) |
| — | **para na hora.** Desenha os dois retângulos: 18×6 e 10×6, e depois o retângulo de 14×6 (a média). "O trapézio fica no meio — é a média. Por isso sobre dois." | nada |
| — | "beleza? então voltando:" — **retoma** e fecha em 84 (a conta não se perde, mesmo interrompida) | nada |
| ~fim | faz a pergunta de volta: *"e se a base de cima encolhesse até zero, o que sobra?"* e **espera** | responde *"um triângulo"* (ou aperta **0**) |
| — | resposta certa → confirma curto, **pula a derivação** (fading) | — |

**O que narrar por cima enquanto ele fala** (baixinho, sem competir):
- na interrupção: *"olha — ele parou no meio da frase."*
- nos retângulos: *"isso não é um slide. O renderizador desenhou isso agora, na hora."*
- na retomada: *"e voltou exatamente de onde tinha parado — a conta não sumiu."*

---

## 3. Como funciona (45 s) — 3 frases

> "O LLM **não desenha e não faz conta** — o benchmark mostrou que modelo pequeno erra
> aritmética. Ele escreve um **plano**: uma lista de falas, cada uma podendo pedir
> uma figura ou uma conta. Um validador confere a matemática antes de ir pro ar.
>
> A interrupção tem **3 camadas**: regex rápido, depois um LLM curto só pra essa
> dúvida, e se nenhum dos dois souber, o professor **admite** — 'essa eu não
> preparei, sigo daqui' — em vez de fingir que respondeu. É a regra do projeto:
> nunca mentir pro aluno.
>
> Roda **tudo local** — voz (Piper + faster-whisper), desenho e, se quiser, o
> próprio LLM (`qwen2.5:7b`). Zero mensalidade pro aluno."

---

## 4. As duas portas de entrada (15 s)

> "Duas formas de começar: o aluno **fala** o assunto que travou — ou **digita**, ou
> **cola a questão inteira** da lista e pede pra explicar. Não é um chat: é uma
> lousa que ouve."

---

## 5. O pedido / roadmap (20 s)

> "Hoje: 4 aulas de ouro (trapézio, Pitágoras, equação do 1º grau, regra de três), o
> ciclo de interrupção honesto fechado e testado (120 testes automatizados). Fase 2:
> mais aulas, o renderizador ao vivo no navegador, e o kit open source pra qualquer
> professor montar as aulas dele. O código está no GitHub, licença aberta."

---

## Se der ruim ao vivo (plano B)

| falha | o que fazer |
|---|---|
| mic não pega a interrupção | apertar **1 / 2 / 3 / 0** na página — mesma coisa, entra como fala do aluno |
| barge-in falso (eco da caixa) | `AUTOTUTO_BARGE_IN=0` (é o padrão) e usar só as teclas |
| LLM lento / sem internet | `demos/demo_roteiro.py roteiros/trapezio.json` — aula de ouro scriptada, roda sem rede e sem LLM |
| trava geral | `Ctrl+C`, narrar o fluxo pelo diagrama do README |
| pouca RAM → morre no meio | `demos/demo_texto.py` (modo texto, sem STT/TTS) |

---

## Perguntas que os jurados fazem

**"Isso não é só um wrapper de ChatGPT?"**
Não. O LLM só escreve o plano. A pedagogia (worked example, *concreteness fading*,
auto-explicação), o renderizador, o motor de conta, o classificador de interrupção e
o estado da aula são nossos. Trocar o LLM é trocar um arquivo (`autotuto/llm.py`).

**"Por que não um vídeo?"**
Vídeo não para quando você não entende. A interrupção + retomada é a tese do projeto.

**"Funciona pra outros assuntos?"**
4 aulas de ouro hoje, cada uma com sua pedagogia (worked example + fading). Aula nova
= escrever um exemplo de ouro seguindo o padrão de `autotuto/aulas.py`; o few-shot
dirigido do planejador faz as aulas geradas por LLM herdarem a mesma pedagogia.

**"Roda offline?"**
Voz e desenho, sempre. O LLM roda local com `qwen2.5:7b`. Na demo usamos a API pela
qualidade da explicação.

**"Como mede aprendizado?"**
Hoje não mede — o beat `pergunta` já coleta a resposta do aluno (auto-explicação).
Próximo passo: usar isso pra decidir se aprofunda ou segue (o *fading* já faz uma
versão disso: se o aluno acerta a intuição, pula a derivação).

**"E se o professor não souber responder uma pergunta?"**
Ele admite. É a regra única do projeto — testada e revisada duas vezes: nunca finge
que respondeu uma coisa que não preparou.

**"Quanto custa rodar?"**
Pro aluno, com LLM local: zero. Só a máquina dele.
