# AutoTuto — análise da demo de voz (lentidão + "ignora o que eu falo")

*2026-09-09. Base: `demo_voz.py trapezio loop` rodando ~6 min no monitor 2, log em
`scratchpad/demo_voz.log` (189 linhas, 3 passadas da aula + interações reais).*

---

## Resumo em 3 frases

1. **Lentidão:** cada interrupção levou **mediana 12 s, até 27 s** pra o professor
   reagir (alvo: < 2 s). Causa nº 1 = a máquina estava **em swap** (268 MB livres,
   swap 1,8 GB); o processo bateu 1,5 GB RSS a 430 % CPU.
2. **"Ele ignora o que eu falo":** é **verdade estrutural**. Toda fala fora do script
   é jogada em `classificar(...) or "por_que"` → um ramo que nem existe → a frase
   morta *"Boa pergunta. Deixa eu achar um jeito melhor de mostrar isso."* O LLM
   **nunca** é consultado numa interrupção.
3. **STT:** as transcrições foram quase todas lixo ("Lami?", "Dois, futebol.",
   "Alô, bem-vindo a você.") — o mic pega eco/ruído e o Whisper alucina palavras.

---

## 1. Lentidão — medido

`✋ ~Xs` no log = tempo de `falar()` retornar (fala → detecta corte → grava resto →
transcreve):

```
n=14   min=6,6s   mediana=12,2s   max=27,1s   média=12,8s
```

### Causas, por impacto

| # | causa | onde | efeito |
|---|---|---|---|
| 1 | **RAM em swap.** Claude desktop + Firefox (muitas abas) + desktop-commander MCP + esta sessão deixaram 268–417 MB livres. faster-whisper `small` (int8, ~500 MB) + Piper + matplotlib → 1,5 GB RSS, **paginando durante a inferência** | sistema | 1 s de transcrição vira 10 s+ |
| 2 | **grava 4 s fixos depois de cada corte** | `voz.py` `resto = self._record_ate(4.0)` | +até 4 s sempre, mesmo se o aluno já parou |
| 3 | **espera 700 ms de silêncio pra fechar a gravação** | `voz.py` `silence_limit = 700 // frame_ms` | +~1 s de rabo em toda resposta |
| 4 | **modelo STT = `small`, CPU, beam 1** | `~/.config` / env `JARVIS_STT_MODEL` | `base` (já baixado, 142 MB) é ~3× mais rápido e quase igual pra PT-BR curto |
| 5 | **beat `pergunta` espera os 12 s cheios** se o VAD não fecha | `tocador.py` `self.ouvir(seg)` → `_record_ate(12.0)` | ar morto de até 12 s |
| 6 | **cão-de-guarda `_TIMEOUT_FALA = 30`** | `voz.py` | o max 27 s é isso quase estourando |
| 7 | **Piper sintetiza a frase inteira antes de tocar** + `LENGTH_SCALE=1.1` | `voz.py` `speak_stream(iter([texto]))` | atraso pra voz começar + 10 % em toda fala |

---

## 2. "Ele ignora o que eu falo além da resposta que ele quer"

**Confirmado no log.** O aluno disse (transcrito certo):

> *"Peraí, mas você confundiu... era uma casa com terreno. A casa tinha três e um,
> cinco."*
> *"Já repetiu isso várias vezes... está rodando em loop, é?"*

Resposta do professor nos dois casos: `→ por_que` → *"Então..."* → *"Boa pergunta.
Deixa eu achar um jeito melhor de mostrar isso."* O conteúdo foi **descartado**.

### O mecanismo exato

1. **Toda interrupção é forçada em ~5 gatilhos fixos.** `tocador.py`:
   ```python
   gat = classificar(r[1], est.aula.ramos) or "por_que"
   ```
   `classificar` = ~8 regras de regex. O que não casa → `"por_que"`.
2. **O `"por_que"` forçado geralmente nem é um ramo.** O trapézio tem `por_que_div_2`,
   não `por_que` → `entra_ramo("por_que")` falha → frase morta. No log: ~10 vezes.
3. **O LLM nunca entra numa interrupção.** Por design (`fillers.py`: "pro MVP NÃO
   precisa de LLM"). O planejador roda **uma vez**, ao montar a aula. Depois é 100 %
   ramos pré-escritos + roteamento por regex.
4. **No beat `pergunta`, só importa** se a resposta casa uma palavra de `acerta` ou
   um ramo. Todo o resto → `senao`. Resposta errada pensada, uma correção, uma
   pergunta de volta — tudo colapsa no mesmo galho. No log: a transcrição-lixo
   *"Eleve a triângulo... NILUPE..."* casou `acerta` (tem "triângulo") →
   *"✓ acertou — pula a derivação"*. É match de substring, não compreensão.

### É o buraco central da arquitetura

"beats + ramos" assume que dá pra pré-enumerar toda resposta possível do aluno.
Aluno de verdade não fica no script. O conserto é ter um **classificador/respondedor
de verdade no loop**: quando `classificar` volta vazio, manda a fala + o contexto da
aula pro LLM e deixa ele (a) escolher o melhor ramo, ou (b) gerar uma resposta curta
falada + uma figura, e retomar.

---

## 3. STT — qualidade (alimenta os dois problemas)

Transcrições reais do log: "Lami?", "Dois, futebol.", "Alô, bem-vindo a você.",
"Você consegue ver e desenhar um circo.", "Deu, Deus que te abençoe."

Causas:
- **mic pega eco do TTS + ambiente** apesar do echo-cancel → `BargeInMonitor`
  dispara em não-fala → o Whisper **alucina** palavras a partir de ruído (Whisper
  sempre devolve *algo*).
- **`small` sob pressão de memória** degrada.
- **`STT_PROMPT` não é usado** aqui (existe no config — daria viés pro domínio de
  matemática).
- clipes < 1 s são filtrados (`audio.size < _SR`), mas 1–3 s de eco passam e viram
  alucinação.

---

## 4. Miudezas

- `BrokenPipeError` (traceback) no log do visor — o browser larga o poll no meio do
  write. Cosmético, mas suja o log. Engolir no handler.
- `loop` não zera o estado de barge entre passadas.
- `_TIMEOUT_FALA = 30` alto demais — Piper pendurado congela a aula por 30 s.

---

## 5. Recomendações (em ordem)

### P0 — deixar a máquina capaz de rodar
- Fechar o **app Claude desktop** + enxugar o Firefox antes de qualquer demo de voz.
  Precisa de ~3 GB livres de verdade.
- `JARVIS_STT_MODEL=base` (já baixado, 3× mais rápido). `tiny` pra demo se precisar.

### P1 — consertar o "ele me ignora"
- Quando `classificar` volta `None` numa interrupção, **NÃO** forçar `"por_que"`.
  Em vez disso: (a) se tem cérebro, perguntar "qual ramo, ou nenhum?" + 1 frase de
  resposta; (b) senão, dizer algo honesto ("essa eu não preparei — seguindo") e
  retomar, no lugar da frase enganosa.
- Garantir que toda aula tenha um ramo `por_que` (ou genérico), ou fazer o fallback
  retomar sem drama.
- No beat `pergunta`, ir além do substring de `acerta`: tratar "não sei / sei lá"
  explicitamente e rotear o resto pelo cérebro.

### P2 — cortar latência
- `_record_ate(4.0)` → `2.0`; rabo de silêncio `700 ms` → `400 ms`.
- **Pré-aquecer** Piper e faster-whisper com uma chamada dummy no startup (a 1ª
  inferência é sempre a mais lenta).
- `_TIMEOUT_FALA` → `12`.
- `JARVIS_TTS_LENGTH_SCALE=1.0` na demo.

### P3 — STT
- `JARVIS_BARGE_IN_VAD_THRESHOLD=0.8` (hoje 0.7) — menos disparo por eco.
- `STT_PROMPT="aula de matemática: trapézio, base, altura, triângulo, fórmula, área"`.
- **Inverter a contingência:** no palco barulhento, as teclas 1/2/3/0 devem ser o
  caminho PRINCIPAL, não o plano B. O log prova que o mic aqui não é confiável.
