import os
from pathlib import Path


def _carrega_env(caminho=".env") -> None:
    """Lê um .env simples (CHAVE=valor por linha) pro os.environ, se existir.

    Sem python-dotenv: são 6 linhas e a regra do projeto é 'deps exatas'. O que
    já está no ambiente GANHA do arquivo — exportar na mão continua mandando.
    É o que faz `python -m autotuto.chaves` valer: ele escreve aqui, e pronto."""
    try:
        texto = Path(caminho).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        os.environ.setdefault(chave.strip(), valor.strip().strip("'\""))


_carrega_env()

env = lambda k, d: os.environ.get(k, d)

# LLM
LLM_PROVEDOR   = env("AUTOTUTO_LLM", "ollama")      # ollama | claude | groq |
                                                     # openrouter | nvidia | github |
                                                     # gemini | openai (ver provedores.py)
LLM_MODELO     = env("AUTOTUTO_MODELO", "qwen2.5:7b")  # modelo do ollama
LLM_MODELO_NUVEM = env("AUTOTUTO_MODELO", "")       # mesma env var: vazio = usa o
                                                     # default do provedor de nuvem
LLM_BASE_URL   = env("AUTOTUTO_BASE_URL", "")       # vazio = base do provedor; setar
                                                     # pra apontar num endpoint próprio
                                                     # (vLLM, LM Studio, llama.cpp...)
LLM_CLAUDE     = "claude-sonnet-5"
CEREBRO_TIMEOUT_S = 8.0                              # LLM curto da interrupção
AVALIADOR_TIMEOUT_S = 8.0                            # LLM curto da avaliação semântica de resposta
PLANEJADOR_TIMEOUT_S = 45.0  # medido ao vivo NO CAMINHO CONHECIDO (few-shot dirigido
                              # bate, ~35-45s): se não respondeu nisso, tá travado —
                              # melhor cair no fallback honesto do que esperar minutos.
PLANEJADOR_TIMEOUT_NOVO_S = 100.0  # autópsia de 2026-09-12: SEM few-shot dirigido (tópico
                              # nunca visto) o modelo pensa mais e passa dos 45s — chegou
                              # a ~90s num caso real. Não pode penalizar o caminho feliz
                              # com esse teto maior, então só entra quando não há few-shot.

# Voz
STT_MODELO     = env("AUTOTUTO_STT", "base")         # tiny | base | small
STT_DEVICE     = "cpu"
TTS_VOICE      = env("AUTOTUTO_TTS_VOICE", os.path.expanduser("~/jarvis/models/piper/pt_BR-faber-medium.onnx"))
STT_CACHE      = env("AUTOTUTO_STT_CACHE", os.path.expanduser("~/jarvis/models/faster-whisper"))
BARGE_IN       = env("AUTOTUTO_BARGE_IN", "0") == "1" # mic interrompe? padrão NÃO
FALA_TIMEOUT_S = 12.0                                # cão-de-guarda do Piper
GRAVA_RESTO_S  = 2.0                                 # quanto grava após o corte
SILENCIO_MS    = 400                                 # silêncio que fecha a gravação
TTS_LENGTH_SCALE = 1.0
TTS_NOISE_SCALE = 0.667                              # textura da voz (default típico do Piper)
TTS_NOISE_W_SCALE = 0.8                              # variação do timing dos fonemas
TTS_JITTER = 0.08                                    # +/- sorteado por fala (evita soar sempre igual)

# Ritmo / visor
SETTLE_S       = 0.4                                 # figura aparece ANTES da fala
RITMO_S_POR_CHAR = 0.045                             # "fala" sem TTS (modo texto)
PAUSA = {"curta": 0.35, "media": 0.9, "longa": 1.8, None: 0.55}
VISOR_PORTA    = 8080
VISOR_POLL_MS  = 120

# Lousa (tema)
COR_FUNDO="#0E2A22"; COR_GIZ="#EAEAEA"; COR_FRACO="#8FA79C"
COR_DESTAQUE="#F2B134"; COR_AZUL="#5AB1E0"; COR_VERDE="#7BD88F"
# Opacidade do preenchimento. Dois níveis porque o preenchimento tem dois papéis:
#   DISCRETO  só diz "esta é a figura de que estou falando" (polígono, círculo).
#   PINTADO   É a resposta — a fatia da fração. Em 0.12 o aluno não distinguia
#             as 3 fatias pintadas da 1 vazia: o desenho não dizia 3/4.
ALPHA_FIGURA  = 0.12
ALPHA_PINTADO = 0.55
