"""provedores.py — a tabela dos provedores de LLM que o autotuto conhece.

Só DADOS. Não importa nada de dentro do autotuto (nem config) — a seta continua
apontando só pra baixo.

A sacada: quase todo provedor de nuvem (grátis ou pago) fala a MESMA API, a
OpenAI-compatível (`POST {base}/chat/completions`). Então um único caminho em
`llm.py` (`_openai_compat`) atende todos eles — trocar de provedor é trocar uma
URL, uma chave e um nome de modelo, não escrever código novo.

Campos de cada provedor:
  base       URL até /chat/completions (sem a barra final)
  chave_env  variável de ambiente onde mora a chave
  modelo     modelo default (o que a gente usa se AUTOTUTO_MODELO não for setado)
  json_nativo  manda `response_format: json_object`? (nem todo provedor aceita)
  limite     o que o tier grátis dá, em texto — pra `python -m autotuto.chaves` mostrar
  onde       de onde se tira a chave
  cadastro   o que o cadastro exige (importa: "sem cartão" é requisito do projeto)

ATENÇÃO: limite de tier grátis e nome de modelo mudam TODO MÊS. O que está aqui
foi conferido em 2026-09-14 (ver docs/PROVEDORES.md). Se um modelo sumir, o
provedor devolve 404/400 — troque com AUTOTUTO_MODELO em vez de editar aqui.
"""

PROVEDORES: dict[str, dict] = {
    "groq": {
        "base": "https://api.groq.com/openai/v1",
        "chave_env": "GROQ_API_KEY",
        "modelo": "llama-3.3-70b-versatile",
        "json_nativo": True,
        "limite": "30 req/min, 1.000 req/dia — o mais rápido de todos",
        "onde": "https://console.groq.com/keys",
        "cadastro": "sem cartão",
    },
    "openrouter": {
        "base": "https://openrouter.ai/api/v1",
        "chave_env": "OPENROUTER_API_KEY",
        "modelo": "meta-llama/llama-3.3-70b-instruct:free",
        "json_nativo": True,
        "limite": "20 req/min, 50 req/dia — 1 chave, dezenas de modelos",
        "onde": "https://openrouter.ai/keys",
        "cadastro": "sem cartão",
    },
    "nvidia": {
        "base": "https://integrate.api.nvidia.com/v1",
        "chave_env": "NVIDIA_API_KEY",
        "modelo": "meta/llama-3.3-70b-instruct",
        "json_nativo": False,
        "limite": "créditos grátis, 120+ modelos abertos",
        "onde": "https://build.nvidia.com",
        "cadastro": "sem cartão",
    },
    "github": {
        "base": "https://models.inference.ai.azure.com",
        "chave_env": "GITHUB_TOKEN",
        "modelo": "gpt-4o-mini",
        "json_nativo": True,
        "limite": "grátis, limite diário varia por modelo",
        "onde": "https://github.com/settings/tokens (token clássico, sem escopo especial)",
        "cadastro": "conta GitHub",
    },
    "gemini": {
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
        "chave_env": "GEMINI_API_KEY",
        "modelo": "gemini-2.0-flash",
        "json_nativo": True,
        "limite": "a cota grátis mais generosa entre os grandes",
        "onde": "https://aistudio.google.com/apikey",
        "cadastro": "sem cartão",
    },
    # Curinga: qualquer endpoint OpenAI-compatível que não esteja na lista
    # (vLLM/LM Studio/llama.cpp local, Together, DeepInfra, Cloudflare...).
    # Precisa setar AUTOTUTO_BASE_URL e AUTOTUTO_MODELO na mão.
    "openai": {
        "base": "https://api.openai.com/v1",
        "chave_env": "OPENAI_API_KEY",
        "modelo": "gpt-4o-mini",
        "json_nativo": True,
        "limite": "pago — ou aponte AUTOTUTO_BASE_URL pro seu endpoint",
        "onde": "https://platform.openai.com/api-keys",
        "cadastro": "cartão",
    },
}

# Provedores que NÃO falam OpenAI-compatível — cada um tem seu caminho em llm.py.
NATIVOS = ("ollama", "claude")


def conhecido(nome: str) -> bool:
    return nome in PROVEDORES or nome in NATIVOS


def nomes() -> list[str]:
    """Todos os provedores aceitos em AUTOTUTO_LLM, na ordem de recomendação."""
    return [*NATIVOS, *PROVEDORES]
