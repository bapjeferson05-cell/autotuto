"""test_api.py — testes do backend sem LLM/rede: usa a aula de ouro do trapézio
(professor/aulas.py) no lugar do planejador de verdade.

    pip install -r backend/requirements.txt -r backend/requirements-dev.txt
    python3 -m pytest backend/tests -v
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from professor import validador
from professor.aulas import carregar

client = TestClient(app)


def _aula_offline(problema, *, verbose=False):
    return carregar("trapezio"), validador.Relatorio()


@pytest.fixture(autouse=True)
def sem_llm():
    """Troca o planejador (que chamaria Ollama/Claude) pela aula de ouro do trapézio —
    os testes do backend não devem depender de rede nem de um LLM configurado."""
    with patch("backend.services.sessao.planejador.planeja", side_effect=_aula_offline):
        yield


def _sid(problema="área do trapézio") -> str:
    return client.post("/api/aulas", json={"problema": problema}).json()["session_id"]


def test_inicia_sessao_e_devolve_o_primeiro_beat():
    r = client.post("/api/aulas", json={"problema": "área do trapézio"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["session_id"]
    assert corpo["titulo"] == "Área do trapézio — o terreno"
    assert corpo["fim"] is False
    assert "figura_png_base64" in corpo
    assert corpo["diz"]


def test_problema_vazio_e_400():
    r = client.post("/api/aulas", json={"problema": "   "})
    assert r.status_code == 400


def test_sessao_inexistente_e_404():
    assert client.post("/api/aulas/nao-existe/proximo", json={}).status_code == 404
    assert client.get("/api/aulas/nao-existe/estado").status_code == 404


def test_avanca_pelos_beats_ate_a_pergunta():
    sid = _sid()
    beats = [client.post(f"/api/aulas/{sid}/proximo", json={}).json() for _ in range(3)]
    assert beats[2]["tem_pergunta"] is True
    assert "calc" not in beats[2]  # a fórmula só vem depois da pergunta


def test_calc_devolve_latex_bruto_pro_frontend_renderizar():
    sid = _sid()
    for _ in range(3):
        client.post(f"/api/aulas/{sid}/proximo", json={})  # até a pergunta
    client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "vira um triângulo"})  # fading
    beat_calc = client.post(f"/api/aulas/{sid}/proximo", json={}).json()
    assert beat_calc["valor"] == 84.0
    assert len(beat_calc["passos_latex"]) >= 1
    assert all(isinstance(p, str) for p in beat_calc["passos_latex"])


def test_responde_certo_a_pergunta_faz_fading_sem_ramo():
    sid = _sid()
    for _ in range(3):
        client.post(f"/api/aulas/{sid}/proximo", json={})
    r = client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "vira um triângulo"})
    assert "Isso" in r.json()["diz"]
    assert client.get(f"/api/aulas/{sid}/estado").json()["na_principal"] is True


def test_silencio_na_pergunta_entra_no_ramo_senao():
    sid = _sid()
    for _ in range(3):
        client.post(f"/api/aulas/{sid}/proximo", json={})
    r = client.post(f"/api/aulas/{sid}/proximo", json={})  # sem resposta = silêncio
    assert client.get(f"/api/aulas/{sid}/estado").json()["na_principal"] is False
    assert r.json()["fim"] is False


def test_responde_errado_a_pergunta_entra_no_ramo():
    sid = _sid()
    for _ in range(3):
        client.post(f"/api/aulas/{sid}/proximo", json={})
    client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "não sei"})
    assert client.get(f"/api/aulas/{sid}/estado").json()["na_principal"] is False


def test_interrompe_com_por_que_entra_no_ramo_por_que_div_2():
    sid = _sid()
    client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "por que divide por dois?"})
    assert client.get(f"/api/aulas/{sid}/estado").json()["na_principal"] is False


def test_gatilho_sem_ramo_correspondente_nao_quebra_a_sessao():
    sid = _sid()
    r = client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "asdkjasdkj sem sentido"})
    assert r.status_code == 200
    assert r.json()["fim"] is False
    assert client.get(f"/api/aulas/{sid}/estado").json()["na_principal"] is True


def test_chega_ao_fim_da_aula():
    sid = _sid()
    ultimo = None
    for _ in range(20):
        ultimo = client.post(f"/api/aulas/{sid}/proximo", json={}).json()
        if ultimo.get("fim"):
            break
    assert ultimo["fim"] is True
    assert "resumo" in ultimo


def test_saude():
    assert client.get("/api/saude").json() == {"ok": True}


# ═════════ as mentiras que o cli.py já recusava e o backend ainda servia

def test_plano_offline_e_recusado_em_vez_de_servir_trapezio():
    """planeja() sem LLM devolve a aula de ouro do TRAPÉZIO com cara de resposta.
    Servir isso pra quem pediu círculo é a mentira que a regra única proíbe — e
    aqui era pior que no CLI, porque é o caminho do `docker compose up`."""
    def _offline(problema, *, verbose=False):
        return carregar("trapezio"), validador.Relatorio(
            avisos=["plano offline"],
            fatais=["LLM indisponível — a aula devolvida não é sobre o pedido"])

    with patch("backend.services.sessao.planejador.planeja", side_effect=_offline):
        r = client.post("/api/aulas", json={"problema": "área do círculo de raio 5"})
    body = r.json()

    assert r.status_code == 200
    assert body.get("recusa") is True
    assert "trapézio" not in (body.get("diz") or "").lower()
    assert "Não consegui montar" in body["diz"]
    assert body["aulas_prontas"], "recusou sem oferecer o que existe pronto"


def test_interrupcao_nao_classificada_nao_finge_que_entendeu():
    sid = _sid()
    r = client.post(f"/api/aulas/{sid}/proximo",
                    json={"resposta": "asdkjasdkj zzz sem sentido nenhum"})
    body = r.json()
    assert "não preparei" in body["diz"], body
    # e não pode ter entrado em ramo nenhum
    assert "ramo" not in body.get("resumo", "")


def test_pedir_ajuda_nao_conta_como_acerto():
    """senao='por_que' é o ramo de quem NÃO sabe. Tratar 'classificou no senao'
    como acerto parabenizava quem acabou de admitir que não entendeu."""
    def _eq(problema, *, verbose=False):
        return carregar("eq_primeiro_grau"), validador.Relatorio()

    with patch("backend.services.sessao.planejador.planeja", side_effect=_eq):
        sid = client.post("/api/aulas", json={"problema": "equação"}).json()["session_id"]
        corpo = None
        for _ in range(8):
            corpo = client.post(f"/api/aulas/{sid}/proximo", json={}).json()
            if corpo.get("tem_pergunta"):
                break
        assert corpo and corpo.get("tem_pergunta"), "não cheguei no beat de pergunta"
        r = client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "por quê?"}).json()

    assert "Exato" not in (r.get("diz") or ""), "parabenizou quem pediu ajuda"


def test_acerto_com_acento_continua_sendo_acerto():
    sid = _sid()
    for _ in range(3):
        client.post(f"/api/aulas/{sid}/proximo", json={})
    r = client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "vira um triângulo"}).json()
    assert "Isso" in r["diz"], ("acento derrubou um acerto", r)


def test_diz_passos_chega_no_frontend():
    """o 'worked example' é uma frase por linha da conta; o adapter descartava e o
    aluno da web via álgebra muda enquanto o de voz ouvia o porquê de cada passo."""
    sid = _sid()
    for _ in range(3):
        client.post(f"/api/aulas/{sid}/proximo", json={})
    client.post(f"/api/aulas/{sid}/proximo", json={"resposta": "vira um triângulo"})
    beat = client.post(f"/api/aulas/{sid}/proximo", json={}).json()
    assert beat.get("diz_passos"), beat
    assert len(beat["diz_passos"]) == len(beat["passos_latex"])


def test_calc_que_estoura_nao_vira_500_nem_engole_o_beat():
    """params crus do LLM ('18' em vez de 18) estouravam no gerador: HTTP 500, e
    como o beat já tinha sido consumido, o retry do cliente pulava ele."""
    from professor.esquema import Aula

    aula = Aula("Teste", [{"diz": "a conta vem aí",
                           "calc": {"gerador": "area_trapezio",
                                    "params": {"B": "18", "b": "10", "h": "6"}}},
                          {"diz": "beat seguinte"}])

    def _torto(problema, *, verbose=False):
        return aula, validador.Relatorio()

    with patch("backend.services.sessao.planejador.planeja", side_effect=_torto):
        r = client.post("/api/aulas", json={"problema": "x"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["diz"] == "a conta vem aí"
    assert body.get("falhou"), "fingiu que a conta saiu"


# ═════════ o plano lento não pode prender o pool compartilhado do Starlette
#
# Medido num uvicorn de verdade, com 45 planos de 5s em voo:
#   antes  → GET /api/saude levava 4,79s (contra 20ms ocioso)
#   depois → 1,6ms, igual a ocioso
#
# A causa não era o event loop (endpoint `def` do FastAPI já roda no pool): era o
# pool COMPARTILHADO de 40 vagas sendo tomado inteiro por planos presos no LLM.
# Os dois testes abaixo são estruturais — fixam o mecanismo que produziu aquela
# medição. Reproduzir a latência em teste exigiria subir servidor e carga real,
# que não cabe numa suíte unitária.

def test_saude_nao_consome_vaga_do_pool_de_threads():
    import inspect

    from backend import app as app_mod
    assert inspect.iscoroutinefunction(app_mod.saude), (
        "/api/saude precisa ser `async def` pra ser respondido no event loop; como "
        "`def` ele entra na fila do pool e fica atrás dos planos lentos")


def test_iniciar_usa_executor_proprio_e_nao_o_pool_compartilhado():
    import inspect

    from backend import app as app_mod
    from backend.services import sessao as svc

    assert inspect.iscoroutinefunction(app_mod.iniciar)
    fonte = inspect.getsource(app_mod.iniciar)
    assert "iniciar_sessao_async" in fonte, (
        "o plano precisa ir pro executor próprio; chamar iniciar_sessao direto num "
        "endpoint `def` devolve o problema do pool compartilhado")
    assert svc._EXECUTOR_PLANO._max_workers <= 16, (
        "o executor do plano tem que ser LIMITADO — ilimitado só muda o lugar do "
        "problema")


def test_iniciar_sessao_async_devolve_o_mesmo_que_a_versao_sincrona():
    import asyncio

    from backend.services import sessao as svc

    with patch("backend.services.sessao.planejador.planeja", side_effect=_aula_offline):
        sid, sessao, saida = asyncio.run(svc.iniciar_sessao_async("trapézio"))
    assert sid and sessao is not None
    assert saida["titulo"] == carregar("trapezio").titulo
