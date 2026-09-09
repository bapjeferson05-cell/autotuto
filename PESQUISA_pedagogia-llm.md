# Treinar o cérebro pra "matemática de gente", não "matemática de máquina"

*2026-09-09. O problema: LLMs de matemática são treinados em competição, prova formal,
GSM8K com solução seca, e código. Não em "como um professor paciente explica área do
trapézio pra um aluno confuso de 12 anos, e adapta quando ele diz 'não entendi'".
Essa é a lacuna.*

---

## O que a nossa própria run mostrou (5 problemas via hermes3:8b)

| problema | escolha do modelo | veredito |
|---|---|---|
| área do círculo r=5 | `parte_circulo` + `area_circulo` c/ passos | ✅ |
| Bhaskara x²−5x+6 | parábola c/ raízes + `bhaskara` | ✅ figura; ❌ narrou "raízes 1 e 6" (são 2 e 3) |
| área do trapézio | `quadrilatero` + `area_trapezio` | ✅ |
| hexágono regular | `poligono_regular(6)` | ✅ figura; pedagogia circular |
| **escada 5 m, base 3 m** | **`porcentagem(parte=5, todo=3, pct=1)`** | ❌ **é Pitágoras (h=4)** |

O validador deixou o último passar porque `porcentagem(5,3,1)` é *estruturalmente*
válido e devolve número finito. **A cola está pronta. O gargalo é o cérebro** — e não é
só pedagogia, é seleção de método.

---

## O reframe que muda tudo — LearnLM (Google)

[**LearnLM: Improving Gemini for Learning**](https://arxiv.org/abs/2412.16429) (arXiv 2412.16429).
Não se treina um modelo pra "ser socrático". Trata-se pedagogia como **instrução que o
modelo segue**: os atributos pedagógicos vão no *system prompt* (no nosso caso, no campo
`diz`/futuro `purpose` do bloco) e o modelo aprende a obedecê-los. Isso evita travar o
modelo numa única definição de pedagogia.

Resultados: educadores preferiram LearnLM **+11% sobre Claude 3.5 Sonnet, +31% sobre
GPT-4o**; 0,1% de erro factual; alunos que tiveram sessão curta com LearnLM ficaram 5,5
p.p. mais propensos a resolver problemas novos. Agora no Gemini 2.5, disponível no AI Studio.

**Consequência pro projeto:** a arquitetura de 3 camadas (pedagógica / matemática /
visual) já É isso. Não precisamos de um modelo que *seja* tutor — precisamos de um que
(a) escolha o método certo, (b) preencha o schema, (c) escreva narração decente.

---

## Datasets de tutoria real ("matemática de gente")

| recurso | o que é | serve pra | licença |
|---|---|---|---|
| [**MathDial**](https://github.com/eth-nlped/mathdial) — EMNLP 2023, ETH ⭐ | ~2.861 diálogos professor↔aluno, ancorados em GSM8K, com **"teacher moves"** anotados (focar / sondar / contar) e personas de aluno com erro | minerar *como* um tutor fala, *quando* pergunta vs. conta | acadêmica (CC BY) |
| [**SocraticMATH**](https://github.com/ECNU-ICALK/SocraticMath) — CIKM 2024, ECNU | ~6.846 diálogos socráticos, 513 pontos de conhecimento, estrutura Revisão→Heurística→Correção→Resumo, base Qwen1.5-7B | fine-tune socrático | **CC BY-NC** (trava produto pago; kit acadêmico ok) |
| [**SocraticLM / SocraTeach**](https://github.com/Ljyustc/SocraticLM) — NeurIPS 2024 Spotlight, USTC | 35K diálogos sintéticos, pipeline "Reitor-Professor-Aluno" | volume pra fine-tune | ver repo |
| [**Khan Academy Tutoring Dataset**](https://blog.khanacademy.org/introducing-a-new-dataset-to-further-the-field-of-ai-research/) | 188 conversas **reais** Khanmigo↔aluno, anonimizadas, fundamental→cálculo | **avaliar** (pequeno demais pra treinar); foco em "pegar o erro do aluno" | pesquisa |

## Benchmarks — como medir se o tutor é bom

- [**MathTutorBench**](https://github.com/eth-lre/mathtutorbench) — ETH/TU Darmstadt, EMNLP 2025 Oral.
  3 habilidades × 7 tarefas, com um *reward model* que distingue resposta de professor
  experiente vs. novato. **Achado central: "saber resolver NÃO se traduz em saber ensinar;
  perícia e pedagogia são um trade-off"** e **"tutoria fica mais difícil em diálogos
  longos, onde estratégias simples de pergunta falham"** — exatamente a parte que o nosso
  ciclo de interrupção/retomada ataca.
- [**MMTutorBench**](https://arxiv.org/abs/2510.23477) — tutoria de matemática **multimodal**
  (com imagens), out/2025. Relevante porque o professor é visual.

## Métodos de alinhamento pedagógico

- [**PEARL**](https://arxiv.org/abs/2605.29582) — tutores socráticos via RL pedagogicamente alinhado.
- [**Towards Pedagogically Aligned LLM Tutors for Math Mistake Remediation**](https://arxiv.org/abs/2606.21502).
- [**Training LLM-based Tutors to Improve Student Learning Outcomes**](https://arxiv.org/abs/2503.06424).

## O que NÃO serve (o ChatGPT misturou)

**MAmmoTH / MathInstruct / OpenMathInstruct** são pra **resolver** (Chain-of-Thought +
Program-of-Thought), não pra ensinar — o `calc.py` já cobre isso. **AlphaGeometry** é
prova de olimpíada. Ignorar.

---

## Os 3 caminhos, na ordem que faríamos

**1. Cérebro do demo = API (Claude ou Gemini/LearnLM).** `PROJETO.md §6` já dizia. Já
implementado: `PROF_LLM=claude` no `planejador.py`. A qualidade da explicação é o que
impressiona o júri.

**2. Destilação pro kit open-source ("roda em qualquer PC").** Modelo forte gera
**200 planos no NOSSO schema** (Ciclo do Trapézio + variações), a gente filtra os que
validam **e** que um humano aprova → QLoRA no hermes3:8b. É "matemática de gente **no
nosso formato**" — muito mais eficaz que treinar em diálogo socrático genérico, porque o
dataset já sai como `blocos`. RTX 3050 6 GB: [Unsloth](https://github.com/unslothai/unsloth)
QLoRA 4-bit cabe um 7-8B apertado, ou A100 alugada (RunPod/Vast, ~US$1,50/h × 3h).

**3. Testar `mistral-small:24b` (já na máquina) no pipeline.** ~3× o hermes3 em seleção
de método e pedagogia. Mais lento, mas o planejamento é offline — só a fala precisa ser
rápida. Shootout no `exemplos.py` igual ao dos outros LLMs.

---

## Maior alavanca ANTES de qualquer fine-tune

**As aulas de ouro** (`professor/aulas.py`). Escrever 5–10 à mão, com a pedagogia que a
gente quer, no schema — e usá-las como few-shot no prompt. Já feito pro trapézio: um 8B
com esse exemplo no prompt erra bem menos método. Puxar o fraseado do MathDial (as
"teacher moves"). Próximas: área do triângulo, Pitágoras, equação do 1º grau, %.
