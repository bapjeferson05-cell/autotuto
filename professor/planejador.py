"""planejador.py — problema (texto) → LLM → PLANO estruturado (Aula) → validado.

    problema
       ↓  hermes3:8b via Ollama, format=json
    JSON bruto
       ↓  valida_aula()  — se falhar, devolve os erros pro LLM e tenta de novo
    Aula pronta pros geradores

Sem dependência externa: fala com o Ollama por HTTP puro (urllib). Se o Ollama
não responder, `planeja()` cai no plano offline (aula escrita à mão).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from professor import validador
from professor.esquema import Aula, catalogo_para_prompt

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODELO = os.environ.get("PROF_MODELO", "hermes3:8b")

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
- "ramos" são desvios curtos para quando o aluno interrompe. Sempre inclua
  "por_que" e "nao_entendi", cada um com 1 a 3 blocos.
- 4 a 8 blocos no plano principal. Frases curtas.
- Use SÓ os geradores do catálogo abaixo, com esses parâmetros.

{catalogo_para_prompt()}
"""


def _ollama_json(mensagens: list[dict], *, timeout: float = 120) -> str:
    corpo = json.dumps({
        "model": MODELO,
        "messages": mensagens,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=corpo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read())["message"]["content"]


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
            bruto = _ollama_json(msgs)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if verbose:
                print(f"  Ollama indisponível ({e}) — usando plano offline")
            return planeja_offline(problema), validador.Relatorio(avisos=["plano offline"])
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
    """O problema do trapézio-terreno, escrito à mão. Usado quando não há LLM."""
    return Aula.de_json({
        "titulo": "Área do trapézio — o terreno",
        "topico": "area_trapezio",
        "dados": {"B": 18, "b": 10, "h": 10},
        "blocos": [
            {"diz": "O terreno tem forma de trapézio. A base de baixo mede dezoito, "
                    "a de cima mede dez.",
             "figura": {"gerador": "quadrilatero", "params": {"tipo": "trapezio_retangulo"}},
             "espera": "media"},
            {"diz": "A distância entre as duas bases é a altura, que vale dez.",
             "figura": {"gerador": "quadrilatero", "params": {"tipo": "trapezio_retangulo"}}},
            {"diz": "A área do trapézio é a soma das bases, vezes a altura, dividido por dois.",
             "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 10}},
             "mostra_passos": True, "espera": "longa"},
        ],
        "ramos": {
            "por_que": [
                {"diz": "Se fosse um retângulo com a base maior, a área seria dezoito vezes a "
                        "altura. Com a base menor, dez vezes. O trapézio fica no meio: por isso "
                        "a média das bases.",
                 "figura": {"gerador": "quadrilatero", "params": {"tipo": "retangulo"}},
                 "espera": "longa"},
            ],
            "nao_entendi": [
                {"diz": "Vamos devagar. Primeiro só as duas bases: dezoito embaixo, dez em cima.",
                 "figura": {"gerador": "quadrilatero", "params": {"tipo": "trapezio_isosceles"}},
                 "espera": "media"},
                {"diz": "Agora soma as duas: dezoito mais dez, vinte e oito. Esse é o número "
                        "que entra na conta.",
                 "espera": "media"},
            ],
        },
    })


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
