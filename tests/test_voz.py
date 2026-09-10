"""Testes do adapter de voz — sem tocar em hardware de áudio.

Componentes fake no lugar do Piper e do faster-whisper; `_tocar_pcm` vira no-op.
Travam dois contratos que o Tocador (Task 14) depende:
  1. `falar` sem barge-in devolve None (não fica escutando o mic).
  2. injeção de teclado (`on_injecao`) tem prioridade — corta antes de falar.
"""
from autotuto import voz as _voz


class _ChunkFake:
    sample_rate = 22050
    audio_int16_bytes = b"\x00\x00" * 100


class _PiperFake:
    def synthesize(self, txt, syn_config=None):
        yield _ChunkFake()


class _STTFake:
    def transcribe(self, audio, **kw):
        class _Seg:
            text = "resposta transcrita"
        return [_Seg()], None


def test_falar_sem_barge_devolve_none(monkeypatch):
    monkeypatch.setattr(_voz, "BARGE_IN", False)
    monkeypatch.setattr(_voz, "_tocar_pcm", lambda pcm, rate: None)
    v = _voz.Voz.__new__(_voz.Voz)
    v.piper, v.stt, v.on_injecao, v.on_inicio_fala = _PiperFake(), _STTFake(), None, None
    assert v.falar("olá turma") is None


def test_injecao_de_teclado_tem_prioridade(monkeypatch):
    monkeypatch.setattr(_voz, "_tocar_pcm", lambda pcm, rate: None)
    v = _voz.Voz.__new__(_voz.Voz)
    v.piper, v.stt = _PiperFake(), _STTFake()
    v.on_injecao = lambda: "tecla 2"
    v.on_inicio_fala = None
    assert v.falar("qualquer coisa") == "tecla 2"
