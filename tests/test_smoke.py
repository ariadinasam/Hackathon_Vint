"""Testes de fumaça (sem pytest): python -m tests.test_smoke"""
import io
import os
import re
from pathlib import Path

os.environ.setdefault("REFERENCE_MONTH", "2026-11")
os.environ["DATA_SOURCE"] = "sqlite"
from app import extract, llm, matching, rag, sgd  # noqa: E402

REQ = {"skills": [{"nome": "PHP", "nivel": "intermediario"}, {"nome": "Vue.js", "nivel": "intermediario"},
                  {"nome": "PostgreSQL", "nivel": "basico"}, {"nome": "Docker", "obrigatoria": False}],
       "duracao_meses": 3, "disponibilidade_min": 50, "texto": "sustentação de portal web em Kanban",
       "tipo_servico": "Sustentação", "metodologia": "Kanban"}


def test_somente_leitura():
    """O SGD só é lido: os módulos que tocam o SGD não podem ter DML/DDL, e o banco do app é outro arquivo."""
    from app import config
    code = "\n".join(Path("app", f).read_text(encoding="utf-8") for f in ("db.py", "sgd.py", "matching.py", "rag.py"))
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE)\s", code), "DML/DDL no acesso ao SGD!"
    assert "default_transaction_read_only=on" in Path("app/db.py").read_text(encoding="utf-8")
    assert config.APP_DB_PATH.resolve() != config.SQLITE_PATH.resolve()


def test_carga():
    s = sgd.get()
    assert s.source == "sqlite" and len(s.colabs) == 279 and len(s.skills) == 159
    assert s.resolve_skill("Postgre") == s.resolve_skill("PostgreSQL")


def test_matching():
    r = matching.run(sgd.get(), REQ)
    assert r["ranking"] and r["resumo"]["aptos"] > 0
    assert r["ranking"] == sorted(r["ranking"], key=lambda c: -c["score"])
    assert any(c["remanejamento"] for c in r["ranking"]), "esperava ao menos 1 caso de remanejamento"
    for c in r["ranking"]:
        assert c["disponivel"] == all(m["disp"] >= 50 for m in c["disp_meses"])
    assert r["tempo_ms"] < 5000


def test_extract_regras():
    txt = "Dev Laravel e Vue.js com PostgreSQL por 4 meses, 80%. Docker é desejável. Kanban, Pleno."
    out = extract.extract(sgd.get(), txt, use_ai=False)
    nomes = {x["nome"]: x for x in out["skills"]}
    assert {"Laravel (PHP)", "Vue.js", "PostgreSQL", "Docker"} <= set(nomes)
    assert nomes["Docker"]["obrigatoria"] is False and out["duracao_meses"] == 4 and out["disponibilidade_min"] == 80
    assert out["metodologia"] == "Kanban" and out["senioridades"] == ["Pleno"]


def test_docx():
    import docx
    d = docx.Document()
    d.add_paragraph("Projeto com Java e Spring Boot por 6 meses")
    buf = io.BytesIO()
    d.save(buf)
    assert "Spring Boot" in extract.read_document("b.docx", buf.getvalue())


def test_rag():
    r = rag.RAG(sgd.get())
    assert r.search("disponibilidade mensal planejamentos", 3)


def test_ia_merge_mock():
    """Simula a resposta do Claude para validar a fusão do score (sem chamar a API)."""
    s = sgd.get()
    r = matching.run(s, REQ)
    orig, enviado = llm.as_json, []

    def fake(sys, user, max_tokens=2500, prazo=None, **kw):
        enviado.append(user)
        return [{"ref": f"C{i}", "aderencia": 100 - 10 * i, "justificativa": f"teste {i}", "pdi": ""} for i in range(1, 9)]
    llm.as_json = fake
    try:
        info = llm.enrich_ranking(REQ, r)
    finally:
        llm.as_json = orig
    assert info["usada"] and r["ranking"][0]["componentes"]["semantico_fonte"] == "IA"
    nomes = [c["nome"] for c in r["ranking"]]
    assert not any(n in enviado[0] for n in nomes), "nome de colaborador enviado à IA!"


def test_gemini_mock():
    """Valida a chamada REST do Gemini e o modo JSON sem acessar a rede."""
    import json as _json
    from app import config
    old = (config.LLM_PROVIDER, config.GEMINI_API_KEY, llm.urllib.request.urlopen, config.GROQ_API_KEY)
    config.GROQ_API_KEY = ""
    seen = {}

    class Fake:
        def __init__(self, body): self.body = body
        def read(self): return self.body
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=0):
        seen["url"], seen["key"], seen["body"] = req.full_url, req.headers.get("X-goog-api-key"), _json.loads(req.data)
        out = {"candidates": [{"content": {"parts": [{"text": '[{"ref":"C1","aderencia":90}]'}]}}]}
        return Fake(_json.dumps(out).encode())
    try:
        config.LLM_PROVIDER, config.GEMINI_API_KEY = "gemini", "teste"
        llm.urllib.request.urlopen = fake_urlopen
        assert llm.provider() == "gemini"
        assert llm.as_json("sys", "user") == [{"ref": "C1", "aderencia": 90}]
        assert ":generateContent" in seen["url"] and seen["key"] == "teste"
        assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"
    finally:
        config.LLM_PROVIDER, config.GEMINI_API_KEY, llm.urllib.request.urlopen, config.GROQ_API_KEY = old


def test_gemini_diagnostico_mock():
    """404 no modelo → escolhe outro sozinho; 400 → marca a IA como bloqueada com o motivo."""
    import io
    import json as _json
    import urllib.error
    from app import config
    old = (config.LLM_PROVIDER, config.GEMINI_API_KEY, config.GEMINI_MODEL, llm.urllib.request.urlopen, dict(llm.STATUS), llm._modelo_gemini, config.GROQ_API_KEY)
    config.GROQ_API_KEY = ""
    llm._reservas_cache = None

    class Fake:
        def __init__(self, body): self.body = body
        def read(self): return self.body
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def http_err(code, status, msg):
        return urllib.error.HTTPError("u", code, status, {}, io.BytesIO(_json.dumps({"error": {"status": status, "message": msg}}).encode()))

    def fake_404(req, timeout=0):
        if "models/modelo-inexistente" in req.full_url:
            raise http_err(404, "NOT_FOUND", "models/modelo-inexistente is not found")
        lista = {"models": [{"name": "models/gemini-9.0-flash", "supportedGenerationMethods": ["generateContent"]},
                            {"name": "models/gemini-9.0-flash-preview", "supportedGenerationMethods": ["generateContent"]},
                            {"name": "models/text-embedding", "supportedGenerationMethods": ["embedContent"]}]}
        return Fake(_json.dumps(lista).encode())

    def fake_400(req, timeout=0):
        raise http_err(400, "INVALID_ARGUMENT", "API key not valid. Please pass a valid API key.")
    try:
        config.LLM_PROVIDER, config.GEMINI_API_KEY, config.GEMINI_MODEL = "gemini", "chave-teste", "modelo-inexistente"
        llm.urllib.request.urlopen = fake_404
        st = llm.verificar()
        assert st["ok"] and llm._modelo_de("gemini") == "gemini-9.0-flash", st
        llm._modelo_gemini = None
        llm.urllib.request.urlopen = fake_400
        st = llm.verificar()
        assert st["ok"] is False and st["bloqueante"] and "aistudio" in st["mensagem"] and not llm.available()
        assert "chave-teste" not in st["mensagem"]
    finally:
        (config.LLM_PROVIDER, config.GEMINI_API_KEY, config.GEMINI_MODEL, llm.urllib.request.urlopen, st0, llm._modelo_gemini, config.GROQ_API_KEY) = old
        llm._reservas_cache = None
        llm.STATUS.clear(); llm.STATUS.update(st0)



def test_reserva_503_para_groq():
    """Gemini 503 em todas as tentativas → a mesma chamada é respondida pelo Groq (provedor reserva)."""
    import io
    import json as _json
    import urllib.error
    from app import config
    old = (config.LLM_PROVIDER, config.GEMINI_API_KEY, config.GROQ_API_KEY, llm.urllib.request.urlopen, dict(llm.STATUS),
           llm._reservas_cache, llm.time.sleep)
    chamadas = []

    class Fake:
        def __init__(self, body): self.body = body
        def read(self): return self.body
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake(req, timeout=0):
        chamadas.append(req.full_url)
        if "googleapis" in req.full_url:
            raise urllib.error.HTTPError("u", 503, "x", {}, io.BytesIO(b'{"error":{"status":"UNAVAILABLE","message":"high demand"}}'))
        assert req.headers.get("Authorization") == "Bearer gsk_teste"
        return Fake(_json.dumps({"choices": [{"message": {"content": '{"candidatos":[{"ref":"C1","aderencia":77}]}'}}]}).encode())
    try:
        config.LLM_PROVIDER, config.GEMINI_API_KEY, config.GROQ_API_KEY = "auto", "AQ.teste", "gsk_teste"
        llm.urllib.request.urlopen, llm.time.sleep = fake, (lambda s: None)
        llm._reservas_cache = ["gemini-reserva-flash"]
        llm.STATUS["provedores"] = {}
        out = llm.as_json("sys", "user")
        assert out["candidatos"][0]["aderencia"] == 77 and llm.ULTIMO["provedor"] == "groq"
        assert sum("googleapis" in c for c in chamadas) == 3, chamadas  # principal + nova tentativa + 1 reserva
    finally:
        (config.LLM_PROVIDER, config.GEMINI_API_KEY, config.GROQ_API_KEY, llm.urllib.request.urlopen, st0,
         llm._reservas_cache, llm.time.sleep) = old
        llm.STATUS.clear(); llm.STATUS.update(st0)


if __name__ == "__main__":
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for f in fns:
        f()
        print("ok ", f.__name__)
    print(f"{len(fns)} testes passaram")
