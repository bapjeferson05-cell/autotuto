"""voz.py — a ponte entre o Tocador e o jarvis (STT + Piper + barge-in).

O contrato do Tocador é `falar(texto) -> str | None`: fala; se o aluno interromper,
devolve a fala dele (transcrita). Este módulo implementa isso com o que o jarvis já
tem pronto:

  jarvis.core.speaker.speak_stream(tokens, piper, monitor=)  → (falado, interrompido)
  jarvis.audio.monitor.BargeInMonitor                        → corta a fala, guarda o onset
  jarvis.audio.capture.record_vad(vad)                        → captura o resto da fala
  jarvis.stt.engine.FasterWhisperEngine.transcribe(audio)     → texto

Import tardio: o venv do professor não precisa das libs de áudio pra rodar o resto
do projeto. Rode o `demo_voz.py` com o Python do jarvis (que já tem tudo):

    ~/jarvis/.venv/bin/python -m pip install matplotlib      # se faltar
    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python demo_voz.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_JARVIS = Path.home() / "jarvis"


def _prepara_path() -> None:
    if str(_JARVIS) not in sys.path:
        sys.path.insert(0, str(_JARVIS))


class Voz:
    """Segura Piper, faster-whisper e o VAD. `falar` e `desenhar` vão pro Tocador;
    `desenhar` continua sendo o do Visor (ou o que for)."""

    def __init__(self) -> None:
        _prepara_path()
        from jarvis.audio.vad import SileroVAD
        from jarvis.stt.engine import FasterWhisperEngine
        from jarvis.tts.piper import Piper

        print("[voz] carregando Piper + faster-whisper…")
        self.piper = Piper()
        self.stt = FasterWhisperEngine()
        self.vad = SileroVAD()
        self._onset_rate = 16000

    # ------------------------------------------------------------------ falar
    def falar(self, texto: str) -> str | None:
        """Fala `texto`. Se o aluno interromper, devolve a transcrição da fala dele."""
        from jarvis.audio import capture
        from jarvis.audio.monitor import BargeInMonitor
        from jarvis.core.speaker import speak_stream

        monitor = BargeInMonitor()
        _falado, interrompido = speak_stream(iter([texto]), self.piper, monitor=monitor)
        if not interrompido:
            return None

        # onset capturado pelo monitor (int16 16k) + o resto da fala.
        # BOUND: se não vier uma fala com fim claro em ~4 s, era eco — não trava.
        onset = np.frombuffer(monitor.buffer, dtype=np.int16).astype(np.float32) / 32768.0
        try:
            resto = self._record_ate(capture, 4.0)
        except Exception:  # noqa: BLE001
            resto = None
        audio = np.concatenate([onset, resto]) if resto is not None and resto.size else onset
        if audio.size < self._onset_rate:           # < 1 s: quase certo que é eco do Piper
            return None
        texto_aluno = self.stt.transcribe(audio).text.strip()
        return texto_aluno or None

    # ------------------------------------------------------------------ ouvir
    def ouvir(self, timeout: float | None = None) -> str | None:
        """Escuta o aluno. Com `timeout`, desiste se ele não começar a falar em
        `timeout` s (pro beat 'pergunta'). Sem `timeout`, bloqueia (início da sessão).
        Devolve a transcrição, ou None se calou / não deu pra entender."""
        from jarvis.audio import capture
        from jarvis.audio.vad import SileroVAD  # noqa: F401  (garante import cedo)

        audio = (self._record_ate(capture, timeout) if timeout
                 else capture.record_vad(self.vad))
        if audio is None or audio.size < self._onset_rate // 3:
            return None
        return self.stt.transcribe(audio).text.strip() or None

    def _record_ate(self, capture, timeout: float):
        """record_vad, mas desiste se nenhuma fala começar em `timeout` s."""
        import collections

        chunk = 512
        frame_ms = chunk * 1000 // 16000
        limite_frames = int(timeout * 1000 / frame_ms)
        silence_limit = max(1, 700 // frame_ms)
        preroll = collections.deque(maxlen=max(1, 300 // frame_ms))
        voiced = bytearray()
        triggered = False
        silence = 0
        self.vad.reset()
        stream = capture.frames(chunk)
        try:
            for i, frame in enumerate(stream):
                fala = self.vad.is_speech(frame)
                if not triggered:
                    preroll.append(frame)
                    if fala:
                        triggered = True
                        voiced = bytearray(b"".join(preroll))
                    elif i >= limite_frames:
                        return None
                    continue
                voiced += frame
                silence = 0 if fala else silence + 1
                if silence >= silence_limit or len(voiced) >= 16000 * 2 * 12:
                    break
        finally:
            stream.close()
        return np.frombuffer(bytes(voiced), dtype=np.int16).astype(np.float32) / 32768.0


def liga_no_visor(voz: "Voz", visor) -> "Voz":
    """Enfia o Visor no meio: a tela mostra a fala do professor (sem dormir — o TTS
    dá o tempo), e a transcrição do aluno quando ele corta."""
    falar_cru = voz.falar

    def falar(texto: str) -> str | None:
        visor.mostrar_fala(texto)
        r = falar_cru(texto)
        if r:
            visor.aluno(r)
        return r

    voz.falar = falar  # type: ignore[method-assign]
    return voz
