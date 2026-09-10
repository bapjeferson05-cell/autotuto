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
