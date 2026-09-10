"""voz.py — adapter fino de áudio: Piper (TTS) + faster-whisper (STT), diretos.

Único módulo do AutoTuto que toca hardware de áudio. Zero jarvis.

Contrato que o Tocador (Task 14) consome:
    Voz()                -> carrega + pré-aquece os dois modelos
    voz.falar(txt)       -> str | None   fala; devolve texto se o aluno cortou
    voz.ouvir(seg)       -> str | None   escuta até `seg` s, transcreve
    voz.on_injecao       -> Callable[[], str|None] | None   (teclado; prioridade)
    voz.on_inicio_fala   -> Callable[[str], None] | None    (visor mostra o texto)

Garantias:
  - `falar` NUNCA trava a aula: a reprodução roda num thread com cão-de-guarda
    (`config.FALA_TIMEOUT_S`). Se o áudio pendurar, abandona e devolve None.
  - Piper falhou (exceção)? Segue em silêncio — o visor ainda mostra o texto.
  - `BARGE_IN` desligado: o mic NÃO é aberto durante `falar` (só teclado).
"""
from __future__ import annotations

import subprocess
import sys
import threading
import time
from typing import Callable

import numpy as np
import piper
import faster_whisper

from autotuto import config

# Monkeypatchável nos testes (ver tests/test_voz.py).
BARGE_IN = config.BARGE_IN

_SR = 16000                     # taxa de captura do mic (whisper gosta de 16 kHz)
_FRAME = 1024                   # amostras por frame lido do arecord
_FRAME_BYTES = _FRAME * 2       # s16le mono
_LIMIAR_RMS = 500.0             # energia RMS acima disso = voz (int16)

# Processos de reprodução ativos, pra que barge-in/teclado consigam cortar.
_procs_reproducao: list[subprocess.Popen] = []
_lock_reproducao = threading.Lock()


# --------------------------------------------------------------------- áudio out
def _tocar_pcm(pcm: bytes, rate: int) -> None:
    """Toca PCM s16le mono cru. Tenta `pw-play`, cai pra `aplay`. Bloqueante."""
    tentativas = (
        ["pw-play", "--rate", str(rate), "--channels", "1", "--format", "s16", "--raw", "-"],
        ["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(rate), "-c", "1", "-"],
    )
    for cmd in tentativas:
        try:
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            continue
        with _lock_reproducao:
            _procs_reproducao.append(proc)
        try:
            proc.communicate(pcm)
        except Exception:  # noqa: BLE001  (pipe quebrado num corte é esperado)
            pass
        finally:
            with _lock_reproducao:
                if proc in _procs_reproducao:
                    _procs_reproducao.remove(proc)
        return
    print("[voz] sem pw-play/aplay — fala em silêncio", file=sys.stderr, flush=True)


def _parar_reproducao() -> None:
    """Mata qualquer reprodução em andamento (corte por teclado ou barge-in)."""
    with _lock_reproducao:
        procs = list(_procs_reproducao)
    for p in procs:
        try:
            p.terminate()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------- áudio in
def _abrir_arecord() -> subprocess.Popen:
    return subprocess.Popen(
        ["arecord", "-q", "-D", "default", "-f", "S16_LE",
         "-r", str(_SR), "-c", "1", "-t", "raw"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )


def _rms(frame: bytes) -> float:
    a = np.frombuffer(frame, dtype=np.int16).astype(np.float32)
    if a.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(a * a)))


def _sintetizar(voz_piper, txt: str) -> tuple[bytes, int]:
    """txt -> (PCM s16le, sample_rate). Consome todos os chunks do Piper."""
    cfg = piper.SynthesisConfig(length_scale=config.TTS_LENGTH_SCALE)
    pcm = bytearray()
    rate = 22050
    for chunk in voz_piper.synthesize(txt, cfg):
        pcm += chunk.audio_int16_bytes
        rate = chunk.sample_rate
    return bytes(pcm), rate


class _MonitorMic:
    """VAD por energia num thread: lê frames do arecord e marca voz sustentada.

    Só é ligado quando `BARGE_IN` está ativo. `voz_sustentada()` fica True depois
    de ~5 frames seguidos acima do limiar (~0,3 s de fala).
    """

    def __init__(self, minimo_frames: int = 5) -> None:
        self._min = minimo_frames
        self._parar = threading.Event()
        self._detectado = threading.Event()
        self._th = threading.Thread(target=self._roda, daemon=True)

    def start(self) -> None:
        self._th.start()

    def _roda(self) -> None:
        try:
            proc = _abrir_arecord()
        except Exception as e:  # noqa: BLE001
            print(f"[voz] monitor de mic não abriu ({e})", file=sys.stderr, flush=True)
            return
        seguidos = 0
        try:
            while not self._parar.is_set():
                buf = proc.stdout.read(_FRAME_BYTES)
                if not buf or len(buf) < _FRAME_BYTES:
                    break
                seguidos = seguidos + 1 if _rms(buf) >= _LIMIAR_RMS else 0
                if seguidos >= self._min:
                    self._detectado.set()
                    break
        finally:
            try:
                proc.terminate()
            except Exception:  # noqa: BLE001
                pass

    def voz_sustentada(self) -> bool:
        return self._detectado.is_set()

    def parar(self) -> None:
        self._parar.set()


class Voz:
    def __init__(self, modelo_stt: str | None = None) -> None:
        modelo = modelo_stt or config.STT_MODELO
        self.on_inicio_fala: Callable[[str], None] | None = None   # visor mostra o texto
        self.on_injecao: Callable[[], str | None] | None = None    # teclado -> texto

        t0 = time.monotonic()
        print("[voz] carregando Piper + faster-whisper…", flush=True)
        self.piper = piper.PiperVoice.load(config.TTS_VOICE)
        self.stt = faster_whisper.WhisperModel(
            modelo, device=config.STT_DEVICE,
            compute_type="int8", download_root=config.STT_CACHE,
        )
        print(f"[voz] modelos carregados em {time.monotonic() - t0:.1f}s", flush=True)

        # A 1ª inferência de cada modelo é a mais lenta — paga esse custo AGORA.
        try:
            t1 = time.monotonic()
            self.stt.transcribe(np.zeros(8000, dtype=np.float32))
            for _ in self.piper.synthesize("um dois três"):
                pass
            print(f"[voz] pré-aquecido em {time.monotonic() - t1:.1f}s", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[voz] pré-aquecimento pulado ({e})", file=sys.stderr, flush=True)

    # ------------------------------------------------------------------- falar
    def falar(self, txt: str) -> str | None:
        """Fala `txt`. Devolve texto se o aluno cortou (teclado ou barge-in), senão None."""
        if self.on_inicio_fala:
            try:
                self.on_inicio_fala(txt)
            except Exception:  # noqa: BLE001
                pass

        # Teclado tem prioridade: se já tem tecla na fila, nem fala.
        if self.on_injecao:
            t = self.on_injecao()
            if t:
                return t

        try:
            pcm, rate = _sintetizar(self.piper, txt)
        except Exception as e:  # noqa: BLE001
            print(f"[voz] Piper falhou ({e}) — sigo em silêncio", file=sys.stderr, flush=True)
            return None

        th = threading.Thread(target=_tocar_pcm, args=(pcm, rate), daemon=True)
        th.start()

        monitor: _MonitorMic | None = None
        if BARGE_IN:
            monitor = _MonitorMic()
            monitor.start()

        prazo = time.monotonic() + config.FALA_TIMEOUT_S
        try:
            while th.is_alive():
                if self.on_injecao:
                    t = self.on_injecao()
                    if t:
                        _parar_reproducao()
                        return t
                if monitor is not None and monitor.voz_sustentada():
                    _parar_reproducao()
                    monitor.parar()
                    resto = self._gravar(config.GRAVA_RESTO_S)
                    return self._transcrever(resto)
                if time.monotonic() > prazo:
                    print("[voz] fala pendurou — abandonando", file=sys.stderr, flush=True)
                    _parar_reproducao()
                    return None
                th.join(timeout=0.05)
        finally:
            if monitor is not None:
                monitor.parar()
        return None

    # ------------------------------------------------------------------- ouvir
    def ouvir(self, seg: float) -> str | None:
        """Escuta o aluno até `seg` s (ou `config.SILENCIO_MS` de silêncio pós-fala)."""
        if self.on_injecao:
            t = self.on_injecao()
            if t:
                return t
        return self._transcrever(self._gravar(seg))

    # --------------------------------------------------------------- internos
    def _gravar(self, seg: float) -> np.ndarray | None:
        """Grava do mic até `seg` s, fechando após `config.SILENCIO_MS` de silêncio
        depois que a fala começou. Devolve float32 em [-1, 1] ou None."""
        try:
            proc = _abrir_arecord()
        except Exception as e:  # noqa: BLE001
            print(f"[voz] arecord não abriu ({e})", file=sys.stderr, flush=True)
            return None

        frame_ms = _FRAME * 1000 // _SR
        max_silencio = max(1, int(config.SILENCIO_MS / frame_ms))
        falou = False
        silencio = 0
        vozeado = bytearray()
        prazo = time.monotonic() + seg
        try:
            while time.monotonic() < prazo:
                buf = proc.stdout.read(_FRAME_BYTES)
                if not buf or len(buf) < _FRAME_BYTES:
                    break
                if _rms(buf) >= _LIMIAR_RMS:
                    falou = True
                    silencio = 0
                    vozeado += buf
                elif falou:
                    silencio += 1
                    vozeado += buf
                    if silencio >= max_silencio:
                        break
        finally:
            try:
                proc.terminate()
            except Exception:  # noqa: BLE001
                pass

        if not vozeado:
            return None
        return np.frombuffer(bytes(vozeado), dtype=np.int16).astype(np.float32) / 32768.0

    def _transcrever(self, audio: np.ndarray | None) -> str | None:
        if audio is None or audio.size < _SR // 3:      # < ~0,33 s: quase certo que é ruído
            return None
        try:
            segmentos, _ = self.stt.transcribe(audio)
            txt = "".join(s.text for s in segmentos).strip()
        except Exception as e:  # noqa: BLE001
            print(f"[voz] transcrição falhou ({e})", file=sys.stderr, flush=True)
            return None
        return txt or None
