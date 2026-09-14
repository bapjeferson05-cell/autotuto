"""visor.py — a tela "lousa" do professor. `http.server` da stdlib + uma página.
Zero dep de frontend.

    v = Visor().start()                       # http://localhost:8080
    v.desenhar(png, "trapézio"); v.falar("olá, turma")

A página faz polling de `/estado` a cada `config.VISOR_POLL_MS` ms e troca a
`<img>` quando o frame muda. `ritmo` faz o `falar` dormir proporcional ao texto
(modo sem TTS), acordando se uma tecla for apertada no meio.

CONTINGÊNCIA — teclado é o 1º caminho de interrupção. Teclas na página simulam a
fala do aluno:
  1 = "por que que divide por dois?"   2 = "não entendi essa parte"
  4 = "de onde veio essa fórmula?"
  3 = "e se fosse um triângulo?"        0 = "acho que vira um triângulo"
Elas fazem POST /interromper; o `falar` devolve esse texto no lugar do microfone.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from autotuto import config

_TECLAS = {
    "1": "por que que divide por dois?",
    "2": "não entendi essa parte",
    "3": "e se fosse um triângulo?",
    "4": "de onde veio essa fórmula?",
    "0": "acho que vira um triângulo",
}


def _pagina() -> str:
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Professor</title>
<style>
  :root {{ --fundo:{config.COR_FUNDO}; --giz:{config.COR_GIZ}; --fraco:{config.COR_FRACO};
          --destaque:{config.COR_DESTAQUE}; --azul:{config.COR_AZUL}; --verde:{config.COR_VERDE}; }}
  * {{ box-sizing:border-box; margin:0; }}
  html,body {{ height:100%; }}
  body {{ background:var(--fundo); color:var(--giz); font:16px/1.5 system-ui,sans-serif;
         display:flex; flex-direction:column; overflow:hidden; }}
  header {{ display:flex; justify-content:center; padding:14px; }}
  .pill {{ display:inline-flex; align-items:center; gap:.5rem; padding:.4rem 1rem;
          border-radius:999px; background:#00000030; border:1px solid #ffffff20;
          font-size:.95rem; letter-spacing:.02em; }}
  .dot {{ width:.6rem; height:.6rem; border-radius:50%; background:var(--fraco); }}
  .falando .dot {{ background:var(--verde); animation:pulse 1s infinite; }}
  .ouvindo .dot {{ background:var(--destaque); animation:pulse .7s infinite; }}
  .pensando .dot {{ background:var(--azul); animation:pulse .5s infinite; }}
  @keyframes pulse {{ 50% {{ opacity:.3; }} }}
  main {{ flex:1; display:flex; align-items:center; justify-content:center; padding:0 24px;
         min-height:0; }}
  #fig {{ max-width:100%; max-height:100%; object-fit:contain;
         filter:drop-shadow(0 8px 40px #00000060); }}
  footer {{ padding:16px 28px 26px; display:flex; flex-direction:column; gap:.4rem;
           min-height:120px; }}
  #aluno {{ color:var(--fraco); font-style:italic; min-height:1.5em; }}
  #aluno:not(:empty)::before {{ content:"\\1F3A4  "; }}
  #prof {{ color:var(--giz); font-size:1.4rem; line-height:1.4; text-wrap:balance;
          max-width:70ch; }}
  #resumo {{ position:fixed; bottom:6px; right:10px; color:#ffffff18; font-size:.7rem; }}
  #dicas {{ position:fixed; bottom:6px; left:10px; color:#ffffff28; font-size:.7rem; }}
  #cx {{ margin-top:.3rem; }}
  #txt {{ width:min(60ch,90vw); padding:.6rem .9rem; border-radius:.6rem;
         border:1px solid #ffffff2a; background:#00000030; color:var(--giz);
         font:inherit; outline:none; }}
  #txt:focus {{ border-color:var(--destaque); }}
</style></head><body>
<header><span class="pill" id="pill"><span class="dot"></span><span id="rot">pronto</span></span></header>
<main><img id="fig" alt=""></main>
<footer>
  <div id="aluno"></div><div id="prof"></div>
  <form id="cx" hidden><input id="txt" autocomplete="off"
    placeholder="Digite o assunto ou cole a questão… (Enter)"></form>
</footer>
<div id="resumo"></div>
<div id="dicas">1 por quê · 2 não entendi · 3 triângulo · 4 de onde veio · 0 responder</div>
<script>
const R = {{ falando:"falando", ouvindo:"ouvindo", pensando:"pensando" }};
const TECLAS = {json.dumps(_TECLAS, ensure_ascii=False)};
let frame = -1;
async function poll() {{
  try {{
    const s = await (await fetch("/estado", {{cache:"no-store"}})).json();
    if (s.frame !== frame) {{ frame = s.frame; document.getElementById("fig").src = "/frame.png?v=" + frame; }}
    document.getElementById("rot").textContent = s.estado;
    document.getElementById("pill").className = "pill " + (R[s.estado] || "");
    document.getElementById("prof").textContent = s.professor || "";
    document.getElementById("aluno").textContent = s.aluno || "";
    document.getElementById("resumo").textContent = s.resumo || "";
    document.getElementById("cx").hidden = (s.estado !== "pronto" && s.estado !== "aguardando");
  }} catch (e) {{}}
}}
document.getElementById("cx").addEventListener("submit", (e) => {{
  e.preventDefault();
  const t = document.getElementById("txt").value.trim();
  if (!t) return;
  document.getElementById("txt").value = "";
  document.getElementById("aluno").textContent = t;
  document.getElementById("rot").textContent = "pensando";
  document.getElementById("pill").className = "pill pensando";
  fetch("/perguntar", {{method:"POST", headers:{{"Content-Type":"application/json"}},
                       body: JSON.stringify({{texto: t}})}}).catch(()=>{{}});
}});
document.addEventListener("keydown", (e) => {{
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const t = TECLAS[e.key];
  if (!t) return;
  e.preventDefault();
  document.getElementById("aluno").textContent = t;
  document.getElementById("rot").textContent = "ouvindo";
  document.getElementById("pill").className = "pill ouvindo";
  fetch("/interromper", {{method:"POST", headers:{{"Content-Type":"application/json"}},
                         body: JSON.stringify({{texto: t}})}}).catch(()=>{{}});
}});
setInterval(poll, {int(config.VISOR_POLL_MS)}); poll();
</script></body></html>"""


class Visor:
    def __init__(self, porta: int = config.VISOR_PORTA,
                 ritmo: float = config.RITMO_S_POR_CHAR, host: str = "127.0.0.1"):
        self.porta, self.host, self.ritmo = porta, host, ritmo
        self._lock = threading.Lock()
        self._png = b""
        self._frame = 0
        self._rotulo = ""
        self._st = {"estado": "pronto", "professor": "", "aluno": "", "resumo": ""}
        self._injecao: str | None = None       # interrupção via teclado (1/2/3/4/0)
        self._pergunta: str | None = None      # pergunta digitada na caixa
        self._srv: ThreadingHTTPServer | None = None

    # ------------------------------------------------ API pro tocador
    def desenhar(self, png: bytes, rotulo: str = "") -> None:
        with self._lock:
            self._png, self._rotulo = png, rotulo
            self._frame += 1

    def falar(self, texto: str) -> str | None:
        """Modo texto/sem-TTS: mostra a fala, dorme ~`len*ritmo` (teto ~8s) e
        devolve a fala do aluno se ele apertar uma tecla no meio (barge-in)."""
        self.mostrar_fala(texto)
        if not self.ritmo:
            return None
        fim = time.monotonic() + min(len(texto) * self.ritmo, 8.0)
        while time.monotonic() < fim:
            t = self.pop_injecao()
            if t:
                return t
            time.sleep(config.TICK_S)
        return None

    def mostrar_fala(self, texto: str) -> None:
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

    # teclado (1º caminho): fala do aluno vinda de POST /interromper
    def pop_injecao(self) -> str | None:
        with self._lock:
            t, self._injecao = self._injecao, None
            return t

    # modo texto: pergunta digitada na caixa (POST /perguntar)
    def pop_pergunta(self) -> str | None:
        with self._lock:
            t, self._pergunta = self._pergunta, None
            return t

    def _payload(self) -> bytes:
        with self._lock:
            return json.dumps({"frame": self._frame, **self._st}).encode()

    # ------------------------------------------------ servidor
    def start(self) -> "Visor":
        v = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def handle_one_request(self):
                try:
                    super().handle_one_request()
                except (BrokenPipeError, ConnectionResetError):
                    self.close_connection = True   # browser largou o poll — normal

            def do_GET(self):
                if self.path == "/":
                    self._resp(200, "text/html; charset=utf-8", _pagina().encode())
                elif self.path.startswith("/estado"):
                    self._resp(200, "application/json", v._payload())
                elif self.path.startswith("/frame.png"):
                    with v._lock:
                        png = v._png
                    self._resp(200, "image/png", png)
                else:
                    self._resp(404, "text/plain", b"nao")

            def do_POST(self):
                if self.path not in ("/interromper", "/perguntar"):
                    self._resp(404, "text/plain", b"nao")
                    return
                n = int(self.headers.get("Content-Length", 0))
                try:
                    txt = json.loads(self.rfile.read(n) or b"{}").get("texto", "").strip()
                except Exception:
                    txt = ""
                if txt:
                    with v._lock:
                        v._st["aluno"] = txt
                        if self.path == "/interromper":
                            v._injecao = txt
                            v._st["estado"] = "ouvindo"
                        else:
                            v._pergunta = txt
                            v._st["estado"] = "pensando"
                self._resp(200, "text/plain", b"ok")

            def _resp(self, code, ctype, body):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if body:
                    self.wfile.write(body)

        try:
            self._srv = ThreadingHTTPServer((self.host, self.porta), H)
        except OSError as e:
            raise OSError(
                f"não consegui abrir a porta {self.porta} ({e}). Provavelmente um "
                f"demo antigo ainda está de pé — mata o processo antigo (ou passa "
                f"outra porta pro Visor) antes de rodar de novo."
            ) from e
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()
        print(f"visor → http://localhost:{self.porta}")
        return self

    def stop(self) -> None:
        if self._srv:
            self._srv.shutdown()
            self._srv.server_close()
            self._srv = None
