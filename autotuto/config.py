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
PLANEJADOR_TIMEOUT_S = 100.0  # teto ÚNICO. Já foram dois (45s no caminho com few-shot
                              # dirigido, 100s sem), de quando "sem pista" queria dizer
                              # "sem exemplo nenhum". Hoje todo problema leva exemplo e o
                              # dirigido é o de prompt MAIOR: a bateria de 2026-09-15
                              # falhou em 3 tópicos, todos com aula de ouro, todos em
                              # 45.0s cravados, enquanto os genéricos passavam em ~20s.
                              # Teto generoso não custa nada quando o modelo é rápido
                              # (ele responde antes) e salva a aula quando não é.

# Voz
STT_MODELO     = env("AUTOTUTO_STT", "base")         # tiny | base | small
STT_DEVICE     = "cpu"
# A SPEC lista "dependência do jarvis arrastada" como pecado do código velho, e o
# README promete "zero jarvis" — mas o caminho PADRÃO dos modelos continuava
# apontando pra dentro do ~/jarvis. Quem clonasse do zero não tinha essa pasta e
# só descobria isso com um stack trace do Piper. Agora o padrão é a pasta do
# próprio autotuto; o caminho antigo segue valendo se ainda existir na máquina,
# pra não quebrar quem já tem os modelos baixados lá.
_VOZ_NOVA  = os.path.expanduser("~/.local/share/autotuto/vozes/pt_BR-faber-medium.onnx")
_VOZ_VELHA = os.path.expanduser("~/jarvis/models/piper/pt_BR-faber-medium.onnx")
_STT_NOVO  = os.path.expanduser("~/.local/share/autotuto/faster-whisper")
_STT_VELHO = os.path.expanduser("~/jarvis/models/faster-whisper")

TTS_VOICE      = env("AUTOTUTO_TTS_VOICE",
                     _VOZ_VELHA if os.path.exists(_VOZ_VELHA) else _VOZ_NOVA)
STT_CACHE      = env("AUTOTUTO_STT_CACHE",
                     _STT_VELHO if os.path.isdir(_STT_VELHO) else _STT_NOVO)
# Vozes pt-BR do Piper: faber, cadu, edresson, jeff (medium). Baixar com
#     python -m piper.download_voices pt_BR-faber-medium
COMO_BAIXAR_VOZ = ("python -m piper.download_voices pt_BR-faber-medium "
                   "--download-dir ~/.local/share/autotuto/vozes")
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
# Ritmo dos passos de uma conta quando NÃO há `diz_passos` narrando cada um:
# o passo precisa ficar tempo suficiente na lousa pro aluno ler antes do próximo.
# O último é mais curto porque já é o resultado — a pausa dele vem do `espera`.
PASSO_S        = 1.1
PASSO_FINAL_S  = 0.7
# Intervalos de espera ativa (visor servindo frames, voz drenando a thread).
# Curtos de propósito: são o piso de latência entre o aluno agir e o sistema ver.
TICK_S         = 0.05

# Lousa (tema)
COR_FUNDO="#0E2A22"; COR_GIZ="#EAEAEA"; COR_FRACO="#8FA79C"
COR_DESTAQUE="#F2B134"; COR_AZUL="#5AB1E0"; COR_VERDE="#7BD88F"
# Opacidade do preenchimento. Dois níveis porque o preenchimento tem dois papéis:
#   DISCRETO  só diz "esta é a figura de que estou falando" (polígono, círculo).
#   PINTADO   É a resposta — a fatia da fração. Em 0.12 o aluno não distinguia
#             as 3 fatias pintadas da 1 vazia: o desenho não dizia 3/4.
# Teto de marcas numa reta numérica. Não é estética: `reta_numerica(0, 1000000)`
# — que um LLM escreve sem pensar — desenharia um milhão de traços e travaria a
# aula. E como o validador agora DESENHA pra validar, travaria o planejador
# antes mesmo de o aluno ouvir a primeira frase. Acima disso não é figura de
# aula nenhuma: falha rápido e o modelo corrige.
MAX_MARCAS_RETA = 60

# Raio do arco que marca um ângulo. Vira knob porque DOIS ângulos vizinhos
# (o 43° e o 47° que juntos fecham o canto reto) desenhados no mesmo raio
# viram um arco contínuo só — o aluno vê um ângulo de 90°, não dois. Cada
# ângulo pode pedir o seu com "raio" no spec.
RAIO_ARCO     = 0.6

# A interrupção é a razão de existir do projeto — e o aluno não tem como
# adivinhar que ela existe. Relato de uso real: a pessoa falou em voz alta, o
# professor seguiu por cima (BARGE_IN vem 0 por padrão, o mic não interrompe) e
# a experiência virou "mais um vídeo, só que ao vivo". README não resolve: quem
# está revisando às onze da noite não lê README. Então o professor CONVIDA, em
# voz alta, uma vez, antes da primeira aula.
CONVITE_INTERRUPCAO = (
    "Antes de começar: pode me interromper quando quiser, e é pra isso mesmo. "
    "Aperta 1 se quiser saber por quê, 2 se eu passar rápido demais, "
    "4 pra saber de onde a fórmula veio — ou escreve na caixa. Eu paro na hora.")

ALPHA_FIGURA  = 0.12
ALPHA_PINTADO = 0.55
