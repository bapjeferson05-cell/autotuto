"""planejador.py — problema (texto) → LLM → PLANO estruturado (Aula) → validado.

    problema
       ↓  few-shot dirigido: casa o texto com uma aula de ouro do mesmo tipo
       ↓  llm.perguntar (Ollama local OU Claude), saída JSON
    JSON bruto
       ↓  schema.validar_estrutura — se falhar, devolve os erros pro LLM e tenta de novo
       ↓  aulas._com_genericos — todo plano ganha por_que / nao_entendi / repete
    Aula pronta pros geradores  (+ validador.checar_matematica → avisos não-fatais)

Sem LLM (ConnectionError etc.) ou tentativas esgotadas com erro → cai na aula de
ouro do trapézio e devolve `Relatorio(ok=False, ...)`. Nunca mente pro aluno: ou
entrega um plano que valida, ou admite que caiu no fallback.

Dependência: só `json`, `re`, `autotuto.config`, `autotuto.llm`, `autotuto.schema`,
`autotuto.validador`, `autotuto.aulas`.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from autotuto import aulas, llm, schema, validador
from autotuto.config import PLANEJADOR_TIMEOUT_S

# RULING: todo módulo PODE importar autotuto.config (é a raiz, não importa nada).


@dataclass
class Relatorio:
    """Resultado de `planeja`. `ok` = plano do LLM validou; `avisos` = checagem
    matemática não-fatal. Quando `ok` é False, a Aula devolvida é o fallback."""

    ok: bool
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


# ───────────────────────────────────────────── few-shot dirigido: texto → tópico
# Primeiro casamento vence. Chaves = tópicos de `aulas._CATALOGO`. Valores = regex
# (já em minúsculas) testadas com `re.search` contra o problema em minúsculas.
_PISTAS: dict[str, tuple] = {
    "eq_primeiro_grau": (
        r"\b\d*x\s*[-+=]",          # "2x -", "x +", "x ="
        r"resolva",
        r"equa[çc][ãa]o",
        r"inc[óo]gnita",
        r"primeiro grau",
        r"pensei num n[úu]mero",
    ),
    "regra_de_tres": (
        r"regra de tr[êe]s",
        r"propor[çc]",
        r"quanto cust",
        r"\bcusta?m?\b",
        r"quantos? .*(custa|precisa|s[ãa]o|d[ãa]o)",
        r"para cada",
    ),
    "trapezio": (
        r"trap[ée]zio",
        r"trap[ée]z[oó]ide",
    ),
    "pitagoras": (
        r"pit[áa]goras",
        r"hipotenusa",
        r"\bcateto",
        r"tri[âa]ngulo ret[âa]ngulo",
        r"\bescada\b",
        r"\brampa\b",
        r"diagonal",
    ),
}


def _exemplo_dirigido(problema: str) -> str | None:
    """JSON enxuto da aula de ouro cujo tópico casa com o problema.

    Melhor que o exemplo genérico quando o tipo bate: dá ao LLM a ESTRUTURA e o
    TOM certos. Corta pra `blocos[:4]` e os 2 primeiros ramos (1 beat cada) pra
    não estourar o contexto. `None` se nenhuma pista casar.
    """
    p = problema.lower()
    for topico, pistas in _PISTAS.items():
        if not any(re.search(k, p) for k in pistas):
            continue
        aula = aulas._CATALOGO.get(topico)
        if aula is None:
            continue
        enxuta = {
            "titulo": aula["titulo"],
            "topico": aula["topico"],
            "dados": aula.get("dados", {}),
            "blocos": aula["blocos"][:4],
            "ramos": {k: v[:1] for k, v in list(aula.get("ramos", {}).items())[:2]},
        }
        return json.dumps(enxuta, ensure_ascii=False)
    return None


# ─────────────────────────────────────────────────────────────── prompt do sistema
# Regras da SPEC §3 (pedagogia) + §6 (modelo de dados). Os nomes de gerador estão
# embutidos como texto (planejador não importa calc/figuras — regra de dep.).
_SISTEMA = """Você é o PLANEJADOR de um professor de matemática que fala e desenha ao vivo.

Você NÃO desenha e NÃO faz contas (modelo de 8B erra aritmética). Você escreve um
PLANO em JSON: decide O QUE dizer, QUAL figura pedir e QUAL conta pedir, em passos
pequenos. Quem desenha é o renderizador; quem calcula é o Python.

MODELO DE DADOS (schema):
  Aula  = {"titulo": str, "topico": "id_curto", "dados": {os números do enunciado},
           "blocos": [Beat, ...], "ramos": {gatilho: [Beat, ...], ...}}
  Beat  = {
    "diz": str,                     # fala do professor — PT-BR, SEM LaTeX, sem "\\frac"
    "figura": {"gerador": str, ...}?,        # opcional: pede um desenho
    "calc":   {"gerador": str, "params": {...}}?,   # opcional: pede uma conta
    "mostra_passos": bool?,         # calc: mostra todos os passos ou só o resultado
    "diz_passos": [str]?,           # 1 frase curta narrada por passo (o aluno vê E ouve)
    "espera": "curta"|"media"|"longa"?,
    "pergunta": {"escuta_s": int(3..60), "senao": "<gatilho de ramo>",
                 "acerta": [str]?, "confirma": str?}?   # professor PERGUNTA e ESPERA
  }
  Cada bloco precisa de pelo menos um de: diz, figura, calc.
  Se um beat tem "pergunta", o "senao" TEM que ser um gatilho existente em "ramos".

REGRAS DE PEDAGOGIA (SPEC §3):
- Nunca mentir pro aluno: só planeje o que dá pra explicar de verdade.
- "diz" NARRA A DECISÃO, não o passo cru. Ruim: "divide por dois". Bom: "divide por
  dois porque a gente quer a média das bases". Todo "diz" carrega o porquê.
- "diz" nunca tem LaTeX nem fórmula escrita — é fala. A fórmula aparece no calc.
- 4 a 8 blocos na trilha principal. Frases curtas, ditas como um bom professor fala.
- Ponha 1 beat "pergunta" antes do passo mais importante (self-explanation).
- "ramos" são desvios pra quando o aluno interrompe ou responde. SEMPRE inclua um
  "por_que..." e o "nao_entendi". Cada ramo com 1 a 3 beats. A trilha principal
  retoma de onde parou. (por_que / nao_entendi / repete genéricos são adicionados
  depois — você pode sobrescrevê-los ou criar gatilhos específicos do tópico.)

GERADORES DE CÁLCULO (use no "calc", campo "gerador"):
  area_trapezio(B, b, h) · area_triangulo(base, altura) · area_retangulo(base, altura)
  · pitagoras(a, b, c)  (passe só 2; a HIPOTENUSA — lado maior, oposto ao ângulo reto
  — é "c") · eq_primeiro_grau(a, b)  (resolve a·x + b = 0) · regra_de_tres(a, b, c)

GERADORES DE FIGURA (use no "figura", campo "gerador"):
  trapezio · triangulo · retangulo · dois_retangulos · balanca · tabela_prop ·
  reta_numerica  — cada um aceita "params". Para uma composição própria (pontos
  nomeados, ângulos marcados) use {"gerador": "figura", "spec": {...}} com as
  chaves: pontos, poligonos, segmentos, angulos, marcas, rotulos.

RESPONDA SÓ com o objeto JSON do plano — nada antes, nada depois, sem cercas de código.
"""


def _extrai_json(txt: str) -> dict:
    """Primeiro `{` até o último `}`. Levanta se não achar / não parsear."""
    i, j = txt.find("{"), txt.rfind("}")
    if i == -1 or j == -1 or j < i:
        raise ValueError("resposta sem objeto JSON")
    obj = json.loads(txt[i : j + 1])
    if not isinstance(obj, dict):
        raise ValueError("JSON de topo não é um objeto")
    return obj


def _fallback(erros: list[str]) -> tuple[schema.Aula, Relatorio]:
    return aulas.carregar("trapezio"), Relatorio(ok=False, erros=erros, avisos=[])


def planeja(
    problema: str,
    *,
    tentativas: int = 3,
    perguntar=llm.perguntar,
) -> tuple[schema.Aula, Relatorio]:
    """Problema em texto → (Aula, Relatorio).

    Monta as mensagens (sistema = regras + catálogo; injeta o exemplo dirigido
    como par user/assistant quando casa; depois o problema), roda o loop de
    validação até `tentativas`, mergeia os ramos genéricos e devolve a Aula.
    Qualquer exceção de `perguntar` OU tentativas esgotadas com erro → fallback
    trapézio + `Relatorio(ok=False, ...)`.
    """
    mensagens: list[dict] = [{"role": "system", "content": _SISTEMA}]
    exemplo = _exemplo_dirigido(problema)
    if exemplo is not None:
        mensagens.append({
            "role": "user",
            "content": "Exemplo de um plano bom para um problema parecido — copie a "
                       "ESTRUTURA e o TOM, nunca os números:\n" + exemplo,
        })
        mensagens.append({"role": "assistant", "content": exemplo})
    mensagens.append({"role": "user", "content": problema})

    erros: list[str] = ["planejador não rodou"]
    aula_dict: dict | None = None

    for _ in range(max(1, tentativas)):
        try:
            bruto = perguntar(mensagens, timeout=PLANEJADOR_TIMEOUT_S, json_mode=True)
        except Exception as e:  # ConnectionError, URLError, TimeoutError...
            return _fallback([f"LLM indisponível: {e!r}"])

        try:
            candidato = _extrai_json(bruto)
            erros = schema.validar_estrutura(candidato)
        except (ValueError, json.JSONDecodeError) as e:
            candidato = None
            erros = [f"JSON inválido: {e}"]

        if not erros:
            aula_dict = candidato
            break

        mensagens.append({"role": "assistant", "content": bruto})
        mensagens.append({"role": "user", "content": "corrija: " + "; ".join(erros)})

    if aula_dict is None:
        return _fallback(erros)

    # RULING: mergeia os ramos genéricos ANTES de montar a Aula — todo plano
    # gerado ganha por_que / nao_entendi / repete (a aula sobrescreve por chave).
    aula_dict = aulas._com_genericos(aula_dict)
    aula = schema.Aula.de_json(aula_dict)
    avisos = validador.checar_matematica(aula_dict)
    # o plano validou a FORMA (schema), mas uma ferramenta pedida pode não
    # existir ou ter explodido com os params que o LLM mandou — aí uma etapa
    # do plano simplesmente não vai acontecer. `ok` tem que contar isso: senão
    # o contrato mente "deu tudo certo" pra um plano com um passo furado.
    ok = not validador.houve_falha_grave(avisos)
    return aula, Relatorio(ok=ok, erros=[], avisos=avisos)
