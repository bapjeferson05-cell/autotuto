# Pitch — AutoTuto na Maratona Tech

*Roteiro do que falar e do que apertar. Alvo: ~5 min de fala + ~90 s de demo ao vivo.
Fase 1 encerra 20/09/2026 · Fase 2 05/10/2026.*

---

## 0. Antes de subir (checklist de 2 min)

- [ ] `free -g` — pelo menos 4 GB livres. Fechar Firefox e o Sober.
- [ ] `wpctl status` — `echo_cancel_source` / `echo_cancel_sink` como default (barge-in com caixa de som, sem fone).
- [ ] Visor no **monitor 2**, tela cheia, navegador sem barra.
- [ ] `PROF_LLM=claude` no ambiente (a explicação é o que impressiona; o local é o plano B).
- [ ] Rodar `demo_voz.py trapezio` **uma vez** e deixar aquecido. Se o palco não tiver internet: `demo_voz.py trapezio` já com `PROF_LLM` vazio (aula de ouro, sem LLM).
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
| — | **para na hora.** Desenha os dois retângulos: 18×6 e 10×6. "Se fosse retângulo seria um ou outro. O trapézio fica no meio — é a média. Por isso sobre dois." | nada |
| — | "beleza? então voltando:" — **retoma** a substituição de onde parou, fecha em 84 | nada |
| ~fim | faz a pergunta de volta: *"e se a base de cima encolhesse até zero, o que sobra?"* e **espera** | responde *"um triângulo"* (ou aperta **0**) |
| — | "isso — e aí a fórmula vira base vezes altura sobre dois, que é a do triângulo. Mesmo desenho." | — |

**O que narrar por cima enquanto ele fala** (baixinho, sem competir):
- na interrupção: *"olha — ele parou no meio da frase."*
- nos dois retângulos: *"isso não é um slide. O LLM pediu essa figura agora, pro renderizador."*
- na retomada: *"e voltou exatamente de onde tinha parado."*

---

## 3. Como funciona (45 s) — 3 frases

> "O LLM **não desenha e não faz conta** — o benchmark mostrou que modelo de 8B erra
> aritmética. Ele escreve um **plano**: uma lista de falas, cada uma podendo pedir
> uma figura ou uma conta. Um validador confere a matemática antes de ir pro ar.
>
> Um executor toca esse plano: fala no TTS enquanto a figura aparece. Quando o mic
> ouve a voz do aluno sustentada, **corta o TTS** e classifica o que ele disse num
> dos *ramos* que o plano já trouxe — 'por quê', 'não entendi', 'e se fosse'.
>
> Renderizador universal: 97 das 100 figuras de geometria do ensino fundamental,
> compostas de pontos, segmentos e ângulos. Roda **tudo local** — voz, desenho e,
> se quiser, o próprio LLM (`qwen2.5:7b`). Zero mensalidade pro aluno."

---

## 4. As duas portas de entrada (15 s)

> "Duas formas de começar: o aluno **fala** o assunto que travou — ou **digita**, ou
> **cola a questão inteira** da lista e pede pra explicar. Não é um chat: é uma
> lousa que ouve."

---

## 5. O pedido / roadmap (20 s)

> "Hoje: 4 aulas de ouro (trapézio, Pitágoras, equação do 1º grau, regra de três),
> 16 tipos de conta, o ciclo de interrupção fechado. Fase 2: mais aulas, o
> renderizador ao vivo no navegador, e o kit open source pra qualquer professor
> montar as aulas dele. O código está no GitHub, licença aberta."

---

## Se der ruim ao vivo (plano B)

| falha | o que fazer |
|---|---|
| mic não pega a interrupção | apertar **1 / 2 / 3 / 0** na página — mesma coisa, entra como fala do aluno |
| barge-in falso (eco da caixa) | `JARVIS_BARGE_IN=0` e usar só as teclas |
| LLM lento / sem internet | rodar sem `PROF_LLM` → aula de ouro do trapézio, roda sem rede |
| trava geral | `Ctrl+C`, mostrar `out/demo-tira.png` (a aula inteira em tiras) e narrar o fluxo pelo diagrama do README |
| pouca RAM → morre no meio | `demo_texto.py` (modo texto, ~1 GB a menos, sem STT/TTS) |

---

## Perguntas que os jurados fazem

**"Isso não é só um wrapper de ChatGPT?"**
Não. O LLM só escreve o plano. A pedagogia (worked example, *concreteness fading*,
auto-explicação), o renderizador, o motor de conta, o classificador de interrupção e
o estado da aula são nossos. Trocar o LLM é trocar um arquivo.

**"Por que não um vídeo?"**
Vídeo não para quando você não entende. A interrupção + retomada é a tese do projeto.

**"Funciona pra outros assuntos?"**
O renderizador cobre 97/100 figuras de geometria fundamental. Conta: 16 tipos. Aula
nova = escrever um exemplo de ouro (ver `COMO_ADICIONAR_AULA.md`); o few-shot dirigido
faz as aulas geradas herdarem a pedagogia.

**"Roda offline?"**
Voz e desenho, sempre. O LLM roda local com `qwen2.5:7b` (venceu 8/8 o nosso
benchmark de escolha de método). Na demo usamos a API pela qualidade da explicação.

**"Como mede aprendizado?"**
Hoje não mede — o beat `pergunta` já coleta a resposta do aluno (auto-explicação).
Próximo passo: usar isso pra decidir se aprofunda ou segue (o *fading* já faz uma
versão disso: se o aluno acerta a intuição, pula a derivação).

**"Quanto custa rodar?"**
Pro aluno, com LLM local: zero. Só a máquina dele.
