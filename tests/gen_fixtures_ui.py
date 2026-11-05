"""Gera respostas da API PSEUDONIMIZADAS (sem nomes reais do SGD) para testes visuais do front. python -m tests.gen_fixtures_ui"""
import json
import os
import re
import tempfile
from pathlib import Path

os.environ.setdefault("REFERENCE_MONTH", "2026-11")
os.environ["DATA_SOURCE"] = "sqlite"
os.environ["APP_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "fx.db")
os.environ["LLM_PROVIDER"] = "none"
from fastapi.testclient import TestClient  # noqa: E402
from app import sgd  # noqa: E402
from app.main import app  # noqa: E402

OUT = Path("tests/fixtures/ui")
S = "Senha-Forte-2026!"


def pseudo(txt: str) -> str:
    s = sgd.get()
    for cid, c in sorted(s.colabs.items(), key=lambda kv: -len(kv[1]["nome"])):
        txt = txt.replace(c["nome"], f"Colaborador {cid:03d}")
    for tid, t in sorted(s.talentos.items(), key=lambda kv: -len(kv[1]["nome"])):
        txt = re.sub(r'(?<=")' + re.escape(t["nome"]) + r'(?=")', f"Talento {tid:03d}", txt)
    assert "Mocado" not in txt
    return txt


with TestClient(app) as c:
    c.post("/api/auth/setup", json={"nome": "Larissa Demo", "email": "larissa.demo@vintglobal.com", "senha": S, "area": "PMO de Tecnologia"})
    for n, e, p in [("Thiago Demo", "thiago.demo@vintglobal.com", "admin"), ("Fernanda Demo", "fernanda.demo@vintglobal.com", "usuario")]:
        c.post("/api/usuarios", json={"nome": n, "email": e, "perfil": p})
    b1 = c.post("/api/buscas", json={"nome": "Plataforma de pagamentos", "descricao": "Evolução da plataforma de pagamentos com Java e Spring Boot, PostgreSQL e Docker em Scrum.",
                                     "skills": [{"nome": "Java"}, {"nome": "Spring Boot (Java)"}, {"nome": "PostgreSQL"}], "duracao": "3–6 meses", "inicio": "Em 30 dias"}).json()["id"]
    r1 = c.get(f"/api/buscas/{b1}").json()["resultado"]
    c.post(f"/api/buscas/{b1}/decisao", json={"selecionados": [{"origem": "interno", "id": r1["ranking"][0]["id"]},
                                                                {"origem": "interno", "id": r1["ranking"][1]["id"]},
                                                                {"origem": "ihiring", "id": r1["externos"][0]["id"]}]})
    c.post("/api/buscas", json={"nome": "Observabilidade da malha", "descricao": "", "skills": [{"nome": "Kubernetes"}], "rascunho": True})
    bid = c.post("/api/buscas", json={"nome": "Portal de serviços SEFAZ", "descricao": "Sustentação do portal de serviços em Laravel e Vue.js com PostgreSQL, Kanban, autenticação Keycloak.",
                                      "skills": [{"nome": "PHP", "nivel": "intermediario"}, {"nome": "Vue.js", "nivel": "intermediario"}, {"nome": "PostgreSQL"}, {"nome": "Keycloak", "obrigatoria": False}],
                                      "duracao": "1–3 meses", "inicio": "Imediato", "disponibilidade_min": 50, "tipo_servico": "Sustentação", "metodologia": "Kanban"}).json()["id"]
    res = c.get(f"/api/buscas/{bid}").json()["resultado"]
    rem = next(x for x in res["ranking"] if x.get("remanejamento"))
    pdi = next((x for x in res["ranking"] if x.get("pdi")), res["ranking"][0])
    rotas = {
        "estado": "/api/auth/estado", "me": "/api/me", "meta": "/api/meta", "dashboard": "/api/dashboard", "buscas": "/api/buscas",
        "busca": f"/api/buscas/{bid}", "busca_conf": f"/api/buscas/{b1}", "relatorio": f"/api/buscas/{b1}/relatorio",
        "det_conf": f"/api/buscas/{b1}/candidatos/interno/{r1['ranking'][0]['id']}", "det_rem": f"/api/buscas/{bid}/candidatos/interno/{rem['id']}",
        "det_pdi": f"/api/buscas/{bid}/candidatos/interno/{pdi['id']}",
        "det_ext": f"/api/buscas/{bid}/candidatos/ihiring/{res['externos'][0]['id']}", "usuarios": "/api/usuarios", "sessoes": "/api/me/sessoes", "base_fontes": "/api/base/fontes",
    }
    idx = {}
    for k, path in rotas.items():
        body = c.get(path).json()
        (OUT / f"{k}.json").write_text(pseudo(json.dumps(body, ensure_ascii=False)), encoding="utf-8")
        idx[path] = f"{k}.json"
    rr = c.post("/api/rag", json={"pergunta": "Quem tem PostgreSQL avançado e está livre em dezembro?"}).json()
    (OUT / "rag.json").write_text(pseudo(json.dumps(rr, ensure_ascii=False)), encoding="utf-8")
    (OUT / "_rotas.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(idx, indent=1))
