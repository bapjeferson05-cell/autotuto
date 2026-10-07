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
import errno
import re
import time
import unicodedata

from professor.aulas import carregar, disponiveis
from professor.classificador import normalizar
from professor.planejador import _PISTAS

_PORTAS = (8080, 8081, 8082)


def _norm(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def resolve(nome: str) -> str | None:
    """Frase pedida -> nome da aula de ouro, ou None.

    Exigir que a frase INTEIRA virasse a chave exata ("trapezio") fazia a caixa do
    visor mandar quase toda frase natural pro LLM — "teorema de pitágoras", "área
    do trapézio", "quero entender fração" — e aí, sem LLM no ar, o aluno ouvia que
    não dava, de uma aula que está pronta no catálogo. O inverso da premissa do
    comando. As pistas são as mesmas que o planejador já usa pra achar o few-shot.
    """
    for c in disponiveis():
        if _norm(c) == _norm(nome):
            return c
    # `_norm` junta palavras com "_" (serve pra comparar chave), então \b não quebra
    # nele. Pra casar FRASE usa-se o normalizador do classificador, separado por
    # espaço — o mesmo que já decide os gatilhos de interrupção.
    alvo = normalizar(nome)
    # casamento por palavra inteira, do mais específico pro mais genérico. Substring
    # cru dava falso positivo: a pista "x +" normaliza pra "x" e casa dentro de
    # "existe", mandando "qualquer coisa que não existe" pra aula de equação.
    catalogo = disponiveis()
    achados = []
    for nome_aula, pistas in _PISTAS.items():
        if nome_aula not in catalogo:
            continue
        for pista in pistas:
            chave = normalizar(pista)
            if len(chave) < 4:
                continue
            if re.search(rf"\b{re.escape(chave)}\b", alvo):
                achados.append((len(chave), nome_aula))
    return max(achados)[1] if achados else None


def _lista() -> str:
    linhas = ["aulas de ouro disponíveis (zero LLM, zero rede):", ""]
    linhas += [f"  autotuto {c}" for c in disponiveis()]
    linhas += ["", "tópico fora daqui? `autotuto --novo <topico>` tenta o planejador."]
    return "\n".join(linhas)


def _abre_visor(ritmo: float = 0.05):
    """Visor na 8080; se estiver ocupada, tenta as próximas. Rodar a demo duas vezes
    (ou ter qualquer coisa na 8080) cuspia um traceback de OSError na tela."""
    from professor.visor import Visor

    for porta in _PORTAS:
        try:
            return Visor(porta=porta, ritmo=ritmo).start()
        except OSError as e:
            if e.errno != errno.EADDRINUSE:
                raise
            print(f"porta {porta} ocupada — tentando a próxima…")
    raise SystemExit(f"portas {_PORTAS[0]}–{_PORTAS[-1]} ocupadas. Feche o visor que já "
                     f"está rodando e tente de novo.")


def _ouvir_teclado(visor, seg: float):
    # respeita o escuta_s do beat: o teto de 8s cortava a janela de 12s que o
    # próprio terminal anuncia ("esperando resposta (12s)"), e quem levava 9s pra
    # ler a figura e responder era tratado como quem ficou calado.
    fim = time.monotonic() + seg
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
    # TRAPÉZIO. Tocar isso aqui seria responder "área do círculo" com uma aula de
    # trapézio e cara de quem respondeu: a mentira que a regra única do projeto
    # proíbe. `rel.fatais` é o sinal estruturado de que a aula devolvida não é
    # sobre o pedido — antes isto procurava a string "plano offline" dentro de uma
    # frase em português, e reescrever a frase desligava a regra em silêncio.
    if rel.fatais or not aula.blocos:
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
    visor.estado("pronto")
    try:
        while True:
            # uma tecla apertada aqui deixava `_injecao` preso e o estado em
            # "ouvindo" pra sempre — e a página só mostra a caixa de texto em
            # "pronto"/"aguardando". Resultado: a caixa sumia, o texto ficava
            # latente pra invadir a próxima aula, e o loop não tinha saída.
            if visor.pop_injecao():
                visor.estado("pronto")
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
        print()


def _rodar(nome_catalogo: str, *, ficar_no_ar: bool) -> None:
    visor = _abre_visor()
    try:
        print(f"'{nome_catalogo}' direto do catálogo, zero LLM — "
              f"teclas 1/2/3/0 interrompem a fala.")
        _toca_na_tela(visor, carregar(nome_catalogo))
        if ficar_no_ar:
            _sessao(visor)
    finally:
        visor.stop()      # só _sessao fechava; sair pelos outros caminhos vazava o socket


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

    visor = _abre_visor()
    try:
        _tenta_planejador(visor, args.topico)
        if args.texto:
            _sessao(visor)
    finally:
        visor.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
