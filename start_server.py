"""Inicia o VINT Match com diagnóstico: escolhe porta livre, grava log em logs/servidor.log e abre o navegador
só quando o servidor responde.  Uso: python start_server.py [--sem-navegador] [--porta 8000]"""
from __future__ import annotations
import importlib.metadata as md
import logging
import platform
import socket
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "servidor.log"
LOG.parent.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(LOG, mode="w", encoding="utf-8")])
log = logging.getLogger("inicio")


def porta_livre(p: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def diagnostico():
    log.info("Python %s em %s (%s)", platform.python_version(), platform.platform(), sys.executable)
    for pkg in ("fastapi", "uvicorn", "pydantic", "python-dotenv", "python-multipart", "psycopg", "pypdf", "python-docx", "anthropic", "mcp"):
        try:
            log.info("  %s %s", pkg, md.version(pkg))
        except md.PackageNotFoundError:
            log.warning("  %s NÃO INSTALADO", pkg)
    env = ROOT / ".env"
    if env.exists():
        chaves = [l.split("=", 1)[0].strip() for l in env.read_text(encoding="utf-8", errors="replace").splitlines()
                  if "=" in l and not l.strip().startswith("#") and l.split("=", 1)[1].strip()]
        log.info(".env encontrado; variáveis preenchidas: %s", ", ".join(chaves))  # só nomes, nunca valores
    else:
        log.warning(".env não encontrado (vou usar os padrões)")


def abrir_quando_pronto(url: str):
    for _ in range(90):
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=2) as r:
                if r.status == 200:
                    log.info("Servidor pronto. Abrindo %s", url)
                    webbrowser.open(url)
                    return
        except Exception:  # noqa: BLE001
            time.sleep(1)
    log.error("O servidor não respondeu em 90 s. Veja as mensagens acima ou logs/servidor.log.")


def main():
    args = sys.argv[1:]
    pedidas = [int(args[args.index("--porta") + 1])] if "--porta" in args else [8000, 8001, 8002, 8080, 8888]
    diagnostico()
    porta = next((p for p in pedidas if porta_livre(p)), None)
    if porta is None:
        log.error("Nenhuma porta livre entre %s. Feche o outro programa que usa a porta ou passe --porta 9000.", pedidas)
        return 1
    if porta != pedidas[0]:
        log.warning("Porta %s ocupada por outro programa; usando %s.", pedidas[0], porta)
    url = f"http://127.0.0.1:{porta}"
    log.info("Iniciando em %s  (deixe esta janela aberta; Ctrl+C para parar)", url)
    if "--sem-navegador" not in args:
        threading.Thread(target=abrir_quando_pronto, args=(url,), daemon=True).start()
    sys.path.insert(0, str(ROOT))
    import uvicorn
    try:
        uvicorn.run("app.main:app", host="127.0.0.1", port=porta, log_config=None)
    except Exception:  # noqa: BLE001
        log.error("Falha ao iniciar:\n%s", traceback.format_exc())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
