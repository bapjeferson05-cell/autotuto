"""cli.py — um comando só: `autotuto [nome]`.

Filosofia: catálogo primeiro, LLM por último. Toda aula de ouro
(professor/aulas.py) toca sem rede, sem chave de API, sem planejador algum.
O planejador só entra quando o tópico pedido NÃO está no catálogo — e só se
o aluno insistir (--novo). Sem isso, o comando só oferece o catálogo.

    autotuto                    # lista as aulas de ouro
    autotuto trapezio           # toca, zero LLM
    autotuto --texto trapezio   # mesma aula; depois de acabar, fica esperando
                                 # outro tópico na caixa de texto do visor
    autotuto circulo            # não está no catálogo -> oferece o catálogo
    autotuto --novo circulo     # insiste -> aí sim chama o planejador
"""
from __future__ import annotations

import argparse
import re
import time
import unicodedata

from professor.aulas import carregar, disponiveis


def _norm(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def resolve(nome: str) -> str | None:
    """Nome pedido (com ou sem acento) -> nome exato no catálogo, ou None."""
    alvo = _norm(nome)
    for c in disponiveis():
        if _norm(c) == alvo:
            return c
    return None


def _lista() -> str:
    linhas = ["aulas de ouro disponíveis (zero LLM, zero rede):", ""]
    linhas += [f"  autotuto {c}" for c in disponiveis()]
    linhas += ["", "tópico fora daqui? `autotuto --novo <topico>` tenta o planejador."]
    return "\n".join(linhas)


def _ouvir_teclado(visor, seg: float):
    fim = time.monotonic() + min(seg, 8.0)
    while time.monotonic() < fim:
        t = visor.pop_injecao()
        if t:
            return t
        time.sleep(0.15)
    return None


def _toca_na_tela(visor, aula) -> None:
    from professor.tocador import Tocador

    tocador = Tocador(falar=visor.falar, ouvir=lambda seg: _ouvir_teclado(visor, seg),
                       desenhar=visor.desenhar, pausas=True, settle=0.45)
    est = tocador.toca(aula)
    visor.resumo(est.resumo())
    visor.estado("pronto")
    print(f"\n■ {est.resumo()}\n")


def _tenta_planejador(visor, pedido: str) -> None:
    from professor import planejador

    print(f"'{pedido}' não está no catálogo — chamando o planejador "
          f"(pode falhar ou demorar)…")
    visor.estado("pensando")
    visor.mostrar_fala("Deixa eu montar isso aqui…")
    aula, rel = planejador.planeja(pedido, verbose=True)
    if rel.avisos:
        print("  avisos:", rel.avisos)

    # planeja() sem LLM no ar devolve planeja_offline() — que é a aula de ouro do
    # TRAPÉZIO, com rel.ok=True. Tocar isso aqui seria responder "área do círculo"
    # com uma aula de trapézio e cara de quem respondeu: a mentira que a regra
    # única do projeto proíbe. Quem pediu tem que ouvir que não deu.
    caiu_no_offline = any("plano offline" in a for a in rel.avisos)
    if caiu_no_offline or not aula.blocos:
        recusa = (f"Não consegui montar uma aula de '{pedido}' agora — não tenho "
                  f"o modelo disponível aqui. Não vou te empurrar outra aula no lugar.")
        print(f"\n{recusa}\n")
        visor.mostrar_fala(recusa)
        visor.estado("pronto")
        print(_lista())
        return
    _toca_na_tela(visor, aula)


def _sessao(visor) -> None:
    print("digite outro tópico na caixa do visor (ou Ctrl+C pra sair)…")
    try:
        while True:
            pedido = visor.pop_pergunta()
            if pedido:
                print(f"\n🎤 “{pedido}”")
                achou = resolve(pedido)
                if achou:
                    _toca_na_tela(visor, carregar(achou))
                else:
                    _tenta_planejador(visor, pedido)
            time.sleep(0.15)
    except KeyboardInterrupt:
        visor.stop()


def _rodar(nome_catalogo: str, *, ficar_no_ar: bool) -> None:
    from professor.visor import Visor

    visor = Visor(ritmo=0.05).start()
    print(f"'{nome_catalogo}' direto do catálogo, zero LLM — teclas 1/2/3/0 interrompem a fala.")
    _toca_na_tela(visor, carregar(nome_catalogo))
    if ficar_no_ar:
        _sessao(visor)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="autotuto",
        description="Professor de matemática — catálogo primeiro, LLM por último.")
    p.add_argument("topico", nargs="?", help="nome da aula (ex.: trapezio)")
    p.add_argument("--novo", action="store_true",
                   help="tópico não está no catálogo? insiste e chama o planejador (LLM).")
    p.add_argument("--texto", action="store_true",
                   help="depois da aula, fica esperando outro tópico na caixa de texto.")
    args = p.parse_args(argv)

    if not args.topico:
        print(_lista())
        return 0

    achou = resolve(args.topico)
    if achou:
        _rodar(achou, ficar_no_ar=args.texto)
        return 0

    if not args.novo:
        print(f"não tenho '{args.topico}' pronto ainda.\n")
        print(_lista())
        print(f"\nquer que eu tente montar essa aula na hora? `autotuto --novo {args.topico}`")
        return 1

    from professor.visor import Visor

    visor = Visor(ritmo=0.05).start()
    _tenta_planejador(visor, args.topico)
    if args.texto:
        _sessao(visor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
