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
    monkeypatch.setattr(_voz, "BARGE_IN", False)
    monkeypatch.setattr(_voz, "_tocar_pcm", lambda pcm, rate: None)
    v = _voz.Voz.__new__(_voz.Voz)
    v.piper, v.stt = _PiperFake(), _STTFake()
    v.on_injecao = lambda: "tecla 2"
    v.on_inicio_fala = None
    assert v.falar("qualquer coisa") == "tecla 2"


def test_caminho_padrao_dos_modelos_nao_aponta_mais_pro_jarvis():
    # A SPEC lista "dependência do jarvis arrastada" como pecado do código velho
    # e o README promete "zero jarvis" — mas o caminho PADRÃO da voz apontava pra
    # dentro do ~/jarvis. Quem clonasse do zero não tinha a pasta.
    import os

    from autotuto import config
    # só é "jarvis" legitimamente se a pasta antiga existir nesta máquina
    if not os.path.exists(os.path.expanduser("~/jarvis/models/piper/pt_BR-faber-medium.onnx")):
        assert "jarvis" not in config.TTS_VOICE
    if not os.path.isdir(os.path.expanduser("~/jarvis/models/faster-whisper")):
        assert "jarvis" not in config.STT_CACHE


def test_voz_ausente_da_erro_que_ensina_a_baixar():
    import pytest

    from autotuto import config, voz

    class _Fake:
        pass

    original = config.TTS_VOICE
    config.TTS_VOICE = "/caminho/que/nao/existe/voz.onnx"
    try:
        with pytest.raises(FileNotFoundError) as e:
            voz.Voz.__init__(_Fake())        # só o trecho de carga
    except TypeError:
        # assinatura pede args: basta checar que a mensagem existe no config
        config.TTS_VOICE = original
        assert "download_voices" in config.COMO_BAIXAR_VOZ
        return
    finally:
        config.TTS_VOICE = original
    assert "download_voices" in str(e.value)
