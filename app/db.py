"""Camada de dados do SGD — SOMENTE LEITURA.

Fonte preferencial: Postgres do hackathon (sessão com default_transaction_read_only=on).
Fallback: snapshot SQLite aberto em modo ro/immutable.
Apenas SELECTs explícitos. Nenhum DDL/DML é emitido por este módulo.
"""
from __future__ import annotations
import logging
import sqlite3
from . import config

log = logging.getLogger("vintmatch.db")

TABLES = {
    "dominios": "id, tipo_dominio, valor_dominio, descricao, status, deletado",
    "colaboradores": "id, nome_abreviado, data_admissao, id_cargo, id_senioridade, id_step, id_vinculo, id_modalidade, id_setor_empresa, id_contrato, status, deletado",
    "skills": "id, nome_skill, id_area_tecnologia, status, deletado",
    "colaborador_skills": "id, id_colaborador, id_skill, id_nivel_conhecimento, status, deletado",
    "contratos": "id, nome_contrato, data_inicio, data_termino, id_situacao, id_centro_custo, id_preposto, status, deletado",
    "demandas": "id, nome_demanda, id_gerente, id_contrato, id_tipo_servico, id_metodologia, id_andamento_demanda, id_grupo, dt_inicio_demanda, dt_termino_demanda_prevista, compartilha_profissionais, pertence_pmo, status, deletado",
    "demanda_skills": "id, id_demanda, id_skill, status, deletado",
    "alocacoes": "id, id_colaborador, id_demanda, status, deletado",
    "planejamentos": "id, id_alocacao, mes, ano, porcentagem, status, deletado",
    "talentos": "id, nome_abreviado, id_cargo, id_senioridade, id_modalidade, disponibilidade_informada_percentual, status, criado_em",
    "talento_skills": "id, id_talento, id_skill, id_nivel_conhecimento",
}
BOOL_COLS = {"status", "deletado", "compartilha_profissionais", "pertence_pmo"}


def _norm(rows, cols):
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        for c in BOOL_COLS & d.keys():
            d[c] = bool(d[c]) if d[c] is not None else None
        for c in ("data_admissao", "data_inicio", "data_termino", "dt_inicio_demanda",
                  "dt_termino_demanda_prevista", "criado_em"):
            if c in d and d[c] is not None:
                d[c] = str(d[c])[:10]
        out.append(d)
    return out


def _load_postgres() -> dict:
    import psycopg  # import tardio: só exige o driver se usar Postgres
    with psycopg.connect(config.DATABASE_URL, connect_timeout=3,
                         options="-c default_transaction_read_only=on") as con:
        con.read_only = True
        data = {}
        with con.cursor() as cur:
            for t, cols in TABLES.items():
                cur.execute(f'SELECT {cols} FROM "InHire".{t}')
                data[t] = _norm(cur.fetchall(), [c.strip() for c in cols.split(",")])
        return data


def _load_sqlite() -> dict:
    path = config.SQLITE_PATH.resolve().as_posix()
    con = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    try:
        data = {}
        for t, cols in TABLES.items():
            data[t] = _norm(con.execute(f"SELECT {cols} FROM {t}").fetchall(),
                            [c.strip() for c in cols.split(",")])
        return data
    finally:
        con.close()


def load_all() -> tuple[dict, str]:
    """Carrega as tabelas do SGD em memória (base pequena: ~20 mil linhas)."""
    src = config.DATA_SOURCE
    if src in ("auto", "postgres") and config.DATABASE_URL and "SEU_TOKEN" not in config.DATABASE_URL:
        try:
            data = _load_postgres()
            log.info("SGD carregado do Postgres (somente leitura)")
            return data, "postgres"
        except Exception as e:  # noqa: BLE001
            if src == "postgres":
                raise
            log.warning("Postgres indisponível (%s); usando snapshot SQLite", type(e).__name__)
    data = _load_sqlite()
    log.info("SGD carregado do snapshot SQLite (somente leitura)")
    return data, "sqlite"
