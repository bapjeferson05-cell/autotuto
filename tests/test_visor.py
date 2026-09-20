"""test_visor.py — `falar()` tem que cortar de verdade quando uma tecla injeta
texto durante a fala (achado no ensaio: antes só dormia e nunca olhava pra
`_injecao`, deixando a interrupção acumulada até a próxima 'pergunta')."""
import threading
import time

from professor.visor import Visor


def test_falar_sem_injecao_dorme_o_tempo_todo_e_devolve_none():
    v = Visor(ritmo=0.01)
    t0 = time.monotonic()
    assert v.falar("oi") is None
    assert time.monotonic() - t0 >= 0.015          # "oi" = 2 chars * 0.01s


def test_falar_e_interrompido_pela_injecao_no_meio_da_fala():
    v = Visor(ritmo=0.2)                            # fala "longa" (texto grande * 0.2s)

    def injeta_logo():
        time.sleep(0.05)
        with v._lock:
            v._injecao = "por que que divide por dois?"

    threading.Thread(target=injeta_logo).start()
    t0 = time.monotonic()
    r = v.falar("um texto propositalmente longo pra dar tempo de interromper")
    dt = time.monotonic() - t0

    assert r == "por que que divide por dois?"
    assert dt < 1.0                                  # cortou, não esperou a fala toda


def test_falar_sem_ritmo_nao_espera_nem_confere_injecao():
    v = Visor(ritmo=0)
    with v._lock:
        v._injecao = "isso não devia importar"
    assert v.falar("qualquer coisa") is None


def test_stop_libera_a_porta_de_verdade():
    # shutdown() sozinho para o loop mas deixa o socket de escuta aberto: o
    # próximo Visor na mesma porta levava "Address already in use".
    v = Visor(porta=8089, ritmo=0).start()
    v.stop()
    v2 = Visor(porta=8089, ritmo=0).start()     # tem que conseguir religar
    v2.stop()


def test_stop_e_idempotente():
    v = Visor(porta=8089, ritmo=0).start()
    v.stop()
    v.stop()
