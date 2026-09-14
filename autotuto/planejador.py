"""planejador.py — problema (texto) → LLM → PLANO estruturado (Aula) → validado.

    problema
       ↓  few-shot dirigido: casa o texto com uma aula de ouro do mesmo tipo
       ↓  llm.perguntar (Ollama local OU Claude), saída JSON
    JSON bruto
       ↓  schema.validar_estrutura — se falhar, devolve os erros pro LLM e tenta de novo
       ↓  aulas._com_genericos — todo plano ganha por_que / nao_entendi / repete
    Aula pronta pros geradores  (+ validador.checar_matematica → avisos não-fatais)

Sem LLM (ConnectionError etc.) ou tentativas esgotadas com erro → cai na
`aulas.AULA_SEM_PLANO`, que DIZ ao aluno que não deu, e devolve
`Relatorio(ok=False, ...)`. Nunca mente pro aluno: ou entrega um plano que
valida, ou admite em voz alta — jamais troca de assunto no lugar.

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
    # fração vem cedo: "3/4" e "metade" são sinal forte, e sem isso uma pergunta
    # como "quanto custa a metade" ia parar na regra de três.
    "fracao": (
        r"fra[çc]",                        # fração, frações, fracao, fracionar
        r"\b\d+\s*/\s*\d+\b",            # "3/4"
        r"\bmetade\b",
        r"\b(um|dois|tr[êe]s) (ter[çc]os?|quartos?|quintos?|oitavos?)\b",
        r"\bnumerador\b|\bdenominador\b",
        r"\bpeda[çc]os? iguais\b",
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


def _uma_figura_so(beats: list, ja_mostrou: list) -> list:
    """Deixa o spec inline COMPLETO só na primeira figura do exemplo.

    Medido: quase METADE do few-shot dirigido eram coordenadas cruas de spec
    inline (4238 chars na aula de equação, 45% disso em `spec`). Isso não ensina
    estrutura — a estrutura é `{"gerador": "figura", "spec": {...}}`, e uma
    ocorrência basta. O que as outras três cópias faziam era inchar o prompt e
    convidar o modelo a copiar as coordenadas do trapézio pro problema do aluno.

    Beats seguintes perdem a chave `figura` inteira em vez de ganharem um `spec`
    truncado: beat sem figura é válido, beat com `spec` de mentira ensinaria
    justamente o erro que o schema rejeita.
    """
    saida = []
    for b in beats:
        fig = b.get("figura")
        inline = isinstance(fig, dict) and fig.get("gerador") == "figura"
        if inline and ja_mostrou:
            b = {k: v for k, v in b.items() if k != "figura"}
            if not (b.get("diz") or b.get("calc")):
                continue                     # beat que ficaria vazio
        elif inline:
            ja_mostrou.append(True)
        saida.append(b)
    return saida


def _enxuta(aula: dict) -> str:
    """JSON compacto de uma aula: 4 blocos e 2 ramos de 1 beat, com só UMA
    figura inline por extenso — dá a forma inteira sem estourar o contexto de um
    modelo pequeno (ver `_uma_figura_so`)."""
    ja_mostrou: list = []
    return json.dumps({
        "titulo": aula["titulo"],
        "topico": aula["topico"],
        "dados": aula.get("dados", {}),
        "blocos": _uma_figura_so(aula["blocos"][:4], ja_mostrou),
        "ramos": {k: _uma_figura_so(v[:1], ja_mostrou)
                  for k, v in list(aula.get("ramos", {}).items())[:2]},
    }, ensure_ascii=False)


def exemplo(problema: str) -> tuple[str, bool]:
    """O few-shot que vai no prompt: `(json, dirigido)`.

    `dirigido=True` quando o tópico casou com uma aula de ouro — aí o exemplo
    dá ESTRUTURA e TOM do tipo certo. Quando não casa, vai o exemplo de
    estrutura genérico, porque ir SEM exemplo nenhum é o pior dos mundos:
    medido numa bateria de 11 tópicos, os 7 que não casavam pista eram
    exatamente os que voltavam com plano quebrado e caíam no fallback. Modelo
    de 7B não acerta schema aninhado só pela descrição em prosa.
    """
    dirigido = _exemplo_dirigido(problema)
    if dirigido is not None:
        return dirigido, True
    return _enxuta(aulas.EXEMPLO_ESTRUTURA), False


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
        return _enxuta(aula)
    return None


# ─────────────────────────────────────────────────────────────── prompt do sistema
# Regras da SPEC §3 (pedagogia) + §6 (modelo de dados). Os nomes de gerador estão
# embutidos como texto (planejador não importa calc/figuras — regra de dep.).
_SISTEMA = """Você é o PLANEJADOR de um professor de matemática que fala e desenha ao vivo.

TODO texto que o aluno vai OUVIR ou LER — "titulo", "diz", "diz_passos",
"confirma", "rotulos" — é em PORTUGUÊS DO BRASIL, sempre, do primeiro ao último
caractere. Nunca escreva em inglês, chinês ou qualquer outro idioma, nem uma
palavra solta: o aluno não lê. Os NOMES das chaves e dos geradores continuam
como estão aqui.

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

  "calc", "mostra_passos" e "diz_passos" vão SEMPRE NO MESMO OBJETO de beat —
  nunca em beats separados. `diz_passos` fora do beat do `calc` é jogado fora e
  a conta aparece muda. Uma frase de `diz_passos` por passo, na ordem. Assim:
    {"diz": "Agora a conta: soma as bases, vezes a altura, sobre dois.",
     "calc": {"gerador": "area_trapezio", "params": {"B": 18, "b": 10, "h": 6}},
     "mostra_passos": true,
     "diz_passos": ["Essa é a fórmula geral.",
                    "Agora entram os números do problema.",
                    "Vinte e oito vezes seis, e a metade disso dá oitenta e quatro."]}

  "pergunta.acerta" = exemplos do que o ALUNO diria pra mostrar que respondeu
  CERTO (a resposta dele, não a sua). "pergunta.confirma" = a SUA fala curta
  quando ele acerta (aí pula a derivação). Não confunda os dois papéis:
    Pergunta: "Qual é o MDC de 15 e 20?"
    acerta (CERTO — é o que o ALUNO fala):    ["5", "cinco", "o mdc é 5", "acho que é 5"]
    acerta (ERRADO — isso é fala SUA, não do aluno): ["Boa!", "Isso mesmo!", "Vamos continuar"]
    confirma (a SUA fala, separado): "Isso, o MDC é 5 mesmo — vamos direto pro próximo."

REGRAS DE PEDAGOGIA (SPEC §3):
- Nunca mentir pro aluno: só planeje o que dá pra explicar de verdade.
- "diz" NARRA A DECISÃO, não o passo cru. Ruim: "divide por dois". Bom: "divide por
  dois porque a gente quer a média das bases". Todo "diz" carrega o porquê.
- "diz" nunca tem LaTeX nem fórmula escrita — é fala. A fórmula aparece no calc.
- 4 a 8 blocos na trilha principal. Frases curtas, ditas como um bom professor fala.
- Ponha 1 beat "pergunta" antes do passo mais importante (self-explanation).
- "ramos" são desvios pra quando o aluno interrompe ou responde. SEMPRE inclua um
  "por_que..." e o "nao_entendi". Cada ramo com 1 a 3 beats. A trilha principal
  retoma de onde parou.
  OS TRÊS RAMOS "por_que", "nao_entendi" e "repete" EXISTEM SEMPRE: são
  adicionados automaticamente. Pode usar qualquer um deles em "senao" sem
  declarar, e pode sobrescrever qualquer um escrevendo o seu. Qualquer OUTRO
  nome que você usar em "senao" tem que estar declarado por você em "ramos".

GERADORES DE CÁLCULO (use no "calc", campo "gerador"):
  area_trapezio(B, b, h) · area_triangulo(base, altura) · area_retangulo(base, altura)
  · pitagoras(a, b, c)  (passe só 2; a HIPOTENUSA — lado maior, oposto ao ângulo reto
  — é "c") · eq_primeiro_grau(a, b)  (resolve a·x + b = 0) · regra_de_tres(a, b, c)
  · porcentagem(parte, todo)  (que % `parte` é de `todo`) · mdc(a, b) · mmc(a, b)
  · area_circulo(raio) · comprimento_circunferencia(raio)  (o contorno, 2·pi·r)
  · fracao_de(num, den, todo)  (quanto é num/den de todo)
  NÃO improvise um cálculo com um gerador que não é dele (ex.: usar eq_primeiro_grau
  pra simular porcentagem ou MDC) — se não existe gerador certo, admita no "diz" e
  siga sem o número exato.

GERADORES DE FIGURA (use no "figura", campo "gerador"):
  trapezio · triangulo · retangulo · dois_retangulos · balanca · tabela_prop ·
  reta_numerica · circulo(raio)  (desenha o raio rotulado) · fracao(num, den)
  (a pizza: den fatias iguais, as num primeiras pintadas — é assim que fração se
  mostra) — cada um aceita "params". Para uma composição própria (pontos nomeados,
  ângulos marcados) use {"gerador": "figura", "spec": {...}} com as
  chaves: pontos, poligonos, segmentos, angulos, marcas, rotulos, circulos.
  Um item de "circulos" é {"centro": [x,y] ou nome de ponto, "raio": n,
  "preenche": bool, "pintado": bool, "setor": [ini, fim] em graus} — com "setor"
  sai uma FATIA em vez do círculo inteiro. Use "pintado" (e não "preenche")
  quando o preenchimento É a resposta — a fatia comida, a parte que o aluno
  levou; "preenche" é só o tom discreto de "é desta figura que eu falo".

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


def _com_genericos_seguro(cand: dict) -> dict:
    """Mergeia por_que/nao_entendi/repete no candidato ANTES de validar.

    O prompt promete ao modelo que esses três ramos existem sempre. Mas a
    validação rodava no JSON CRU, antes do merge — então um plano que usava
    `"senao": "nao_entendi"` (exatamente o que o prompt manda fazer) era
    rejeitado com "não é um ramo", queimava as três tentativas e caía no
    fallback. Plano perfeito, reprovado por uma contradição nossa.

    Não mergeia quando `ramos` veio com formato errado: aí quem tem que
    reclamar é o schema, com a mensagem certa, e não um TypeError aqui.
    """
    if not isinstance(cand.get("ramos", {}), dict):
        return cand
    return aulas._com_genericos(cand)


def _norm_fala(t) -> str:
    return " ".join(str(t or "").split()).casefold()


def _tira_falas_repetidas(aula: dict) -> list[str]:
    """Tira `diz` idêntico ao do beat imediatamente anterior. Muta `aula`.

    ACHADO em bateria local: o professor falava a mesma frase duas vezes
    seguidas. Modelo pequeno repete beat, e ouvir a frase idêntica de novo não
    acrescenta nada — só faz o professor parecer travado. Cada trilha (a
    principal e cada ramo) é comparada separadamente: a primeira frase de um
    ramo PODE repetir a última da principal, ali a repetição é retomada, não
    gagueira.

    Beat com `pergunta` nunca é mexido: sem `diz` o tocador não pergunta nada e
    ficaria escutando um silêncio — pior que a repetição.
    """
    avisos: list[str] = []

    def limpa(beats: list, onde: str) -> list:
        saida, anterior = [], None
        for b in beats:
            if not isinstance(b, dict):
                saida.append(b)
                continue
            fala = _norm_fala(b.get("diz"))
            if fala and fala == anterior and not b.get("pergunta"):
                b = {k: v for k, v in b.items() if k != "diz"}
                avisos.append(f"{onde}: fala repetida do beat anterior, removida")
                if not (b.get("figura") or b.get("calc")):
                    continue                    # beat que virou vazio: some
            else:
                anterior = fala or anterior
            saida.append(b)
        return saida

    if isinstance(aula.get("blocos"), list):
        aula["blocos"] = limpa(aula["blocos"], "blocos")
    ramos = aula.get("ramos")
    if isinstance(ramos, dict):
        for nome, beats in ramos.items():
            if isinstance(beats, list):
                ramos[nome] = limpa(beats, f"ramo '{nome}'")
    return avisos


def _fallback(erros: list[str]) -> tuple[schema.Aula, Relatorio]:
    """A aula que ADMITE que não deu — nunca a de outro assunto.

    Antes isso devolvia a aula de ouro do trapézio: o aluno perguntava de
    porcentagem e o professor começava a falar de terreno, sem avisar. Trocar
    de assunto calado é a mentira que a regra única do projeto proíbe."""
    import copy
    dic = aulas._com_genericos(copy.deepcopy(aulas.AULA_SEM_PLANO))
    return schema.Aula.de_json(dic), Relatorio(ok=False, erros=erros, avisos=[])


def planeja(
    problema: str,
    *,
    tentativas: int = 3,
    perguntar=None,
) -> tuple[schema.Aula, Relatorio]:
    """Problema em texto → (Aula, Relatorio).

    Monta as mensagens (sistema = regras + catálogo; injeta o exemplo dirigido
    como par user/assistant quando casa; depois o problema), roda o loop de
    validação até `tentativas`, mergeia os ramos genéricos e devolve a Aula.
    Qualquer exceção de `perguntar` OU tentativas esgotadas com erro → fallback
    trapézio + `Relatorio(ok=False, ...)`.
    """
    # `perguntar=None` e não `perguntar=llm.perguntar`: o default de uma
    # função é avaliado no import, então a segunda forma CONGELA a função
    # daquele instante — trocar `llm.perguntar` depois (um mock, um
    # provedor escolhido em runtime) não tinha efeito nenhum aqui.
    perguntar = perguntar or llm.perguntar
    mensagens: list[dict] = [{"role": "system", "content": _SISTEMA}]
    modelo, dirigido = exemplo(problema)
    cabecalho = ("Exemplo de um plano bom para um problema parecido — copie a "
                 "ESTRUTURA e o TOM, nunca os números:\n" if dirigido else
                 "Exemplo do FORMATO exigido, de outro assunto — copie só a "
                 "ESTRUTURA do JSON. NÃO copie o assunto, os números, nem as "
                 "frases: o plano tem que ser sobre o que o aluno pediu:\n")
    mensagens.append({"role": "user", "content": cabecalho + modelo})
    mensagens.append({"role": "assistant", "content": modelo})
    mensagens.append({"role": "user", "content": problema})

    # Um teto só. O par curto/longo vinha de quando o caminho SEM pista ia pro
    # modelo sem exemplo nenhum: ali o modelo pensava mais e merecia mais tempo.
    # Depois que todo problema passou a levar exemplo, a relação INVERTEU — o
    # dirigido carrega uma aula de ouro e tem o prompt maior — e o teto curto
    # ficou no lado errado. A bateria de 2026-09-15 mostrou isso na cara: os 3
    # únicos fracassos foram tópicos COM aula de ouro, todos em 45.0s cravados,
    # enquanto os genéricos (prompt menor, teto de 100s) passaram folgados.
    timeout = PLANEJADOR_TIMEOUT_S

    erros: list[str] = ["planejador não rodou"]
    aula_dict: dict | None = None
    melhor_candidato: dict | None = None   # último que passou o schema (mesmo com avisos graves)

    for _ in range(max(1, tentativas)):
        try:
            bruto = perguntar(mensagens, timeout=timeout, json_mode=True)
        except Exception as e:  # ConnectionError, URLError, TimeoutError...
            return _fallback([f"LLM indisponível: {e!r}"])

        try:
            candidato = _com_genericos_seguro(_extrai_json(bruto))
            erros = schema.validar_estrutura(candidato)
        except (ValueError, json.JSONDecodeError) as e:
            candidato = None
            erros = [f"JSON inválido: {e}"]

        if not erros:
            melhor_candidato = candidato
            # P1.1: a forma pode validar mas uma ferramenta pedida não existir,
            # ou explodir com os params que vieram (kwarg que não é da
            # assinatura). Dá pro LLM a MESMA chance de correção que um erro
            # de schema tem — antes disso só aparecia depois, tarde demais.
            erros = validador.avisos_graves(validador.checar_matematica(candidato))

        if not erros:
            aula_dict = candidato
            break

        mensagens.append({"role": "assistant", "content": bruto})
        mensagens.append({"role": "user", "content": "corrija: " + "; ".join(erros)})

    if aula_dict is None:
        # tentativas esgotadas: se ALGUM candidato chegou a validar a forma,
        # usa o último deles (com os avisos que restarem) em vez de trocar de
        # assunto — perder o passo de uma conta é bem menos ruim que o
        # professor virar pra outro tópico sem avisar.
        aula_dict = melhor_candidato
        if aula_dict is None:
            return _fallback(erros)

    # RULING: mergeia os ramos genéricos ANTES de montar a Aula — todo plano
    # gerado ganha por_que / nao_entendi / repete (a aula sobrescreve por chave).
    aula_dict = aulas._com_genericos(aula_dict)
    repetidas = _tira_falas_repetidas(aula_dict)
    aula = schema.Aula.de_json(aula_dict)
    avisos = repetidas + validador.checar_matematica(aula_dict)
    # o plano validou a FORMA (schema), mas uma ferramenta pedida pode não
    # existir ou ter explodido com os params que o LLM mandou — aí uma etapa
    # do plano simplesmente não vai acontecer. `ok` tem que contar isso: senão
    # o contrato mente "deu tudo certo" pra um plano com um passo furado.
    ok = not validador.houve_falha_grave(avisos)
    return aula, Relatorio(ok=ok, erros=[], avisos=avisos)
