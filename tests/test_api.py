"""Fluxo completo da API (login, busca, detalhe, decisão, convite, bloqueio). python -m tests.test_api"""
import os
import re
import tempfile

os.environ.setdefault("REFERENCE_MONTH", "2026-11")
os.environ["DATA_SOURCE"] = "sqlite"
os.environ.setdefault("APP_DB_PATH", os.path.join(tempfile.mkdtemp(), "app_teste.db"))
os.environ["LLM_PROVIDER"] = "none"

import shutil  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app import config  # noqa: E402
_corpus = os.path.join(tempfile.mkdtemp(), "corpus")
shutil.copytree(config.CORPUS_DIR, _corpus)
config.CORPUS_DIR = __import__("pathlib").Path(_corpus)  # uploads do teste não sujam a pasta do projeto
from app.main import app  # noqa: E402

FORTE = "Senha-Forte-2026!"
BUSCA = {"nome": "Portal de serviços", "descricao": "Sustentação do portal de serviços em Laravel e Vue.js com PostgreSQL, Kanban.",
         "skills": [{"nome": "PHP", "nivel": "intermediario"}, {"nome": "Vue.js", "nivel": "intermediario"},
                    {"nome": "PostgreSQL"}, {"nome": "Docker", "obrigatoria": False}],
         "duracao": "1–3 meses", "inicio": "Imediato", "disponibilidade_min": 50, "tipo_servico": "Sustentação"}


def run():
    with TestClient(app) as adm:
        assert adm.get("/api/auth/estado").json()["precisa_setup"] is True
        assert adm.get("/api/meta").status_code == 401, "rota de dados sem login"
        r = adm.post("/api/auth/setup", json={"nome": "Admin Teste", "email": "admin@vintglobal.com", "senha": "fraca"})
        assert r.status_code == 400
        r = adm.post("/api/auth/setup", json={"nome": "Admin Teste", "email": "admin@gmail.com", "senha": FORTE})
        assert r.status_code == 400, "domínio corporativo"
        assert adm.post("/api/auth/setup", json={"nome": "Admin Teste", "email": "admin@vintglobal.com", "senha": FORTE}).status_code == 200
        assert adm.get("/api/me").json()["perfil"] == "admin"
        assert adm.post("/api/auth/setup", json={"nome": "X", "email": "x@vintglobal.com", "senha": FORTE}).status_code == 409

        # busca: validação e execução
        r = adm.post("/api/buscas", json={"nome": "", "descricao": "curta", "skills": []})
        assert r.status_code == 400 and set(r.json()["detail"]["erros"]) == {"nome", "descricao", "skills"}
        bid = adm.post("/api/buscas", json=BUSCA).json()["id"]
        b = adm.get(f"/api/buscas/{bid}").json()
        res = b["resultado"]
        assert b["status"] == "aguardando" and res["ranking"] and len(res["externos"]) <= 8
        c0 = res["ranking"][0]
        d = adm.get(f"/api/buscas/{bid}/candidatos/interno/{c0['id']}").json()
        assert d["motivos"] and len(d["timeline"]["meses"]) == 6
        rem = next((c for c in res["ranking"] if c.get("remanejamento")), None)
        if rem:
            dr = adm.get(f"/api/buscas/{bid}/candidatos/interno/{rem['id']}").json()
            assert dr["rem"] and dr["rem"]["principal"]
        e0 = res["externos"][0]
        assert adm.get(f"/api/buscas/{bid}/candidatos/ihiring/{e0['id']}").json()["origem"] == "ihiring"
        assert adm.get(f"/api/buscas/{bid}/candidatos/interno/999999").status_code == 404
        # prévia ao vivo e campos livres (data de início, duração digitada, tipo/nível digitados)
        pv = adm.post("/api/buscas/previa", json={**BUSCA, "inicio": "2026-12-01", "duracao": "10 semanas"}).json()
        assert pv["inicio"] == "2026-12-01" and pv["meses"] == 3 and pv["aptos"] >= 1 and "externos" in pv
        assert adm.post("/api/buscas/previa", json={"duracao": "xyz"}).json()["duracao_entendida"] is False
        livre = {**BUSCA, "nome": "Busca com campos livres", "inicio": "15/12/2026", "duracao": "30/04/2027",
                 "tipo_servico": "sustentacao", "metodologia": "Kanban adaptado",
                 "skills": [{"nome": "PHP", "nivel": "Avançado"}, {"nome": "Vue.js", "nivel": "pleno"}]}
        bl = adm.get(f"/api/buscas/{adm.post('/api/buscas', json=livre).json()['id']}").json()
        assert bl["resultado"]["inicio_data"] == "2026-12-15" and bl["resultado"]["periodo"]["rotulo"].startswith("Dez/26")
        assert bl["resultado"]["requisitos"][0]["nivel"] == "Avançado" and bl["resultado"]["requisitos"][1]["nivel"] == "Intermediário"
        assert "erro" not in bl["resultado"]["ia"]
        assert adm.delete(f"/api/buscas/{bl['id']}").status_code == 200
        # duplicidade: mesmo nome (ignora caixa/acento/pontuação) e mesmo arquivo de briefing
        r = adm.post("/api/buscas", json={**BUSCA, "nome": "  portal de SERVIÇOS! "})
        assert r.status_code == 409 and "nome" in r.json()["detail"]["erros"]
        import io
        import docx
        d0 = docx.Document(); d0.add_paragraph("Projeto Laravel e Vue.js por 4 meses, 80%."); buf = io.BytesIO(); d0.save(buf)
        x1 = adm.post("/api/extract", files={"arquivo": ("brief.docx", buf.getvalue())}, data={"usar_ia": "false"}).json()
        b2 = adm.post("/api/buscas", json={**BUSCA, "nome": "Outro projeto", "briefing_nome": "brief.docx", "briefing_hash": x1["briefing_hash"]}).json()["id"]
        r = adm.post("/api/extract", files={"arquivo": ("copia.docx", buf.getvalue())}, data={"usar_ia": "false"})
        assert r.status_code == 409 and r.json()["detail"]["busca_id"] == b2
        r = adm.post("/api/buscas", json={**BUSCA, "nome": "Terceiro", "briefing_hash": x1["briefing_hash"]})
        assert r.status_code == 409 and "briefing" in r.json()["detail"]["erros"]
        # editar a própria busca não acusa duplicidade
        assert adm.post("/api/buscas", json={**BUSCA, "nome": "Outro projeto", "briefing_hash": x1["briefing_hash"], "busca_id": b2}).status_code == 200
        assert adm.get("/api/ia/status").json()["ok"] is False
        # rascunho
        rid = adm.post("/api/buscas", json={**BUSCA, "nome": "Rascunho X", "rascunho": True}).json()["id"]
        assert adm.get(f"/api/buscas/{rid}").json()["status"] == "rascunho"
        # decisão
        assert adm.post(f"/api/buscas/{bid}/decisao", json={"selecionados": [{"origem": "interno", "id": c0["id"]}, {"origem": "ihiring", "id": e0["id"]}]}).json()["registrados"] == 2
        # mais gente depois de confirmar, % por pessoa, editar o projeto e remover
        c1 = res["ranking"][1]
        assert adm.post(f"/api/buscas/{bid}/decisao", json={"selecionados": [{"origem": "interno", "id": c1["id"]}]}).json()["registrados"] == 1
        assert adm.post(f"/api/buscas/{bid}/decisao", json={"selecionados": [{"origem": "interno", "id": c1["id"]}]}).status_code == 400
        assert adm.patch(f"/api/buscas/{bid}/decisao/interno/{c1['id']}", json={"percentual": 80}).status_code == 200
        rel = adm.get(f"/api/buscas/{bid}/relatorio").json()
        assert rel["resumo"]["total"] == 3 and rel["resumo"]["internos"] == 2 and rel["resumo"]["externos"] == 1
        assert all(x["justificativa"] for x in rel["pessoas"]) and rel["pessoas"][0]["motivos"]
        assert 0 < rel["resumo"]["dedicacao_media"] <= 100
        assert len(rel["cobertura"]) == len(res["requisitos"]) and rel["projeto"]["nome"] == BUSCA["nome"]
        assert any(x["percentual"] == 80 for x in rel["pessoas"]) and rel["pessoas"][0]["alocado_por"] == "Admin Teste"
        r = adm.post("/api/buscas", json={**BUSCA, "skills": [{"nome": "Java"}], "busca_id": bid})
        assert r.status_code == 200 and r.json()["status"] == "confirmada"
        bb = adm.get(f"/api/buscas/{bid}").json()
        pool = {x["id"] for x in bb["resultado"]["ranking"] + bb["resultado"]["quase_la"] + bb["resultado"]["fixados"]}
        pool_e = {x["id"] for x in bb["resultado"]["externos"] + bb["resultado"]["externos_fixados"]}
        assert all((d["candidato_id"] in (pool if d["origem"] == "interno" else pool_e)) for d in bb["decisoes"])
        assert {d["percentual"] for d in bb["decisoes"] if d["candidato_id"] == c1["id"]} == {80}
        assert adm.delete(f"/api/buscas/{bid}/decisao/interno/{c1['id']}").json()["restantes"] == 2
        dash = adm.get("/api/dashboard").json()
        assert dash["ultimas_decisoes"] and dash["buscas_recentes"]
        assert adm.get(f"/api/buscas/{bid}").json()["status"] == "confirmada"

        # convite → primeiro acesso
        r = adm.post("/api/usuarios", json={"nome": "Fulana Teste", "email": "fulana@vintglobal.com", "perfil": "usuario"})
        token = re.search(r"token=([\w-]+)", r.json()["link"]).group(1)
        assert adm.post("/api/usuarios", json={"nome": "Dup", "email": "fulana@vintglobal.com"}).status_code == 409
        with TestClient(app) as usr:
            assert usr.get(f"/api/auth/convite/{token}").json()["email"] == "fulana@vintglobal.com"
            assert usr.post("/api/auth/login", json={"identificador": "fulana@vintglobal.com", "senha": "x"}).status_code == 403
            assert usr.post("/api/auth/definir-senha", json={"token": token, "senha": "abc"}).status_code == 400
            assert usr.post("/api/auth/definir-senha", json={"token": token, "senha": FORTE}).status_code == 200
            assert usr.post("/api/auth/definir-senha", json={"token": token, "senha": FORTE}).status_code == 404, "token de uso único"
            assert usr.get("/api/me").json()["perfil"] == "usuario"
            assert usr.get("/api/usuarios").status_code == 403, "Usuário não acessa admin"
            assert usr.get("/api/buscas").status_code == 200
            usr.post("/api/auth/logout")
            assert usr.get("/api/me").status_code == 401
            # bloqueio após 5 tentativas
            for i in range(4):
                r = usr.post("/api/auth/login", json={"identificador": "fulana", "senha": "errada"})
                assert r.status_code == 401 and r.json()["detail"]["restantes"] == 4 - i
            assert usr.post("/api/auth/login", json={"identificador": "fulana", "senha": "errada"}).status_code == 423
            assert usr.post("/api/auth/login", json={"identificador": "fulana", "senha": FORTE}).status_code == 423
            uid = next(u["id"] for u in adm.get("/api/usuarios").json() if u["email"] == "fulana@vintglobal.com")
            assert adm.post(f"/api/usuarios/{uid}/acao/desbloquear").status_code == 200
            assert usr.post("/api/auth/login", json={"identificador": "fulana", "senha": FORTE, "lembrar": False}).status_code == 200
            # perfil
            assert usr.post("/api/me/senha", json={"atual": "errada", "nova": FORTE + "x"}).status_code == 400
            assert usr.post("/api/me/senha", json={"atual": FORTE, "nova": FORTE + "x"}).status_code == 200
            assert len(usr.get("/api/me/sessoes").json()) == 1
            # admin bloqueia → sessão cai
            assert adm.post(f"/api/usuarios/{uid}/acao/bloquear").status_code == 200
            assert usr.get("/api/me").status_code == 401
        # excluir projeto (com alocações) — só autor/Admin
        xid = adm.post("/api/buscas", json={**BUSCA, "nome": "Projeto descartável"}).json()["id"]
        rx = adm.get(f"/api/buscas/{xid}").json()["resultado"]
        adm.post(f"/api/buscas/{xid}/decisao", json={"selecionados": [{"origem": "interno", "id": rx["ranking"][0]["id"]}]})
        assert adm.delete(f"/api/buscas/{xid}").status_code == 200
        assert adm.get(f"/api/buscas/{xid}").status_code == 404
        assert adm.delete(f"/api/buscas/{xid}").status_code == 404
        assert adm.post("/api/buscas", json={**BUSCA, "nome": "Projeto descartável"}).status_code == 200  # nome liberado
        # base de conhecimento: banco ao vivo + projetos + documento enviado
        f = adm.get("/api/base/fontes").json()
        assert f["sgd"]["colaboradores"] > 200 and f["projetos"] >= 1
        a = adm.post("/api/rag", json={"pergunta": "Quem tem PostgreSQL avançado e está livre em dezembro?"}).json()
        assert a["fontes"][0]["fonte"] == "SGD · consulta ao vivo" and "Mocado" in a["fontes"][0]["texto"]  # nomes reais na tela
        a = adm.post("/api/rag", json={"pergunta": "Quais projetos estão aguardando decisão?"}).json()
        assert any(x["fonte"] == "VINT Match · projeto" for x in a["fontes"])
        r = adm.post("/api/base/documentos", files={"arquivo": ("politica_alocacao.txt", "Política: ninguém pode passar de 100% de alocação; prioridade para contratos vencendo.".encode())})
        assert r.status_code == 200
        a = adm.post("/api/rag", json={"pergunta": "Qual a política de alocação acima de 100%?"}).json()
        assert any(x["fonte"] == "politica_alocacao.txt" for x in a["fontes"])
        assert adm.delete("/api/base/documentos/politica_alocacao.txt").status_code == 200
        assert adm.get("/favicon.ico").status_code == 200
        # redefinição
        r = adm.post(f"/api/usuarios/{uid}/acao/redefinir").json()
        assert "token=" in r["link"]
        assert adm.get("/api/buscas").json()
    print("test_api: fluxo completo OK")


def test_fluxo_completo():
    """Fluxo ponta a ponta pela API (pytest)."""
    run()


if __name__ == "__main__":
    run()
