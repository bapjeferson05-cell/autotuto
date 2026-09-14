from autotuto.schema import Aula
from autotuto.estado import EstadoAula

A = Aula.de_json({"titulo": "T", "blocos": [{"diz": "p1"}, {"diz": "p2"}, {"diz": "p3"}],
                  "ramos": {"por_que": [{"diz": "r1"}, {"diz": "r2"}]}})

def test_percorre_principal():
    e = EstadoAula(A)
    assert [e.proximo()["diz"] for _ in range(3)] == ["p1", "p2", "p3"]
    assert e.proximo() is None

def test_ramo_empilha_drena_retoma():
    e = EstadoAula(A)
    e.proximo()                       # p1
    assert e.entra_ramo("por_que") and not e.na_principal
    assert [b["diz"] for b in e.drena_ramo()] == ["r1", "r2"]
    assert e.na_principal
    assert e.proximo()["diz"] == "p2" # retomou de onde parou

def test_ramo_inexistente_nao_muda_nada():
    e = EstadoAula(A)
    e.proximo()
    assert e.entra_ramo("fantasma") == []
    assert e.na_principal and e.proximo()["diz"] == "p2"

def test_historico_registra_gatilhos():
    e = EstadoAula(A)
    e.proximo(); e.entra_ramo("por_que"); list(e.drena_ramo())
    assert e.historico == ["por_que"]

def test_aula_public():
    """aula deve ser público (Task 11 acessa est.aula.ramos e est.aula.titulo)."""
    e = EstadoAula(A)
    assert e.aula is A

def test_drena_ramo_noop_na_principal():
    """drena_ramo() deve ser no-op quando já está na trilha principal."""
    e = EstadoAula(A)
    # Chamar drena_ramo() sem entra_ramo() anterior (já está na principal)
    resultado = list(e.drena_ramo())
    assert resultado == []  # yields nothing
    assert e.na_principal   # ainda está na principal
    assert e.proximo()["diz"] == "p1"  # proximo() retorna o primeiro beat

def test_historico_returns_copy():
    """historico property deve retornar uma cópia, não a lista interna."""
    e = EstadoAula(A)
    e.proximo(); e.entra_ramo("por_que"); list(e.drena_ramo())
    h1 = e.historico
    h2 = e.historico
    assert h1 == ["por_que"]
    assert h2 == ["por_que"]
    assert h1 is not h2  # são objetos diferentes
    # Tentar mutar a cópia não deve afetar o estado interno
    h1.append("fake")
    assert e.historico == ["por_que"]  # não foi afetado


def test_ramo_vazio_nao_empilha_e_a_aula_continua():
    # BUG: `entra_ramo` empilhava a trilha ANTES de ver que o ramo estava vazio e
    # devolvia [] — que o tocador lê como "ramo não existe". Resultado: fallback
    # honesto + pilha presa fora da principal = a aula acabava em silêncio no
    # meio. Um ramo vazio tem que se comportar como ramo inexistente, ponto.
    aula = Aula.de_json({"blocos": [{"diz": "a"}, {"diz": "b"}, {"diz": "c"}],
                         "ramos": {"vazio": []}})
    est = EstadoAula(aula)
    assert est.proximo() == {"diz": "a"}
    assert est.entra_ramo("vazio") == []
    assert est.na_principal                     # a pilha não pode ter mexido
    assert est.historico == []                  # nem o histórico
    assert est.proximo() == {"diz": "b"}        # e a aula SEGUE
    assert est.proximo() == {"diz": "c"}
