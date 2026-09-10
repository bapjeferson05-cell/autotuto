import json
import os
import urllib.request
import urllib.error

from autotuto import config

# Get Ollama host from config or environment
OLLAMA_HOST = getattr(config, "OLLAMA_HOST", os.environ.get("OLLAMA_HOST", "http://localhost:11434"))

# Export module-level references for monkeypatching in tests
LLM_PROVEDOR = config.LLM_PROVEDOR


def _ollama(mensagens, timeout, json_mode):
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
        body["format"] = "json"

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


def perguntar(mensagens, *, timeout, json_mode=True):
    """
    Ask an LLM (Ollama or Claude) a question.

    Args:
        mensagens: List of message dicts with role and content
        timeout: Timeout in seconds for the HTTP request
        json_mode: If True, request JSON response format

    Returns:
        String response from the LLM
    """
    provedor = LLM_PROVEDOR

    if provedor == "claude":
        return _claude(mensagens, timeout, json_mode)
    else:  # default to ollama
        return _ollama(mensagens, timeout, json_mode)
