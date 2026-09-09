"""checar_audio.py — teste de volume antes do teste de voz.

Roda com o Python do jarvis:
    PYTHONPATH=~/professor-matematica ~/jarvis/.venv/bin/python checar_audio.py

O que faz:
  1. mostra saída (deve ser a caixa BT MO-3401) e entrada (mic do notebook)
  2. fala uma frase pelo Piper na saída atual
  3. grava ~4s do mic e mede o nível (RMS/pico)
  4. diz se o mic está ouvindo, e se está ouvindo a PRÓPRIA caixa (eco → problema
     pro barge-in, então melhor fone; mas dá pra testar com JARVIS_BARGE_IN=0)
"""
from __future__ import annotations

import subprocess
import sys
import time

import numpy as np


def _sh(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def _rms_dbfs(x: np.ndarray) -> float:
    r = float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) + 1e-12
    return 20 * np.log10(r)


def main():
    print("=== dispositivos ===")
    print("saída  :", _sh("wpctl inspect @DEFAULT_AUDIO_SINK@ 2>/dev/null | grep node.description") or "?")
    print("entrada:", _sh("wpctl inspect @DEFAULT_AUDIO_SOURCE@ 2>/dev/null | grep node.description") or "?")
    print("vol saída  :", _sh("wpctl get-volume @DEFAULT_AUDIO_SINK@"))
    print("vol entrada:", _sh("wpctl get-volume @DEFAULT_AUDIO_SOURCE@"))
    _sh("wpctl set-mute @DEFAULT_AUDIO_SINK@ 0; wpctl set-mute @DEFAULT_AUDIO_SOURCE@ 0")

    sys.path.insert(0, "/home/antoniojeferson/jarvis")
    from jarvis.audio import capture, playback
    from jarvis.tts.piper import Piper

    print("\n=== 1) silêncio de fundo (2s, não fale) ===")
    time.sleep(0.5)
    base = _rec(capture, 2.0)
    db_base = _rms_dbfs(base)
    print(f"ruído de fundo: {db_base:+.1f} dBFS")

    print("\n=== 2) o professor fala pela caixa ===")
    piper = Piper()
    pcm = piper.synth("Teste de volume. Um, dois, três. Se você ouviu isso pela caixa "
                      "de som, a saída está funcionando.")
    playback.play(pcm, piper.rate)

    print("\n=== 3) FALE AGORA por ~4s (conte até cinco) ===")
    time.sleep(0.3)
    fala = _rec(capture, 4.0)
    db_fala = _rms_dbfs(fala)
    pico = float(np.max(np.abs(fala)))
    print(f"nível da sua fala: {db_fala:+.1f} dBFS   pico {pico:.2f}")

    print("\n=== veredito ===")
    if db_fala < db_base + 6:
        print("✗ o mic mal captou sua voz. Suba o volume de entrada (wpctl set-volume "
              "@DEFAULT_AUDIO_SOURCE@ 0.30) ou chegue mais perto do notebook.")
    elif db_fala > -12:
        print("⚠ sua voz está MUITO alta (clipando). Baixe a entrada pra ~0.15.")
    else:
        print(f"✓ mic ok (fala {db_fala - db_base:+.1f} dB acima do fundo).")
    if pico > 0.9:
        print("⚠ pico saturado — provavelmente a caixa BT vazando no mic. Pra testar o "
              "barge-in de verdade, use fone; ou rode o demo com JARVIS_BARGE_IN=0.")


def _rec(capture, secs: float) -> np.ndarray:
    """Grava `secs` segundos crus do mic (16 kHz mono)."""
    frames = []
    n_alvo = int(16000 * secs)
    got = 0
    for fr in capture.frames(1600):
        frames.append(np.frombuffer(fr, dtype=np.int16))
        got += len(frames[-1])
        if got >= n_alvo:
            break
    return np.concatenate(frames)[:n_alvo].astype(np.float32) / 32768.0


if __name__ == "__main__":
    main()
