"""Configuração central (lida do .env)."""
import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
GEMINI_MODELOS_RESERVA = [m.strip() for m in os.getenv("GEMINI_MODELOS_RESERVA", "").split(",") if m.strip()]
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"
GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip().rstrip("/")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5").strip() or "claude-sonnet-5-5"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SQLITE_PATH = ROOT / os.getenv("SQLITE_PATH", "data/sgd_snapshot.sqlite")
DATA_SOURCE = os.getenv("DATA_SOURCE", "auto").strip().lower()
CORPUS_DIR = ROOT / "docs" / "corpus"

# Banco PRÓPRIO do app (usuários, sessões, histórico de buscas e decisões). Separado do SGD, que segue somente leitura.
APP_DB_PATH = ROOT / os.getenv("APP_DB_PATH", "data/app.db")
ALLOWED_EMAIL_DOMAIN = os.getenv("ALLOWED_EMAIL_DOMAIN", "vintglobal.com").strip().lower().lstrip("@")
SESSION_HOURS = int(os.getenv("SESSION_HOURS", "12"))
REMEMBER_DAYS = int(os.getenv("REMEMBER_DAYS", "30"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
MAX_TENTATIVAS = 5
BLOQUEIO_MINUTOS = 15

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def reference_month() -> tuple[int, int]:
    """Mês de referência ('hoje'), formato AAAA-MM no .env; padrão = mês atual."""
    raw = os.getenv("REFERENCE_MONTH", "").strip()
    if raw:
        a, m = raw.split("-")
        return int(a), int(m)
    t = date.today()
    return t.year, t.month
