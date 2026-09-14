import json
import os
import urllib.request
import urllib.error

from autotuto import config, provedores

_SO_JSON = "\n\nResponda APENAS com o objeto JSON, sem cercas de código."

# Get Ollama host from config or environment
OLLAMA_HOST = getattr(config, "OLLAMA_HOST", os.environ.get("OLLAMA_HOST", "http://localhost:11434"))

# Export module-level references for monkeypatching in tests
LLM_PROVEDOR = config.LLM_PROVEDOR


def _ollama(mensagens, timeout, json_mode, esquema=None):
    """Call Ollama API with messages."""
    url = f"{OLLAMA_HOST}/api/chat"

    body = {
        "model": config.LLM_MODELO,
        "messages": mensagens,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_ctx": 8192,
        },
    }

    if json_mode:
        # "json" solto garante que SAI um JSON — e só. Com um JSON Schema aqui,
        # o ollama (>=0.3.0) força a FORMA no próprio decoder: `blocos` sai
        # lista, beat sai objeto, `senao` sai texto. Deixa de ser "pede, recebe
        # torto, manda corrigir" e passa a não ter como vir torto.
        body["format"] = esquema if esquema else "json"

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        response_data = json.loads(resp.read().decode("utf-8"))

    return response_data["message"]["content"]


def _claude(mensagens, timeout, json_mode):
    """Call Claude API with messages."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ConnectionError("ANTHROPIC_API_KEY not set")

    # Extract system messages and join them
    system_parts = []
    other_messages = []

    for msg in mensagens:
        if msg["role"] == "system":
            system_parts.append(msg["content"])
        else:
            other_messages.append(msg)

    system_text = "\n".join(system_parts)

    # Add JSON mode instruction to system if needed
    if json_mode:
        system_text += "\n\nResponda APENAS com o objeto JSON, sem cercas de código."

    body = {
        "model": config.LLM_CLAUDE,
        "max_tokens": 4096,
        "temperature": 0.3,
        "system": system_text,
        "messages": other_messages,
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        response_data = json.loads(resp.read().decode("utf-8"))

    # Concatenate all text blocks from content
    text_parts = []
    for content_block in response_data.get("content", []):
        if content_block.get("type") == "text":
            text_parts.append(content_block["text"])

    return "".join(text_parts)


def _openai_compat(mensagens, timeout, json_mode, provedor):
    """Qualquer provedor que fale a API OpenAI (POST {base}/chat/completions).

    É o caminho de Groq, OpenRouter, NVIDIA, GitHub Models, Gemini e de qualquer
    endpoint próprio (vLLM/LM Studio) via AUTOTUTO_BASE_URL. Um caminho só, porque
    a API é a mesma — o que muda é base, chave e nome do modelo."""
    info = provedores.PROVEDORES[provedor]
    chave = os.environ.get(info["chave_env"])
    if not chave:
        raise ConnectionError(
            f"{info['chave_env']} não está definida (provedor '{provedor}'). "
            f"Pega a chave em {info['onde']} — ou roda: python -m autotuto.chaves")

    base = (config.LLM_BASE_URL or info["base"]).rstrip("/")
    modelo = config.LLM_MODELO_NUVEM or info["modelo"]

    msgs = [dict(m) for m in mensagens]
    if json_mode:
        # Instrução no system serve em TODO provedor; o response_format nativo é
        # bônus só pra quem aceita (mandar pra quem não aceita vira erro 400).
        sistema = next((m for m in msgs if m["role"] == "system"), None)
        if sistema:
            sistema["content"] += _SO_JSON
        else:
            msgs.insert(0, {"role": "system", "content": _SO_JSON.strip()})

    body = {"model": modelo, "messages": msgs, "temperature": 0.2}
    if json_mode and info["json_nativo"]:
        body["response_format"] = {"type": "json_object"}

    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {chave}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dados = json.loads(resp.read().decode("utf-8"))

    return dados["choices"][0]["message"]["content"]


def perguntar(mensagens, *, timeout, json_mode=True, esquema=None):
    """Manda as mensagens pro provedor configurado e devolve o texto da resposta.

    Provedor vem de AUTOTUTO_LLM (ver provedores.py): 'ollama' (local, default) e
    'claude' têm caminho próprio; o resto vai pelo caminho OpenAI-compatível.

    `esquema`: JSON Schema pra constrained decoding. Quem chama é que conhece a
    forma que quer (o planejador passa `schema.esquema_json()`) — assim este
    módulo não precisa saber o que é uma Aula. Hoje só o caminho do ollama usa:
    os provedores de nuvem têm `response_format: json_schema`, mas o suporte
    varia de um pro outro e eu não tenho como testar cada um daqui. Nos outros
    o parâmetro é ignorado, e o `json_mode` de sempre continua valendo."""
    provedor = LLM_PROVEDOR

    if provedor == "claude":
        return _claude(mensagens, timeout, json_mode)
    if provedor in provedores.PROVEDORES:
        return _openai_compat(mensagens, timeout, json_mode, provedor)
    return _ollama(mensagens, timeout, json_mode, esquema)
