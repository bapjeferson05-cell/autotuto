"""test_figuras_concorrencia.py — as figuras são desenhadas do pool de threads do
FastAPI (uma thread por request). Por isso `professor/figuras/*` largou o pyplot,
que guarda as figuras num registro GLOBAL, e passou a usar Figure+FigureCanvasAgg,
onde cada figura é um objeto isolado.

Honestidade sobre o que este teste prova: ele garante que desenhar em paralelo dá o
MESMO byte que desenhar em série. Não é prova de que o pyplot corrompia — eu não
consegui reproduzir corrupção com ele. O que se ganhou foi concreto e medido: dá pra
largar o lock que serializava o desenho no backend (1,4x de vazão com 8 threads).
"""
import hashlib
from concurrent.futures import ThreadPoolExecutor

from professor.esquema import GERADORES
from professor.figuras import primitivas


def _nomeados():
    return [(n, g.fn) for n, g in sorted(GERADORES.items())
            if g.familia == "figura" and n != "figura"]


def test_pacote_de_figuras_nao_usa_pyplot():
    """pyplot é máquina de estado global; o pacote não pode voltar a importá-lo."""
    import pathlib
    pasta = pathlib.Path(primitivas.__file__).parent
    for arquivo in pasta.glob("*.py"):
        linhas = [ln for ln in arquivo.read_text(encoding="utf-8").splitlines()
                  if ln.strip().startswith(("import ", "from "))]
        for ln in linhas:
            assert "pyplot" not in ln, f"{arquivo.name}: {ln}"


def test_desenhar_em_paralelo_da_o_mesmo_byte_que_em_serie():
    tarefas = _nomeados()
    tarefas += [(f"passo{i}", (lambda i=i: primitivas.passo(rf"A = \dfrac{{{i}}}{{2}}")))
                for i in range(4)]
    assert len(tarefas) > 5, "catálogo de figuras vazio demais pro teste valer"

    serie = {nome: hashlib.sha256(fn()).hexdigest() for nome, fn in tarefas}

    def desenha(t):
        nome, fn = t
        return nome, hashlib.sha256(fn()).hexdigest()

    with ThreadPoolExecutor(max_workers=8) as ex:
        saidas = list(ex.map(desenha, tarefas * 4))

    divergentes = [n for n, h in saidas if serie[n] != h]
    assert not divergentes, f"figuras diferentes em paralelo: {sorted(set(divergentes))}"


def test_toda_figura_nomeada_sai_png_valido():
    for nome, fn in _nomeados():
        png = fn()
        assert png[:4] == b"\x89PNG", nome
        assert len(png) > 1000, (nome, len(png))
