"""voz.py — a ponte entre o Tocador e o jarvis (STT + Piper + barge-in).

Contrato do Tocador:
    falar(texto)   -> str | None   fala; se o aluno cortou, devolve a transcrição
    ouvir(seg)     -> str | None   escuta até `seg` s (beat 'pergunta')

Garantias:
  - `falar` NUNCA trava a aula: `speak_stream` roda num cão-de-guarda com timeout
    duro. Se o Piper/áudio pendurar, a gente abandona e segue.
  - Se o Piper falhar (exceção), a aula continua em silêncio (o visor ainda mostra
    o texto). Sem fallback pra gTTS (quebraria o "100% local") nem pyttsx3 (não
    instalado) — degradar é mais robusto que depender de rede.

Import tardio: o venv do professor não precisa das libs de áudio. Rode assim:
    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python demo_voz.py
"""
from __future__ import annotations

import collections
import sys
import threading
import time
from pathlib import Path
from typing import Callable

import numpy as np

_JARVIS = Path.home() / "jarvis"
_TIMEOUT_FALA = 30.0            # cão-de-guarda: nenhuma frase demora mais que isso
_CHUNK = 512
_SR = 16000


def _prepara_path() -> None:
    if str(_JARVIS) not in sys.path:
        sys.path.insert(0, str(_JARVIS))


class Voz:
    def __init__(self) -> None:
        _prepara_path()
        from jarvis.audio.vad import SileroVAD
        from jarvis.stt.engine import FasterWhisperEngine
        from jarvis.tts.piper import Piper

        print("[voz] carregando Piper + faster-whisper…", flush=True)
        self.piper = Piper()
        self.stt = FasterWhisperEngine()
        self.vad = SileroVAD()
        self.on_inicio_fala: Callable[[str], None] | None = None   # visor mostra o texto
        self.on_injecao: Callable[[], str | None] | None = None    # contingência: teclado → texto
        self._inj_pendente: str | None = None

    # ------------------------------------------------------------------ falar
    def falar(self, texto: str) -> str | None:
        """Fala `texto`. Devolve a transcrição se o aluno cortou, senão None.
        Blindado: exceção do Piper → segue em silêncio; travada → abandona em 30 s."""
        if self.on_inicio_fala:
            try:
                self.on_inicio_fala(texto)
            except Exception:  # noqa: BLE001
                pass

        from jarvis.audio.monitor import BargeInMonitor

        monitor = BargeInMonitor()
        res: dict = {}
        inj: dict = {}

        def _rodar() -> None:
            try:
                from jarvis.core.speaker import speak_stream
                _falado, cortou = speak_stream(iter([texto]), self.piper, monitor=monitor)
                res["cortou"] = cortou
            except Exception as e:  # noqa: BLE001
                print(f"[voz] Piper falhou ({e}) — sigo em silêncio", file=sys.stderr, flush=True)
                res["cortou"] = False

        th = threading.Thread(target=_rodar, daemon=True)
        th.start()
        # cão-de-guarda + vigia de injeção do teclado (contingência)
        fim = time.monotonic() + _TIMEOUT_FALA
        while th.is_alive() and time.monotonic() < fim:
            if self.on_injecao:
                t = self.on_injecao()
                if t:
                    inj["texto"] = t
                    monitor.triggered.set()      # corta o Piper na hora
                    break
            th.join(0.1)
        if th.is_alive() and not inj:
            print("[voz] fala pendurou — abandonando essa frase", file=sys.stderr, flush=True)
            try:
                monitor.stop()
            except Exception:  # noqa: BLE001
                pass
            return None
        if inj:
            th.join(1.0)
            return inj["texto"]                  # veio do teclado, não precisa de STT

        if not res.get("cortou"):
            return None

        # cortou (mic): junta o onset + o resto (limitado a 4 s — eco não trava)
        onset = np.frombuffer(monitor.buffer, dtype=np.int16).astype(np.float32) / 32768.0
        try:
            resto = self._record_ate(4.0)
        except Exception:  # noqa: BLE001
            resto = None
        if isinstance(resto, str):              # "INJ" — teclado; ignora aqui
            resto = None
        audio = np.concatenate([onset, resto]) if resto is not None and resto.size else onset
        if audio.size < _SR:           # < 1 s: quase certo que é eco do Piper
            return None
        return self.stt.transcribe(audio).text.strip() or None

    def falar_com_pausa(self, texto: str, ritmo: float = 1.0) -> bool:
        """Adapter pedido: notifica o visor, fala, dá uma pausa CURTA proporcional
        ao texto (não `len*0.08` — isso dobraria a duração; o Piper já leva o tempo
        da fala. Aqui é só um respiro entre frases, no máx. 1,4 s), e devolve
        True se o aluno cortou."""
        cortou_txt = self.falar(texto)
        respiro = min(len(texto) * 0.018 * max(ritmo, 0.1), 1.4)
        time.sleep(respiro)
        return cortou_txt is not None

    # ------------------------------------------------------------------ ouvir
    def ouvir(self, timeout: float | None = None) -> str | None:
        """Escuta o aluno (mic OU teclado, o que vier primeiro). Com `timeout`,
        desiste se ninguém falar/apertar nesse tempo. Devolve a transcrição/texto."""
        if self.on_injecao:                    # já tem tecla na fila?
            t = self.on_injecao()
            if t:
                return t
        audio = self._record_ate(timeout if timeout else 3600.0)
        if isinstance(audio, str):              # "INJ" — teclado interrompeu a espera
            return self._inj_pendente
        if audio is None or audio.size < _SR // 3:
            return None
        return self.stt.transcribe(audio).text.strip() or None

    def _record_ate(self, timeout: float):
        """record_vad, mas desiste se nenhuma fala começar em `timeout` s.
        Se o teclado (on_injecao) disparar antes da fala, devolve "INJ" e guarda o
        texto em self._inj_pendente."""
        from jarvis.audio import capture

        frame_ms = _CHUNK * 1000 // _SR
        limite = int(timeout * 1000 / frame_ms)
        silence_limit = max(1, 700 // frame_ms)
        preroll = collections.deque(maxlen=max(1, 300 // frame_ms))
        voiced = bytearray()
        triggered = False
        silence = 0
        self._inj_pendente = None
        self.vad.reset()
        stream = capture.frames(_CHUNK)
        try:
            for i, frame in enumerate(stream):
                if not triggered and self.on_injecao:
                    t = self.on_injecao()
                    if t:
                        self._inj_pendente = t
                        return "INJ"
                fala = self.vad.is_speech(frame)
                if not triggered:
                    preroll.append(frame)
                    if fala:
                        triggered = True
                        voiced = bytearray(b"".join(preroll))
                    elif i >= limite:
                        return None
                    continue
                voiced += frame
                silence = 0 if fala else silence + 1
                if silence >= silence_limit or len(voiced) >= _SR * 2 * 12:
                    break
        finally:
            stream.close()
        return np.frombuffer(bytes(voiced), dtype=np.int16).astype(np.float32) / 32768.0


def liga_no_visor(voz: "Voz", visor) -> "Voz":
    """O visor mostra a fala do professor ANTES do áudio (via on_inicio_fala) e a
    transcrição do aluno quando ele corta."""
    voz.on_inicio_fala = visor.mostrar_fala
    falar_cru = voz.falar

    def falar(texto: str) -> str | None:
        r = falar_cru(texto)
        if r:
            visor.aluno(r)
        return r

    voz.falar = falar  # type: ignore[method-assign]
    return voz
