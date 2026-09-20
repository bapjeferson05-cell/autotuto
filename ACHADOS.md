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

### Ambiente

- Não existe vault Obsidian neste ambiente (procurado em `/home/user`, `/root`,
  scratchpad). A memória do projeto são os markdowns das duas árvores.
- Pythons disponíveis: 3.10, 3.11 (default), 3.12, 3.13.
- Ollama **não** está no ar — que é justamente o cenário do palco.
