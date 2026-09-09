# Como o ser humano ensina matemática visual — e o que isso pede do professor

*2026-09-09. Pesquisa pra alinhar o renderizador + a pedagogia com o que professor
de verdade faz na lousa. Não é opinião: são cinco resultados de pesquisa educacional
com décadas de replicação.*

---

## Os 5 princípios (e o que cada um manda fazer no código)

### 1. Worked examples — exemplo resolvido antes de mandar resolver
[Cognitive Load Theory, Sweller.](https://researchschool.org.uk/clips-from-the-classroom/maths/using-worked-examples-to-reduce-cognitive-load-in-maths)
No começo do aprendizado, **ver um exemplo 100% resolvido, passo a passo, com cada
passo explicado**, ensina mais que tentar resolver sozinho. O exemplo tira a carga
da memória de trabalho e deixa o aluno focar no *padrão*. O professor modela o
**raciocínio de especialista** e destaca *por que* aquele método.

→ **É o formato `beats`.** Um passo por beat, figura + fala juntas. Já fazemos.
→ **Ajuste:** narrar a DECISÃO, não só o passo. "Divide por dois" ✗ →
   "divide por dois **porque a gente quer a média das duas bases**" ✓. O `diz` de
   cada beat tem que carregar o motivo.

### 2. Concreteness fading — concreto → figura → símbolo, nessa ordem
[Bruner (enativo→icônico→simbólico); Fyfe et al.](https://link.springer.com/article/10.1007/s10648-014-9249-3)
Começa no concreto (um terreno de verdade), passa por uma representação que **vai
apagando o concreto** (dois retângulos lado a lado), e termina no abstrato (a
fórmula). **Concreto-antes-de-abstrato melhora a transferência** — o aluno resolve
problemas novos melhor.

→ **A aula de ouro do trapézio já é exatamente isso:** terreno → duas bases
   destacadas → dois retângulos (a média) → `A = (B+b)·h/2`. Manter esse arco em
   toda aula nova. O ramo `por_que_div_2` é o estágio "icônico" — não cortar.

### 3. Dual coding — ver e ouvir ao mesmo tempo, integrado
[Paivio; Caviglioli.](https://thirdspacelearning.com/blog/dual-coding/)
Palavra + imagem processadas em canais separados da memória. Junto e sincronizado
ensina mais que texto sozinho ou imagem sozinha. Mas **separados no tempo ou no
espaço, atrapalham** (split-attention effect).

→ **O `Tocador` já fala a figura enquanto ela aparece.** Cuidado: NÃO pôr LaTeX no
   `diz` (é pra falar) e NÃO deixar a figura mudar enquanto a fala é sobre outra.
   Um beat = uma ideia = uma figura = uma frase.

### 4. Self-explanation effect — o ganho está no ALUNO explicando
[Chi et al.](https://www.sciencedirect.com/science/article/pii/S0732312324000695)
O maior salto de compreensão vem quando o **aluno** responde "por quê?" e "como?",
não quando ele vê mais exemplos. Verbalizar força ele a perceber o que ainda não
entendeu. Mas tem que ser **a pergunta certa** na hora certa.

→ **Os `ramos` já respondem "por quê".** Falta o professor às vezes **devolver a
   pergunta antes de responder**: "o que você acha que acontece se a base de cima
   encolher até zero?" — e esperar. Um novo tipo de beat: `pergunta` (fala + espera
   longa + só depois o ramo). Isso é o item mais alto da lista.

### 5. Think-aloud — narrar as decisões, não só as ações
["Giving instruction, not instructions."](https://texasgateway.org/resource/thinking-expert-teacher-modeling-and-thinking-aloud)
Professor bom fala em voz alta *as escolhas* que faz e *o porquê* delas enquanto
resolve — mostra o processo mental, não só o resultado.

→ Reforça o item 1. O `diz` de cada beat = pensamento em voz alta.

---

## Convenções de desenho de geometria (o renderizador já faz, com nome)

[MathBitsNotebook](https://mathbitsnotebook.com/Geometry/BasicTerms/BTnotation2.html) ·
[BossMaths G1e](https://bossmaths.com/g1e/) · [Hatch mark (Wikipedia)](https://en.wikipedia.org/wiki/Hatch_mark)

| convenção | o que significa | primitiva |
|---|---|---|
| tracinho no lado (`\|`) | lados de mesmo comprimento | `marcas: tipo "cong"` |
| dois/três tracinhos | um SEGUNDO/TERCEIRO par de lados iguais | `marcas: n: 2` |
| arco no ângulo | ângulos de mesma medida | `angulos: n: 1` |
| arcos duplos | segundo par de ângulos iguais | `angulos: n: 2` |
| quadradinho no vértice | ângulo reto (90°) | `angulos: reto: true` |
| setinha no lado (`›`) | lados paralelos | `marcas: tipo "par"` |
| cota `\|←— 18 —→\|` | medida de um comprimento | `cotas` |

Regras humanas que valem seguir:
- **O aluno desenha e rotula ele mesmo** sempre que dá — ativa o raciocínio
  espacial. O professor não força, mas pode pausar e pedir ("desenha aí o
  trapézio antes de eu continuar").
- **Unidade e contexto reais** ("18 metros", "o terreno", "a escada") — não
  "figura genérica". Já fazemos nas aulas de ouro.
- Triângulo: vértices em MAIÚSCULA (A, B, C), lados na minúscula oposta (a = BC).
- Cor com função, não decoração: uma cor por papel (base, altura, resultado) e
  a mesma cor pro mesmo papel a aula inteira. A paleta lousa já separa
  destaque/azul/verde/verm.

---

## Onde o projeto já acerta / o que mudar

**Já acerta:** o arco concreto→ícone→símbolo (trapézio), beats como worked example,
figura+fala sincronizadas, ramos como re-explicação adaptativa, as convenções de
marcação no `primitivas`.

**Mudar, em ordem de impacto:**
1. **Beat `pergunta`** — professor devolve a pergunta e ESPERA o aluno tentar
   explicar, antes de dar a resposta no ramo. (self-explanation)
2. **`mostra_passos` um de cada vez** — hoje despeja os passos do `calc` juntos.
   Melhor: um passo, pausa curta, próximo. (worked example + carga)
3. **`diz` narra a decisão** — "divide por dois porque é a média", não "divide por
   dois". Revisar as aulas de ouro com esse filtro.
4. **Fading pra quem já sabe** — se o aluno acerta rápido, PULAR a derivação
   completa. Worked example vira estorvo depois que você aprendeu (expertise
   reversal). O `EstadoAula` já tem o histórico pra decidir isso.
