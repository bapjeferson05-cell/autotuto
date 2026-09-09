"""planejador.py — problema (texto) → LLM → PLANO estruturado (Aula) → validado.

    problema
       ↓  LLM (Ollama local OU Claude API), saída JSON
    JSON bruto
       ↓  valida_aula()  — se falhar, devolve os erros pro LLM e tenta de novo
    Aula pronta pros geradores

Agnóstico de modelo. `PROF_LLM=ollama` (padrão) fala com o Ollama por HTTP puro;
`PROF_LLM=claude` usa a API da Anthropic (precisa de ANTHROPIC_API_KEY). O resto do
sistema — validador, geradores, tocador — não percebe a troca. Sem Ollama nem chave,
`planeja()` cai no plano offline.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from professor import validador
from professor.aulas import TRAPEZIO
from professor.esquema import Aula, catalogo_para_prompt

PROVEDOR = os.environ.get("PROF_LLM", "ollama")
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODELO = os.environ.get("PROF_MODELO", "hermes3:8b")
CLAUDE_MODELO = os.environ.get("PROF_CLAUDE_MODEL", "claude-sonnet-5")


def _fewshot() -> str:
    """A aula de ouro do trapézio, enxugada — o LLM copia o padrão."""
    ex = {"titulo": TRAPEZIO["titulo"], "topico": TRAPEZIO["topico"],
          "dados": {k: TRAPEZIO["dados"][k] for k in ("B", "b", "h")},
          "blocos": TRAPEZIO["blocos"][:4],
          "ramos": {"por_que_div_2": TRAPEZIO["ramos"]["por_que_div_2"][:2],
                    "nao_entendi": TRAPEZIO["ramos"]["nao_entendi"][:1]}}
    return json.dumps(ex, ensure_ascii=False, indent=1)

PROMPT = f"""Você é o planejador de um professor de matemática que fala e desenha ao vivo.

Você NÃO desenha e NÃO faz contas. Você escreve um PLANO em JSON. Quem desenha é o
renderizador; quem calcula é o Python. Você decide O QUE dizer, QUAL figura pedir e
QUAL conta pedir, em pequenos passos.

Formato exato (responda SÓ com esse objeto JSON, nada antes ou depois):

{{
  "titulo": "curto",
  "topico": "identificador_curto",
  "dados": {{ ...os números do problema... }},
  "blocos": [
    {{
      "diz": "frase curta e falada, sem LaTeX, do jeito que um professor fala",
      "figura": {{ "gerador": "...", "params": {{...}} }},
      "espera": "curta" | "media" | "longa"
    }},
    {{
      "diz": "...",
      "calc": {{ "gerador": "...", "params": {{...}} }},
      "mostra_passos": true
    }}
  ],
  "ramos": {{
    "por_que": [ {{ "diz": "...", "figura": {{...}} }} ],
    "nao_entendi": [ {{ "diz": "...", "figura": {{...}} }} ]
  }}
}}

Regras:
- Todo bloco tem "diz" (texto falado, sem LaTeX). "figura" e "calc" são opcionais.
- PREFIRA os geradores específicos: parte_circulo, poligono_regular, triangulo,
  quadrilatero, curva, funcao, solido. Use "figura" SÓ quando precisar de uma
  composição própria (pontos nomeados, cotas, ângulos marcados) que os outros não dão.
- O gerador "figura" usa a chave "spec" (não "params"). A spec é assim:
      {{"pontos": {{"A": [0,0], "B": [18,0], "C": [14,6], "D": [4,6]}},
        "poligonos": [{{"vs": ["A","B","C","D"], "preenche": true}}],
        "cotas": [{{"de": "A", "para": "B", "texto": "18", "lado": -1}}],
        "angulos": [{{"em": "A", "de": "B", "para": "D", "reto": true}}]}}
  Chaves válidas: pontos, poligonos, segmentos, circulos, angulos, marcas, cotas, rotulos.
- "ramos" são desvios para quando o aluno interrompe. Gatilhos: "por_que_div_2"
  (ou "por_que" genérico), "nao_entendi", e outros que fizerem sentido pro tópico
  (ex.: "e_triangulo", "decompor"). Sempre inclua "nao_entendi" e um "por_que...".
  Cada ramo com 1 a 3 blocos. A trilha principal retoma de onde parou.
- 4 a 8 blocos no plano principal. Frases curtas, faladas, como um bom professor.
- Use SÓ os geradores do catálogo abaixo, com esses parâmetros.

EXEMPLO de um plano bom (área do trapézio):
{_fewshot()}

CATÁLOGO:
{catalogo_para_prompt()}
"""


def _ollama_json(mensagens: list[dict], *, timeout: float = 120) -> str:
    corpo = json.dumps({
        "model": MODELO,
        "messages": mensagens,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_ctx": 12288},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=corpo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read())["message"]["content"]


def _claude_json(mensagens: list[dict], *, timeout: float = 120) -> str:
    chave = os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        raise ConnectionError("PROF_LLM=claude mas ANTHROPIC_API_KEY não está definida")
    sistema = "\n".join(m["content"] for m in mensagens if m["role"] == "system")
    turnos = [m for m in mensagens if m["role"] != "system"]
    corpo = json.dumps({
        "model": CLAUDE_MODELO,
        "max_tokens": 4096,
        "temperature": 0.3,
        "system": sistema + "\n\nResponda APENAS com o objeto JSON, sem cercas de código.",
        "messages": turnos,
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=corpo,
                                 headers={"content-type": "application/json",
                                          "x-api-key": chave,
                                          "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        d = json.loads(r.read())
    return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")


def _llm_json(mensagens: list[dict], *, timeout: float = 120) -> str:
    return (_claude_json if PROVEDOR == "claude" else _ollama_json)(mensagens, timeout=timeout)


def _extrai_json(txt: str) -> dict:
    txt = txt.strip()
    if txt.startswith("```"):
        txt = txt.split("```", 2)[1].removeprefix("json").strip()
    i, j = txt.find("{"), txt.rfind("}")
    return json.loads(txt[i:j + 1])


# ────────────────────────────────────────────────────── reparo determinístico
_RENOMEIA = {"circulo": "circulos", "poligono": "poligonos", "poligonos_": "poligonos",
             "segmento": "segmentos", "angulo": "angulos", "cota": "cotas",
             "rotulo": "rotulos", "ponto": "pontos", "circle": "circulos"}
_FALLBACK_RAMO = {
    "por_que": "Boa pergunta. A ideia é sempre voltar à definição e ver de onde a "
               "fórmula vem — não decorar, entender.",
    "nao_entendi": "Sem problema, vamos mais devagar. Me diz qual parte travou que "
                   "eu refaço só ela.",
}


def _repara_spec(spec: dict) -> dict:
    if not isinstance(spec, dict):
        return {}
    out: dict = {}
    for k, v in spec.items():
        nk = _RENOMEIA.get(k, k)
        if nk in ("poligonos", "segmentos", "circulos", "angulos", "marcas", "cotas", "rotulos"):
            if isinstance(v, dict):
                v = [v]
            elif not isinstance(v, list):
                continue
        out[nk] = v
    return out


def _saneia(aula: Aula) -> tuple[Aula, list[str]]:
    """Última linha: repara o que dá, joga fora bloco/ramo que não valida, garante
    os ramos padrão. Um plano com 1 ramo quebrado não derruba a aula toda."""
    notas: list[str] = []
    todos = list(aula.blocos) + [b for v in (aula.ramos or {}).values() for b in v]
    for b in todos:
        fg = b.get("figura")
        if isinstance(fg, dict) and fg.get("gerador") == "figura":
            fg["spec"] = _repara_spec(fg.get("spec", {}))

    bons = [b for b in aula.blocos if validador.valida_bloco(b).ok]
    if len(bons) < len(aula.blocos):
        notas.append(f"{len(aula.blocos) - len(bons)} bloco(s) inválidos removidos")
    if not bons:
        return planeja_offline(), notas + ["plano inteiro inválido — plano offline"]
    aula.blocos = bons

    ramos: dict[str, list[dict]] = {}
    for g, blist in (aula.ramos or {}).items():
        ok = [b for b in blist if validador.valida_bloco(b).ok]
        if ok:
            ramos[g] = ok
        else:
            notas.append(f"ramo '{g}' descartado (inválido)")
    for g, txt in _FALLBACK_RAMO.items():
        ramos.setdefault(g, [{"diz": txt, "espera": "media"}])
    aula.ramos = ramos
    return aula, notas


def planeja(problema: str, *, tentativas: int = 4, sanear: bool = True,
            verbose: bool = True) -> tuple[Aula, validador.Relatorio]:
    """Devolve (aula, relatorio). Se `sanear`, a aula volta sempre utilizável
    (blocos/ramos ruins removidos); relatorio.avisos conta o que foi mexido."""
    msgs = [{"role": "system", "content": PROMPT}, {"role": "user", "content": problema}]
    ultima = Aula("(vazia)", [])
    rel = validador.Relatorio(["não rodou"])
    for t in range(1, tentativas + 1):
        try:
            bruto = _llm_json(msgs)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if verbose:
                print(f"  LLM ({PROVEDOR}) indisponível ({e}) — usando plano offline")
            return planeja_offline(problema), validador.Relatorio(avisos=[f"plano offline ({e})"])
        try:
            ultima = Aula.de_json(_extrai_json(bruto))
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            rel = validador.Relatorio([f"JSON inválido: {e}"])
            msgs += [{"role": "assistant", "content": bruto[:2000]},
                     {"role": "user", "content": f"Isso não era JSON válido ({e}). "
                      "Responda só com o objeto JSON, nada mais."}]
            continue
        rel = validador.valida_aula(ultima)
        if verbose:
            print(f"  tentativa {t}: {len(ultima.blocos)} blocos, {len(rel.problemas)} problema(s)")
        if rel.ok:
            return ultima, rel
        msgs += [{"role": "assistant", "content": bruto[:2000]},
                 {"role": "user", "content": "O plano tem estes problemas. Corrija TODOS e "
                  "reenvie o JSON completo:\n- " + "\n- ".join(rel.problemas[:20])}]

    if sanear:
        ultima, notas = _saneia(ultima)
        rel2 = validador.valida_aula(ultima)
        rel2.avisos = notas + [f"{len(rel.problemas)} problema(s) do LLM não resolvidos em "
                               f"{tentativas} tentativas"]
        if verbose:
            print(f"  saneado: {notas}")
        return ultima, rel2
    return ultima, rel


# ────────────────────────────────────────────────────────── plano offline (demo)
def planeja_offline(problema: str = "") -> Aula:
    """Sem LLM: devolve a aula de ouro do trapézio (professor/aulas.py)."""
    from professor.aulas import carregar
    return carregar("trapezio")


if __name__ == "__main__":
    import sys

    prob = " ".join(sys.argv[1:]) or (
        "Um terreno é um trapézio retângulo. A base maior mede 18 m, a base menor 10 m "
        "e a altura 10 m. Qual é a área?")
    print(f"PROBLEMA: {prob}\n")
    aula, rel = planeja(prob)
    print(f"\nTÍTULO: {aula.titulo}   ({len(aula.blocos)} blocos, ramos: {list(aula.ramos)})")
    if rel.problemas:
        print("PROBLEMAS:", *rel.problemas, sep="\n  ")
    print("\n" + json.dumps(aula.para_json(), ensure_ascii=False, indent=2))
