# Achados — log de investigação

Registro do que foi investigado, com evidência. Só entra aqui o que foi
**executado e observado**. Hipótese não confirmada fica marcada como hipótese.

---

## 2026-09-20 — ataque ao caminho que o júri executa

Contexto: dia da entrega da Fase 1. O link do GitHub abre o `main`; a demo ao
vivo roda nesta branch (`claude/repository-improvements-fzea65`).

### O repositório tem duas árvores sem ancestral comum

`git merge-base origin/main claude/repository-improvements-fzea65` → **vazio**.

- `main` = pacote `autotuto/` (v2). Primeiro commit: `40e0c9e esqueleto do v2
  (branch orphan, docs preservados)`. Foi um pivô deliberado, documentado em
  `docs/superpowers/plans/2026-09-10-autotuto-v2.md`, que chama o v1 de
  "Frankenstein".
- esta branch = pacote `professor/` (v1). Mesma raiz (`8fd372e Initial commit`)
  que a branch local `main` obsoleta deste checkout.

Consequência prática: **não dá pra abrir PR entre as duas.** Qualquer
unificação é trabalho manual, depois da entrega.

### Bugs encontrados e corrigidos hoje

| # | Onde | Sintoma observado | Estado |
|---|---|---|---|
| 1 | README do `main` | Bloco da demo morria em `fatal: not a git repository` (faltava `cd autotuto`) e em `ModuleNotFoundError: matplotlib` (usava `python` do sistema, não o do venv) | corrigido, `c2c9ab6` |
| 2 | `cli._tenta_planejador` | Pedir "área do círculo" sem Ollama tocava a aula de **trapézio** inteira, com `rel.ok=True` | corrigido, `41f3b2d` |
| 3 | `cli._abre_visor` | Porta 8080 ocupada → traceback `OSError [Errno 98]` na tela | corrigido, `3c3eb66` |
| 4 | `Visor.stop()` | `shutdown()` sem `server_close()`: socket de escuta ficava aberto, porta seguia ocupada | corrigido, `3c3eb66` |
| 5 | `tocador.toca()` | `classificar(...) or "por_que"` fingia entender interrupção não classificada | corrigido, `3040d57` |
| 6 | `Visor.falar()` | Não olhava `_injecao`: teclas não interrompiam a fala; a injeção ficava acumulada e era lida como resposta de uma pergunta feita minutos depois | corrigido, `3040d57` |
| 7 | `planejador._saneia` | Gerador inexistente era podado bloco a bloco e a aula seguia sem a figura | corrigido, `675dff5` |

Detalhe do #2 (o mais grave): `planeja()` captura `URLError` e devolve
`planeja_offline()`, que é literalmente `carregar("trapezio")`. Era um atalho de
demo que virou o fallback silencioso de toda falha de LLM.

### Aberto — precisa de decisão humana

**O `main` não instala em Python < 3.13.** Reproduzido:

```
python3.11 -m venv .venv && .venv/bin/pip install -e .
→ ERROR: No matching distribution found for numpy==2.5.3
```

`pyproject.toml` do `main` tem `requires-python = ">=3.13"` e pins exatos.
Em 3.13 instala e roda (verificado). Em 3.11/3.10 falha com parede de vermelho.
Esse é o caminho **padrão** de quem clona o link do GitHub.

**`pytest` está documentado mas não declarado.** O `## Rodar` do `main` manda
`.venv/bin/pytest`, mas `pytest` não está em `dependencies` nem em
`optional-dependencies`. Depois de `pip install -e .`, o binário não existe.

Decisão adiada conscientemente: mexer no `pyproject` do `main` na véspera foi
avaliado como risco maior que o benefício. Reavaliar depois da Fase 1.

### Verificado e sadio

- Suíte do `main`: **294 passam** em 3.13 (a alegação do README é verdadeira).
- Suíte desta branch: **167 passam**.
- Demo em clone limpo: `:8080` responde 200; interrupção entra no ramo certo;
  interrupção **dentro** de um ramo troca de ramo e volta pra trilha principal.

> **Correção de 2026-10-07.** A linha acima afirmava mais do que foi verificado. O
> que eu testei foi o caso em que a interrupção **classifica** num ramo. O caso em
> que ela NÃO classifica continuava sendo ignorado em silêncio (`tocador.py`,
> `_entra_ramo`) — a mesma mentira que o commit `3040d57` dizia ter removido, um
> quadro de pilha mais fundo. Num arquivo cuja primeira regra é "só entra aqui o
> que foi executado e observado", isso era exatamente o tipo de exagero que a
> regra existe pra impedir. Corrigido na rodada abaixo.

### Ambiente

- Não existe vault Obsidian neste ambiente (procurado em `/home/user`, `/root`,
  scratchpad). A memória do projeto são os markdowns das duas árvores.
- Pythons disponíveis: 3.10, 3.11 (default), 3.12, 3.13.
- Ollama **não** está no ar — que é justamente o cenário do palco.

---

## 2026-10-07 — o que o `/code-review max` achou

Dez ângulos de revisão em cima dos commits de 20/09. Quinze descobertas, todas com
reprodução executada. O padrão que mais se repete: **eu consertei um arquivo e
deixei a cópia gêmea do mesmo bug viva noutro**.

### As duas mentiras que sobreviveram em outro arquivo

`or "por_que"` saiu do `tocador.py` e continuou vivo em
`backend/services/sessao.py`. A recusa honesta do plano offline entrou no `cli.py`
e não entrou nem no backend, nem no `demo_voz.py`, nem no `demo_texto.py`. O
backend é o caminho que o README anuncia com `docker compose up`, e o
`docker-compose.yml` sobe sem `ANTHROPIC_API_KEY` por padrão — ou seja, o caminho
documentado era, por padrão, o caminho que mente.

### O canal estruturado que nasceu morto

`Relatorio.fatais` era escrito pelo validador e lido pelo `_saneia`, mas `planeja()`
devolvia `rel2 = valida_aula(ultima)` calculado em cima da aula **já substituída**
(que é válida), então chegava sempre vazio em quem chamava. Por isso o `cli.py`
dependia de procurar a string `"plano offline"` dentro de uma frase em português:
reescrever a frase desligava a regra de ouro em silêncio, e o teste continuava verde
porque repetia a mesma string.

### Duas regressões introduzidas em 20/09

- Fazer `Visor.falar()` devolver a injeção transformou a tecla `0` — a que a tela
  manda apertar pra **responder** — em interrupção. O beat de auto-explicação era
  consumido: quem acertava ia pro ramo de quem errou e o `confirma` nunca saía.
- Cinco chamadas de `self.falar(...)` descartavam o retorno. Inofensivo enquanto
  `falar()` devolvia `None`; depois da mudança, a fala do aluno passou a ser lida e
  **destruída** (o slot `_injecao` é único, não há fila).

### Achado de pedagogia, não de código

`acertou = achou == senao or ...` dava ACERTO pra quem caísse no ramo do `senao`.
Em `eq_primeiro_grau` e `regra_de_tres` o `senao` é `por_que` — o ramo de quem NÃO
sabe —, então quem respondia "por quê?" era parabenizado e tinha a derivação pulada.
O campo `senao` estava fazendo dois trabalhos opostos: no trapézio ele aponta pro
ramo que *explica a resposta certa*; nas outras, pro ramo de quem errou. Resolvido
tornando `acerta` explícito em toda aula e normalizando acento na comparação —
sem isso "triângulo" não casava com "triangulo" e um acerto virava erro.

### Estado atual

- Suíte: **183 testes** passando (eram 167). `tsc -b` e `npm run build` limpos.
- Ensaio ao vivo refeito: apertar `0` durante a leitura da pergunta dá
  "acertou — pula a derivação (fading)", sem entrar em ramo.
- `resolve()` do CLI agora aceita frase natural ("teorema de pitágoras", "área do
  trapézio") em vez de exigir a chave exata — antes mandava pro LLM uma aula que
  está pronta no catálogo, e sem LLM no ar o aluno ouvia que não dava.

### Aberto — não mexi

- `professor/figuras/*` usa `pyplot`, que é estado global. O backend serializa o
  desenho com um lock (resolve a corrida), mas a cura real é largar o `pyplot` e
  usar `Figure` + `FigureCanvasAgg`, que não tem estado global.
- Endpoint síncrono bloqueia o event loop em até 4×200s de I/O de LLM, inclusive
  para `/api/saude`. Pede `async` + `run_in_threadpool`, ou fila.
- `SESSOES` ganhou teto e lock, mas segue em memória por processo: com
  `--workers > 1` a sessão "some" quando o request cai noutro worker. Estado
  compartilhado de verdade pede Redis.
- `main` e esta branch continuam sem ancestral comum (ver 2026-09-20).
