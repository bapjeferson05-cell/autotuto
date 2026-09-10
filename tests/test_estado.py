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
