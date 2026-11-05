"""Autenticação: senhas PBKDF2, sessões por cookie httpOnly, convites e bloqueio após 5 tentativas."""
from __future__ import annotations
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from . import config, store

COOKIE = "vm_sessao"
ITER = 240_000
REGRAS = [("12 ou mais caracteres", lambda p: len(p) >= 12),
          ("1 letra maiúscula", lambda p: bool(re.search(r"[A-ZÀ-Ý]", p))),
          ("1 número", lambda p: bool(re.search(r"\d", p))),
          ("1 símbolo, como ! @ # $", lambda p: bool(re.search(r"[^A-Za-z0-9À-ÿ\s]", p)))]


def hash_senha(senha: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, ITER)
    return f"pbkdf2_sha256${ITER}${salt.hex()}${h.hex()}"


def confere_senha(senha: str, armazenado: str | None) -> bool:
    if not armazenado:
        return False
    try:
        _, it, salt, h = armazenado.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(calc.hex(), h)
    except ValueError:
        return False


def senha_fraca(senha: str) -> list[str]:
    return [nome for nome, ok in REGRAS if not ok(senha or "")]


def token_hash(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def novo_token() -> tuple[str, str]:
    t = secrets.token_urlsafe(32)
    return t, token_hash(t)


def utc(dt_iso: str | None) -> datetime | None:
    return datetime.fromisoformat(dt_iso) if dt_iso else None


def email_ok(email: str) -> bool:
    email = (email or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return False
    return not config.ALLOWED_EMAIL_DOMAIN or email.endswith("@" + config.ALLOWED_EMAIL_DOMAIN)


def usuario_publico(u: dict) -> dict:
    return {"id": u["id"], "nome": u["nome"], "email": u["email"], "perfil": u["perfil"], "area": u.get("area"),
            "status": status_efetivo(u), "ultimo_acesso": u.get("ultimo_acesso"), "criado_em": u["criado_em"],
            "senha_trocada_em": u.get("senha_trocada_em")}


def status_efetivo(u: dict) -> str:
    if u["status"] == "bloqueado" and u.get("bloqueado_ate"):
        ate = utc(u["bloqueado_ate"])
        if ate and ate < datetime.now(timezone.utc):
            return "ativo"
    return u["status"]


# ------------------------------------------------------------------ sessões
def criar_sessao(usuario_id: int, request: Request, lembrar: bool) -> tuple[str, int | None]:
    t, th = novo_token()
    agora = datetime.now(timezone.utc)
    dur = timedelta(days=config.REMEMBER_DAYS) if lembrar else timedelta(hours=config.SESSION_HOURS)
    store.x("INSERT INTO sessoes(token_hash, usuario_id, user_agent, ip, lembrar, criado_em, ultimo_uso, expira_em) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (th, usuario_id, (request.headers.get("user-agent") or "")[:300],
             request.client.host if request.client else None, int(lembrar), agora.isoformat(timespec="seconds"),
             agora.isoformat(timespec="seconds"), (agora + dur).isoformat(timespec="seconds")))
    store.x("UPDATE usuarios SET ultimo_acesso=?, falhas=0, bloqueado_ate=NULL WHERE id=?", (store.now(), usuario_id))
    return t, (int(dur.total_seconds()) if lembrar else None)


def set_cookie(response, token: str, max_age: int | None):
    response.set_cookie(COOKIE, token, max_age=max_age, httponly=True, samesite="lax",
                        secure=config.COOKIE_SECURE, path="/")


def sessao_atual(request: Request) -> dict | None:
    t = request.cookies.get(COOKIE)
    if not t:
        return None
    s = store.q("SELECT * FROM sessoes WHERE token_hash=?", (token_hash(t),), one=True)
    if not s or utc(s["expira_em"]) < datetime.now(timezone.utc):
        return None
    u = store.q("SELECT * FROM usuarios WHERE id=?", (s["usuario_id"],), one=True)
    if not u or status_efetivo(u) != "ativo":
        return None
    store.x("UPDATE sessoes SET ultimo_uso=? WHERE id=?", (store.now(), s["id"]))
    return {"sessao": s, "usuario": u}


def usuario_logado(request: Request) -> dict:
    ctx = sessao_atual(request)
    if not ctx:
        raise HTTPException(401, "Sessão expirada. Entre novamente.")
    request.state.sessao_id = ctx["sessao"]["id"]
    return ctx["usuario"]


def admin(u: dict = Depends(usuario_logado)) -> dict:
    if u["perfil"] != "admin":
        raise HTTPException(403, "Acesso restrito ao perfil Admin.")
    return u
