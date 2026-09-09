"""visor.py — a tela do professor. `http.server` da stdlib + uma página. Zero dep.

    v = Visor().start()                       # http://localhost:8080
    Tocador(falar=v.falar, desenhar=v.desenhar).toca(aula)

O tocador empurra figura (`desenhar`) e fala (`falar`); a página faz polling de
`/estado` a cada 150 ms e troca a `<img>` quando o frame muda. `ritmo` faz o
`falar` dormir proporcional ao texto — dá pra assistir sem TTS ainda.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_PAGINA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Professor</title>
<style>
  :root { --fundo:#0E2A22; --giz:#EAEAEA; --fraco:#8FA79C; --destaque:#F2B134;
          --azul:#5AB1E0; --verde:#7BD88F; }
  * { box-sizing:border-box; margin:0; }
  html,body { height:100%; }
  body { background:var(--fundo); color:var(--giz); font:16px/1.5 system-ui,sans-serif;
         display:flex; flex-direction:column; overflow:hidden; }
  header { display:flex; justify-content:center; padding:14px; }
  .pill { display:inline-flex; align-items:center; gap:.5rem; padding:.4rem 1rem;
          border-radius:999px; background:#00000030; border:1px solid #ffffff20;
          font-size:.95rem; letter-spacing:.02em; }
  .dot { width:.6rem; height:.6rem; border-radius:50%; background:var(--fraco); }
  .falando .dot { background:var(--verde); animation:pulse 1s infinite; }
  .ouvindo .dot { background:var(--destaque); animation:pulse .7s infinite; }
  .pensando .dot { background:var(--azul); animation:pulse .5s infinite; }
  @keyframes pulse { 50% { opacity:.3; } }
  main { flex:1; display:flex; align-items:center; justify-content:center; padding:0 24px;
         min-height:0; }
  #fig { max-width:100%; max-height:100%; object-fit:contain;
         filter:drop-shadow(0 8px 40px #00000060); }
  footer { padding:16px 28px 26px; display:flex; flex-direction:column; gap:.4rem;
           min-height:120px; }
  #aluno { color:var(--fraco); font-style:italic; min-height:1.5em; }
  #aluno:not(:empty)::before { content:"🎤  "; }
  #prof { color:var(--giz); font-size:1.4rem; line-height:1.4; text-wrap:balance;
          max-width:70ch; }
  #resumo { position:fixed; bottom:6px; right:10px; color:#ffffff18; font-size:.7rem; }
</style></head><body>
<header><span class="pill" id="pill"><span class="dot"></span><span id="rot">pronto</span></span></header>
<main><img id="fig" alt=""></main>
<footer><div id="aluno"></div><div id="prof"></div></footer>
<div id="resumo"></div>
<script>
const R = { falando:"falando", ouvindo:"ouvindo", pensando:"pensando" };
let frame = -1;
async function poll() {
  try {
    const s = await (await fetch("/estado", {cache:"no-store"})).json();
    if (s.frame !== frame) { frame = s.frame; document.getElementById("fig").src = "/frame.png?v=" + frame; }
    document.getElementById("rot").textContent = s.estado;
    document.getElementById("pill").className = "pill " + (R[s.estado] || "");
    document.getElementById("prof").textContent = s.professor || "";
    document.getElementById("aluno").textContent = s.aluno || "";
    document.getElementById("resumo").textContent = s.resumo || "";
  } catch (e) {}
}
setInterval(poll, 120); poll();
</script></body></html>"""


class Visor:
    def __init__(self, porta: int = 8080, ritmo: float = 0.045, host: str = "127.0.0.1"):
        self.porta, self.host, self.ritmo = porta, host, ritmo
        self._lock = threading.Lock()
        self._png = b""
        self._frame = 0
        self._st = {"estado": "pronto", "professor": "", "aluno": "", "resumo": ""}
        self._srv: ThreadingHTTPServer | None = None

    # ------------------------------------------------ API pro tocador
    def desenhar(self, png: bytes, rotulo: str = "") -> None:
        with self._lock:
            self._png, self._frame = png, self._frame + 1

    def falar(self, texto: str) -> str | None:
        self.mostrar_fala(texto)
        if self.ritmo:
            time.sleep(min(len(texto) * self.ritmo, 8.0))
        return None

    def mostrar_fala(self, texto: str) -> None:
        """Só atualiza a tela (sem dormir). Pro modo voz, onde o TTS dá o tempo."""
        with self._lock:
            self._st["estado"], self._st["professor"] = "falando", texto

    def aluno(self, texto: str) -> None:
        with self._lock:
            self._st["estado"], self._st["aluno"] = "ouvindo", texto

    def estado(self, nome: str) -> None:
        with self._lock:
            self._st["estado"] = nome

    def resumo(self, txt: str) -> None:
        with self._lock:
            self._st["resumo"] = txt

    def _payload(self) -> bytes:
        with self._lock:
            return json.dumps({"frame": self._frame, **self._st}).encode()

    # ------------------------------------------------ servidor
    def start(self) -> "Visor":
        v = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):  # silêncio
                pass

            def do_GET(self):
                if self.path == "/":
                    self._resp(200, "text/html; charset=utf-8", _PAGINA.encode())
                elif self.path.startswith("/estado"):
                    self._resp(200, "application/json", v._payload())
                elif self.path.startswith("/frame.png"):
                    with v._lock:
                        png = v._png
                    self._resp(200, "image/png", png)
                else:
                    self._resp(404, "text/plain", b"nao")

            def _resp(self, code, ctype, body):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if body:
                    self.wfile.write(body)

        self._srv = ThreadingHTTPServer((self.host, self.porta), H)
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()
        print(f"visor → http://localhost:{self.porta}")
        return self

    def stop(self) -> None:
        if self._srv:
            self._srv.shutdown()
