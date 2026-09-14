# Provedores de LLM — quais existem, quais são grátis de verdade

*Levantamento de 2026-09-14. **Tier grátis muda todo mês** — trate como ponto de
partida, não como verdade eterna. Se um modelo sumir, o provedor devolve 400/404:
troque com `AUTOTUTO_MODELO` no `.env`, sem mexer em código.*

## Por que isso é só um arquivo de dados

Quase todo provedor de nuvem fala a **mesma API**, a OpenAI-compatível
(`POST {base}/chat/completions`). Então o autotuto tem **um caminho só**
(`llm._openai_compat`) e uma tabela (`autotuto/provedores.py`). Adicionar um
provedor novo = três linhas na tabela, zero código.

Só `ollama` (local) e `claude` têm caminho próprio, porque a API deles é outra.

## Configurar em 15 segundos

```bash
python -m autotuto.chaves          # menu: escolhe, cola a chave, pronto
python -m autotuto.chaves groq     # ou já direto no provedor
```

Grava num `.env` com permissão `600` (só você lê) — o `config.py` carrega
sozinho. O `.env` está no `.gitignore`; **nunca** commite chave.

## A tabela

| provedor | cadastro | tier grátis (set/2026) | onde pegar a chave |
|---|---|---|---|
| **groq** | sem cartão | 30 req/min, ~1.000 req/dia — **o mais rápido** | [console.groq.com/keys](https://console.groq.com/keys) |
| **gemini** | sem cartão | a cota grátis mais generosa entre os grandes | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **openrouter** | sem cartão | 20 req/min, 50 req/dia (1.000/dia com US$10 de crédito) — **uma chave, dezenas de modelos** | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **github** | só conta GitHub | grátis, limite diário por modelo | [github.com/settings/tokens](https://github.com/settings/tokens) |
| **nvidia** | sem cartão | créditos grátis, 120+ modelos abertos | [build.nvidia.com](https://build.nvidia.com) |
| **openai** | **cartão** | pago — ou aponte `AUTOTUTO_BASE_URL` pro seu endpoint | [platform.openai.com](https://platform.openai.com/api-keys) |
| **ollama** | — | local, 100% grátis, mas pede RAM (ver "Perfis de hardware" no README) | — |

### Recomendação pro autotuto

1. **groq** — o planejador espera resposta em ~45s; velocidade é o que mais
   importa aqui, e groq é o mais rápido do mercado grátis.
2. **gemini** — se bater no limite diário do groq, a cota do Gemini é maior.
3. **openrouter** — pra *testar vários modelos* sem criar conta em cada lugar:
   uma chave só, e o nome do modelo escolhe o provedor por trás.

### Armadilhas (o "free" que não é free)

- **Cerebras** virou trial com cartão em jul/2026 — era o mais generoso, hoje
  não entra na lista de "free real".
- Vários serviços anunciam "grátis" mas pedem cartão no cadastro ou expiram em
  N dias. A coluna **cadastro** acima existe por isso: `sem cartão` foi o
  critério de entrada na tabela.
- Limite por **dia** costuma doer mais que o por minuto: uma aula do autotuto
  gasta 1 chamada do planejador + 1 por interrupção que a regex não pegou.

## Endpoint próprio (vLLM, LM Studio, llama.cpp)

Qualquer servidor que fale OpenAI-compatível entra sem código novo:

```bash
AUTOTUTO_LLM=openai
AUTOTUTO_BASE_URL=http://localhost:8000/v1
AUTOTUTO_MODELO=o-nome-do-seu-modelo
OPENAI_API_KEY=qualquer-coisa    # a maioria desses servidores ignora a chave
```

## TTS na nuvem — ainda NÃO implementado

Hoje o TTS é **local** (Piper) e é o certo pro projeto: zero latência de rede,
zero custo, funciona offline. O levantamento abaixo fica registrado pra quando
fizer sentido ter um fallback de nuvem (máquina de 4GB que não aguenta o Piper):

| serviço | tier grátis (set/2026) | pt-BR? |
|---|---|---|
| **ElevenLabs** | 10.000 créditos/mês, permanente, sem cartão | sim |
| **Groq (Orpheus/PlayAI)** | dentro do tier grátis do groq, ~100 char/s | verificar |
| SpeechGen / Maestra / ttsMP3 | grátis por caractere, mas são **site**, não API estável | sim |

Nenhum deles entrou no código ainda — TTS de nuvem só vale a pena no perfil
`leve`, e isso depende de decidir o que fazer quando a cota acaba no meio de uma
aula (a regra "nunca mentir" vale aqui também: não dá pra fingir que falou).

## Próximo passo natural: bateria de testes

Com vários provedores plugados, dá pra medir qual serve pro professor:
tempo até o primeiro plano válido, quantas vezes o JSON volta quebrado, e se o
modelo escolhe o método certo. Isso ainda **não existe** — quando existir, as
recomendações acima deixam de ser "o que a internet diz" e viram "o que a gente
mediu".

## Fontes

- [Free LLM API in 2026: 13 Options Ranked — OpenRouter](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)
- [5 Free LLM API Providers You Can Use in 2026 — KDnuggets](https://www.kdnuggets.com/5-free-llm-api-providers-you-can-use-in-2026)
- [Free LLM API 2026: 17 Tested, 7 Need No Card](https://klymentiev.com/blog/free-llm-api)
- [Groq Free Tier Limits 2026 — TokenMix](https://tokenmix.ai/blog/groq-free-tier-limits-2026)
- [Cerebras API Key: Rate Limits 2026 — TokenMix](https://tokenmix.ai/blog/cerebras-api-key-rate-limits-free-tier-2026)
- [ElevenLabs Free Tier 2026: Character Limit Tested](https://nexodatech.com/elevenlabs-free-tier-2026-character-limit-tested/)
- [awesome-free-llm-apis (GitHub)](https://github.com/mnfst/awesome-free-llm-apis)
