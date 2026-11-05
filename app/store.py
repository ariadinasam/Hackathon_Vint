"""Banco do próprio app (SQLite): usuários, sessões, buscas e decisões.

NÃO é o SGD. O SGD continua somente leitura (db.py). Este arquivo guarda apenas o que o produto cria.
"""
from __future__ import annotations
import json
import sqlite3
import threading
from datetime import datetime, timezone
from . import config

_lock = threading.RLock()
SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  perfil TEXT NOT NULL DEFAULT 'usuario', area TEXT, status TEXT NOT NULL DEFAULT 'pendente',
  senha_hash TEXT, falhas INTEGER NOT NULL DEFAULT 0, bloqueado_ate TEXT,
  token_hash TEXT, token_tipo TEXT, token_expira TEXT, convidado_por INTEGER,
  criado_em TEXT NOT NULL, ultimo_acesso TEXT, senha_trocada_em TEXT);
CREATE TABLE IF NOT EXISTS sessoes (
  id INTEGER PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE, usuario_id INTEGER NOT NULL,
  user_agent TEXT, ip TEXT, lembrar INTEGER NOT NULL DEFAULT 0,
  criado_em TEXT NOT NULL, ultimo_uso TEXT NOT NULL, expira_em TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS buscas (
  id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL, nome TEXT NOT NULL, descricao TEXT,
  params_json TEXT NOT NULL, resultado_json TEXT, status TEXT NOT NULL,
  n_talentos INTEGER, n_remanejamento INTEGER, briefing_nome TEXT,
  criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decisoes (
  id INTEGER PRIMARY KEY, busca_id INTEGER NOT NULL, usuario_id INTEGER NOT NULL,
  origem TEXT NOT NULL, candidato_id INTEGER NOT NULL, percentual INTEGER, remanejamento INTEGER NOT NULL DEFAULT 0,
  criado_em TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_sessoes_usuario ON sessoes(usuario_id);
CREATE INDEX IF NOT EXISTS ix_buscas_criado ON buscas(criado_em);
CREATE INDEX IF NOT EXISTS ix_decisoes_busca ON decisoes(busca_id);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    config.APP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(config.APP_DB_PATH, timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init():
    with _lock, connect() as con:
        con.executescript(SCHEMA)
        cols = {r[1] for r in con.execute("PRAGMA table_info(buscas)")}
        if "briefing_hash" not in cols:  # migração simples do banco do app
            con.execute("ALTER TABLE buscas ADD COLUMN briefing_hash TEXT")
        if "nome_chave" not in cols:
            con.execute("ALTER TABLE buscas ADD COLUMN nome_chave TEXT")


def q(sql: str, args: tuple = (), one: bool = False):
    with _lock, connect() as con:
        cur = con.execute(sql, args)
        rows = [dict(r) for r in cur.fetchall()]
    return (rows[0] if rows else None) if one else rows


def x(sql: str, args: tuple = ()) -> int:
    """Executa escrita no banco DO APP e devolve lastrowid."""
    with _lock, connect() as con:
        cur = con.execute(sql, args)
        con.commit()
        return cur.lastrowid


def dumps(o) -> str:
    return json.dumps(o, ensure_ascii=False, separators=(",", ":"))
