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

        # onset capturado pelo monitor (int16 16k) + o resto da fala
        onset = np.frombuffer(monitor.buffer, dtype=np.int16).astype(np.float32) / 32768.0
        try:
            resto = capture.record_vad(self.vad)
        except Exception:  # noqa: BLE001
            resto = np.array([], dtype=np.float32)
        audio = np.concatenate([onset, resto]) if resto.size else onset
        if audio.size < self._onset_rate // 2:      # < 0,5 s: provavelmente eco
            return None
        texto_aluno = self.stt.transcribe(audio).text.strip()
        return texto_aluno or None

    # ------------------------------------------------------------------ ouvir (1ª fala)
    def ouvir(self) -> str:
        """Bloqueia até o aluno falar, devolve a transcrição. Pro início da sessão."""
        from jarvis.audio import capture

        audio = capture.record_vad(self.vad)
        return self.stt.transcribe(audio).text.strip() if audio.size else ""


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
