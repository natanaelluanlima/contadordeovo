#!/usr/bin/env python3
"""Launcher local do Contador de Ovos.

Serve a tela de carregamento, sobe os servicos e expõe:
  GET  /            splash
  GET  /api/status  progresso das portas
  POST /api/shutdown encerra tudo (usado pelo botao Desligar)
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

LAUNCHER_PORT = 8010
WORKSPACE = Path(__file__).resolve().parents[2]
SCRIPTS = WORKSPACE / "scripts"
SPLASH = Path(__file__).resolve().parent / "splash.html"
MEDIA_DIR = Path(__file__).resolve().parent / "media"
PID_FILE = WORKSPACE / "logs" / "launcher.pid"

SERVICES = (
    ("processador", 9002),
    ("bff", 9001),
    ("gateway", 9000),
    ("site", 8009),
)

_state_lock = threading.Lock()
_state: dict = {
    "boot_started_at": time.time(),
    "boot_error": None,
    "services_started": False,
    "shutting_down": False,
}


def _port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _find_chrome() -> str | None:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def _open_chrome(url: str) -> None:
    chrome = _find_chrome()
    if chrome:
        subprocess.Popen(
            [
                chrome,
                f"--app={url}",
                "--new-window",
                "--start-maximized",
                "--window-position=0,0",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        threading.Thread(target=_maximize_chrome_window, daemon=True).start()
        return
    webbrowser.open(url)


def _maximize_chrome_window() -> None:
    """Garante janela maximizada (Chrome --app as vezes ignora --start-maximized)."""
    time.sleep(1.1)
    script = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinApi {
  [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
}
"@
$deadline = (Get-Date).AddSeconds(8)
do {
  $procs = Get-Process chrome -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
  foreach ($proc in $procs) {
    $title = $proc.MainWindowTitle
    if ($title -match 'Contador de Ovos|localhost:8010|localhost:8009') {
      [WinApi]::ShowWindowAsync($proc.MainWindowHandle, 3) | Out-Null
      return
    }
  }
  Start-Sleep -Milliseconds 400
} while ((Get-Date) -lt $deadline)
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=12,
        )
    except Exception:  # noqa: BLE001
        pass


def _start_services() -> None:
    with _state_lock:
        if _state["services_started"] or _state["shutting_down"]:
            return
        _state["services_started"] = True

    script = SCRIPTS / "iniciar-contador.ps1"
    try:
        # Sem AbrirNavegador: o splash/Chrome ja esta aberto nesta porta.
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "Falha ao iniciar servicos").strip()
            with _state_lock:
                _state["boot_error"] = detail[-500:]
    except Exception as exc:  # noqa: BLE001
        with _state_lock:
            _state["boot_error"] = str(exc)


def _stop_services() -> None:
    script = SCRIPTS / "parar-contador.ps1"
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except Exception:  # noqa: BLE001
        pass


def _status_payload() -> dict:
    services = {name: _port_open(port) for name, port in SERVICES}
    ready_count = sum(1 for ok in services.values() if ok)
    total = len(services)
    percent = int(round((ready_count / total) * 100)) if total else 0
    ready = ready_count == total

    with _state_lock:
        boot_error = _state["boot_error"]
        shutting_down = _state["shutting_down"]
        elapsed = time.time() - _state["boot_started_at"]

    if shutting_down:
        message = "Encerrando o Contador…"
    elif ready:
        message = "Sistema pronto"
    elif ready_count == 0:
        message = "Ligando módulos…"
    else:
        pending = [name for name, ok in services.items() if not ok]
        message = f"Aguardando: {', '.join(pending)}"

    # Evita 0% eterno nos primeiros segundos
    if not ready and percent < 5 and elapsed > 2:
        percent = 5

    return {
        "ready": ready and not shutting_down,
        "percent": 100 if ready else percent,
        "message": message,
        "services": services,
        "error": boot_error,
        "elapsed_s": round(elapsed, 1),
        "app_url": "http://localhost:8009/contagem",
    }


class LauncherHandler(BaseHTTPRequestHandler):
    server_version = "ContadorLauncher/1.0"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Mantem o console limpo; erros ainda aparecem via print no main.
        return

    def _cors(self) -> None:
        origin = self.headers.get("Origin", "*")
        if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1") or origin == "*":
            self.send_header("Access-Control-Allow-Origin", origin if origin != "null" else "*")
        else:
            self.send_header("Access-Control-Allow-Origin", "http://localhost:8009")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            body = SPLASH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return

        if path.startswith("/media/"):
            name = Path(path).name
            if name != Path(path).name or ".." in path:
                self.send_response(400)
                self._cors()
                self.end_headers()
                return
            file_path = (MEDIA_DIR / name).resolve()
            if not str(file_path).startswith(str(MEDIA_DIR.resolve())) or not file_path.is_file():
                self.send_response(404)
                self._cors()
                self.end_headers()
                return
            body = file_path.read_bytes()
            content_type = "image/png" if file_path.suffix.lower() == ".png" else "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/status":
            payload = json.dumps(_status_payload(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self._cors()
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_response(404)
        self._cors()
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/shutdown":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return

        with _state_lock:
            already = _state["shutting_down"]
            _state["shutting_down"] = True

        payload = json.dumps({"ok": True, "message": "Encerrando Contador…"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)

        if not already:
            threading.Thread(target=_shutdown_sequence, daemon=True).start()


def _shutdown_sequence() -> None:
    print("Encerrando Contador de Ovos…")
    _stop_services()
    # Libera o HTTP server
    time.sleep(0.4)
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except OSError:
            pass
    # Mata este processo launcher (e o listener)
    os._exit(0)


def _write_pid() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def main() -> int:
    if not SPLASH.is_file():
        print(f"Splash nao encontrado: {SPLASH}", file=sys.stderr)
        return 1

    # Evita dois launchers
    if _port_open(LAUNCHER_PORT):
        print(f"Launcher ja ativo em http://127.0.0.1:{LAUNCHER_PORT}/")
        _open_chrome(f"http://127.0.0.1:{LAUNCHER_PORT}/")
        return 0

    _write_pid()
    server = ThreadingHTTPServer(("127.0.0.1", LAUNCHER_PORT), LauncherHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=_start_services, daemon=True).start()

    url = f"http://127.0.0.1:{LAUNCHER_PORT}/"
    print(f"Contador de Ovos — carregamento: {url}")
    time.sleep(0.35)
    _open_chrome(url)

    try:
        while True:
            with _state_lock:
                if _state["shutting_down"]:
                    break
            time.sleep(0.5)
    except KeyboardInterrupt:
        with _state_lock:
            _state["shutting_down"] = True
        _stop_services()
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
