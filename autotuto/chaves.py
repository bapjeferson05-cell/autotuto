"""chaves.py — escolher provedor e colar a chave em 15 segundos.

    python -m autotuto.chaves            # menu
    python -m autotuto.chaves groq       # já vai direto no groq

Escreve num `.env` na pasta atual (que o config.py carrega sozinho no import).
Não é "interface", é um prompt de terminal: escolhe número, cola a chave, pronto.
A chave NUNCA aparece de volta na tela inteira — só os 4 últimos caracteres.
"""
import sys
from pathlib import Path

from autotuto import provedores

ENV = Path(".env")


def _le_env() -> dict[str, str]:
    if not ENV.exists():
        return {}
    pares = {}
    for linha in ENV.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, _, v = linha.partition("=")
            pares[k.strip()] = v.strip()
    return pares


def _grava_env(pares: dict[str, str]) -> None:
    corpo = "\n".join(f"{k}={v}" for k, v in pares.items())
    ENV.write_text(corpo + "\n", encoding="utf-8")
    try:
        ENV.chmod(0o600)  # a chave é segredo: só o dono lê
    except OSError:
        pass


def _mascara(valor: str) -> str:
    return "····" + valor[-4:] if len(valor) > 4 else "····"


def _tabela() -> list[str]:
    """Lista os provedores de nuvem, marcando quem já tem chave configurada."""
    atual = _le_env()
    linhas = []
    for i, (nome, info) in enumerate(provedores.PROVEDORES.items(), 1):
        tem = atual.get(info["chave_env"])
        marca = f"  [chave: {_mascara(tem)}]" if tem else ""
        linhas.append(f"  {i}. {nome:<11} {info['cadastro']:<12} {info['limite']}{marca}")
    return linhas


def configura(nome: str, chave: str) -> None:
    """Grava a chave do provedor e deixa ele como o provedor ativo."""
    info = provedores.PROVEDORES[nome]
    pares = _le_env()
    pares[info["chave_env"]] = chave
    pares["AUTOTUTO_LLM"] = nome
    _grava_env(pares)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    nomes = list(provedores.PROVEDORES)

    if argv and argv[0] in nomes:
        escolhido = argv[0]
    elif argv:
        print(f"provedor '{argv[0]}' não existe. Conhecidos: {', '.join(nomes)}")
        return 1
    else:
        print("\nProvedores de LLM na nuvem (ollama roda local, não precisa de chave):\n")
        print("\n".join(_tabela()))
        resposta = input("\nqual? (número ou nome, Enter cancela): ").strip()
        if not resposta:
            return 0
        if resposta.isdigit() and 1 <= int(resposta) <= len(nomes):
            escolhido = nomes[int(resposta) - 1]
        elif resposta in nomes:
            escolhido = resposta
        else:
            print("não entendi.")
            return 1

    info = provedores.PROVEDORES[escolhido]
    print(f"\n{escolhido} — pega a chave em: {info['onde']}")
    print(f"cadastro: {info['cadastro']}  ·  grátis: {info['limite']}")
    chave = input(f"\ncola a {info['chave_env']} aqui: ").strip()
    if not chave:
        print("nada colado, saindo.")
        return 0

    configura(escolhido, chave)
    print(f"\n✓ gravado em {ENV.resolve()} (só você lê)")
    print(f"✓ AUTOTUTO_LLM={escolhido}, modelo default: {info['modelo']}")
    print("\nTesta com:  python demos/demo_texto.py")
    print("Trocar de modelo:  AUTOTUTO_MODELO=<nome> no .env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
