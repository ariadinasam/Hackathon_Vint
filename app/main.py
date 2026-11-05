"""VINT Match — API + front (SPA no design Vint_Global).  Rodar:  uvicorn app.main:app --reload"""
from __future__ import annotations
import hashlib
import json
import time
import uuid
import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import auth, buscas, config, extract, llm, matching, rag, sgd, store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("vintmatch")
STATIC = Path(__file__).parent / "static"

app = FastAPI(title="VINT Match", version="0.2.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
_rag: rag.RAG | None = None


def get_rag() -> rag.RAG:
    global _rag
    if _rag is None:
        _rag = rag.RAG(sgd.get())
    return _rag


@app.on_event("startup")
def _startup():
    store.init()
    threading.Thread(target=llm.verificar, daemon=True).start()  # testa a chave/modelo da IA sem atrasar a subida
    s = sgd.get()
    get_rag()
    n = store.q("SELECT count(*) AS n FROM usuarios", one=True)["n"]
    log.info("pronto: fonte=%s, colaboradores=%d, IA=%s, usuarios=%d%s", s.source, len(s.colabs),
             llm.provider() or "desligada", n, " (primeiro acesso: crie o admin na tela de login)" if not n else "")


# ======================================================================= páginas
@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(STATIC / "img" / "favicon.ico")


@app.get("/legado")
def legado():
    return FileResponse(STATIC / "legado.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/ia/status")
def ia_status(refazer: bool = False):
    """Diagnóstico da IA (sem segredos): provedor, modelo em uso e o motivo de falha, se houver."""
    if refazer:
        llm.verificar()
    return {"provedor": llm.provider(), "modelo": llm.model_name(), **llm.STATUS}


# ======================================================================= autenticação
class LoginReq(BaseModel):
    identificador: str
    senha: str
    lembrar: bool = True


class SetupReq(BaseModel):
    nome: str
    email: str
    senha: str
    area: str = ""


class DefinirSenhaReq(BaseModel):
    token: str
    senha: str


@app.get("/api/auth/estado")
def auth_estado(request: Request):
    n = store.q("SELECT count(*) AS n FROM usuarios", one=True)["n"]
    ctx = auth.sessao_atual(request)
    return {"precisa_setup": n == 0, "logado": bool(ctx), "dominio": config.ALLOWED_EMAIL_DOMAIN}


@app.post("/api/auth/setup")
def auth_setup(body: SetupReq, request: Request, response: Response):
    if store.q("SELECT count(*) AS n FROM usuarios", one=True)["n"]:
        raise HTTPException(409, "O administrador inicial já foi criado.")
    if not body.nome.strip():
        raise HTTPException(400, "Informe seu nome.")
    if not auth.email_ok(body.email):
        raise HTTPException(400, f"Use o e-mail corporativo, terminado em @{config.ALLOWED_EMAIL_DOMAIN}."
                            if config.ALLOWED_EMAIL_DOMAIN else "E-mail inválido.")
    falta = auth.senha_fraca(body.senha)
    if falta:
        raise HTTPException(400, "Senha fraca: " + ", ".join(falta))
    agora = store.now()
    uid = store.x("INSERT INTO usuarios(nome,email,perfil,area,status,senha_hash,criado_em,senha_trocada_em) "
                  "VALUES (?,?,?,?,?,?,?,?)", (body.nome.strip(), body.email.strip().lower(), "admin",
                                               body.area.strip() or None, "ativo", auth.hash_senha(body.senha), agora, agora))
    t, age = auth.criar_sessao(uid, request, True)
    auth.set_cookie(response, t, age)
    return {"ok": True}


@app.post("/api/auth/login")
def auth_login(body: LoginReq, request: Request, response: Response):
    ident = body.identificador.strip().lower()
    if not ident or not body.senha:
        raise HTTPException(400, "Informe e-mail/usuário e senha.")
    if "@" in ident and config.ALLOWED_EMAIL_DOMAIN and not ident.endswith("@" + config.ALLOWED_EMAIL_DOMAIN):
        raise HTTPException(400, f"Use o e-mail corporativo, terminado em @{config.ALLOWED_EMAIL_DOMAIN}.")
    u = store.q("SELECT * FROM usuarios WHERE lower(email)=? OR lower(substr(email,1,instr(email,'@')-1))=?",
                (ident, ident), one=True)
    erro = {"codigo": "credenciais", "mensagem": "E-mail/usuário ou senha incorretos."}
    if not u:
        raise HTTPException(401, erro)
    st = auth.status_efetivo(u)
    if st == "bloqueado":
        raise HTTPException(423, {"codigo": "bloqueado", "mensagem": "Conta bloqueada após 5 tentativas. "
                                  f"Tente de novo em {config.BLOQUEIO_MINUTOS} minutos ou peça desbloqueio a um Admin."})
    if st == "pendente":
        raise HTTPException(403, {"codigo": "pendente", "mensagem": "Convite ainda não aceito. Use o link de convite para definir sua senha."})
    if not auth.confere_senha(body.senha, u["senha_hash"]):
        falhas = (u["falhas"] or 0) + 1
        if falhas >= config.MAX_TENTATIVAS:
            ate = (datetime.now(timezone.utc) + timedelta(minutes=config.BLOQUEIO_MINUTOS)).isoformat(timespec="seconds")
            store.x("UPDATE usuarios SET falhas=?, status='bloqueado', bloqueado_ate=? WHERE id=?", (falhas, ate, u["id"]))
            log.warning("usuário id=%s bloqueado por tentativas", u["id"])
            raise HTTPException(423, {"codigo": "bloqueado", "mensagem": "Conta bloqueada após 5 tentativas. "
                                      f"Tente de novo em {config.BLOQUEIO_MINUTOS} minutos ou peça desbloqueio a um Admin."})
        store.x("UPDATE usuarios SET falhas=? WHERE id=?", (falhas, u["id"]))
        raise HTTPException(401, {**erro, "restantes": config.MAX_TENTATIVAS - falhas})
    if u["status"] == "bloqueado":  # bloqueio expirou
        store.x("UPDATE usuarios SET status='ativo', bloqueado_ate=NULL, falhas=0 WHERE id=?", (u["id"],))
    t, age = auth.criar_sessao(u["id"], request, body.lembrar)
    auth.set_cookie(response, t, age)
    return {"ok": True}


@app.post("/api/auth/logout")
def auth_logout(request: Request, response: Response):
    t = request.cookies.get(auth.COOKIE)
    if t:
        store.x("DELETE FROM sessoes WHERE token_hash=?", (auth.token_hash(t),))
    response.delete_cookie(auth.COOKIE, path="/")
    return {"ok": True}


@app.get("/api/auth/convite/{token}")
def convite_info(token: str):
    u = store.q("SELECT u.*, c.nome AS por FROM usuarios u LEFT JOIN usuarios c ON c.id=u.convidado_por "
                "WHERE u.token_hash=?", (auth.token_hash(token),), one=True)
    if not u or auth.utc(u["token_expira"]) < datetime.now(timezone.utc):
        raise HTTPException(404, "Link inválido ou expirado. Peça um novo convite ao administrador.")
    return {"email": u["email"], "nome": u["nome"], "tipo": u["token_tipo"], "convidado_por": u["por"],
            "expira_em": u["token_expira"]}


@app.post("/api/auth/definir-senha")
def definir_senha(body: DefinirSenhaReq, request: Request, response: Response):
    u = store.q("SELECT * FROM usuarios WHERE token_hash=?", (auth.token_hash(body.token),), one=True)
    if not u or auth.utc(u["token_expira"]) < datetime.now(timezone.utc):
        raise HTTPException(404, "Link inválido ou expirado. Peça um novo convite ao administrador.")
    falta = auth.senha_fraca(body.senha)
    if falta:
        raise HTTPException(400, "Senha fraca: " + ", ".join(falta))
    store.x("UPDATE usuarios SET senha_hash=?, status='ativo', falhas=0, bloqueado_ate=NULL, token_hash=NULL, "
            "token_tipo=NULL, token_expira=NULL, senha_trocada_em=? WHERE id=?",
            (auth.hash_senha(body.senha), store.now(), u["id"]))
    store.x("DELETE FROM sessoes WHERE usuario_id=?", (u["id"],))
    t, age = auth.criar_sessao(u["id"], request, False)
    auth.set_cookie(response, t, age)
    return {"ok": True}


# ======================================================================= meu perfil
class TrocaSenhaReq(BaseModel):
    atual: str
    nova: str


@app.get("/api/me")
def me(u: dict = Depends(auth.usuario_logado)):
    return auth.usuario_publico(u)


@app.post("/api/me/senha")
def trocar_senha(body: TrocaSenhaReq, request: Request, u: dict = Depends(auth.usuario_logado)):
    if not auth.confere_senha(body.atual, u["senha_hash"]):
        raise HTTPException(400, "Senha atual incorreta.")
    falta = auth.senha_fraca(body.nova)
    if falta:
        raise HTTPException(400, "Senha fraca: " + ", ".join(falta))
    store.x("UPDATE usuarios SET senha_hash=?, senha_trocada_em=? WHERE id=?",
            (auth.hash_senha(body.nova), store.now(), u["id"]))
    store.x("DELETE FROM sessoes WHERE usuario_id=? AND id<>?", (u["id"], request.state.sessao_id))
    return {"ok": True}


@app.get("/api/me/sessoes")
def sessoes(request: Request, u: dict = Depends(auth.usuario_logado)):
    rows = store.q("SELECT id, user_agent, ip, criado_em, ultimo_uso FROM sessoes WHERE usuario_id=? AND expira_em>? "
                   "ORDER BY ultimo_uso DESC", (u["id"], store.now()))
    for r in rows:
        r["atual"] = r["id"] == request.state.sessao_id
    return rows


@app.delete("/api/me/sessoes/{sid}")
def encerrar_sessao(sid: int, u: dict = Depends(auth.usuario_logado)):
    store.x("DELETE FROM sessoes WHERE id=? AND usuario_id=?", (sid, u["id"]))
    return {"ok": True}


@app.post("/api/me/sessoes/encerrar-outras")
def encerrar_outras(request: Request, u: dict = Depends(auth.usuario_logado)):
    store.x("DELETE FROM sessoes WHERE usuario_id=? AND id<>?", (u["id"], request.state.sessao_id))
    return {"ok": True}


# ======================================================================= admin: usuários
class ConviteReq(BaseModel):
    nome: str
    email: str
    perfil: str = "usuario"
    area: str = ""


def _link(request: Request, token: str) -> str:
    return f"{str(request.base_url).rstrip('/')}/#/primeiro-acesso?token={token}"


@app.get("/api/usuarios")
def usuarios(u: dict = Depends(auth.admin)):
    rows = store.q("SELECT * FROM usuarios ORDER BY perfil, nome")
    return [{**auth.usuario_publico(r), "voce": r["id"] == u["id"]} for r in rows]


@app.post("/api/usuarios")
def convidar(body: ConviteReq, request: Request, u: dict = Depends(auth.admin)):
    email = body.email.strip().lower()
    if not body.nome.strip():
        raise HTTPException(400, {"campo": "nome", "mensagem": "Informe o nome completo."})
    if not auth.email_ok(email):
        raise HTTPException(400, {"campo": "email", "mensagem": f"Use o e-mail corporativo, terminado em @{config.ALLOWED_EMAIL_DOMAIN}."
                                  if config.ALLOWED_EMAIL_DOMAIN else "E-mail inválido."})
    if store.q("SELECT 1 FROM usuarios WHERE lower(email)=?", (email,), one=True):
        raise HTTPException(409, {"campo": "email", "mensagem": "Já existe um usuário com este e-mail."})
    t, th = auth.novo_token()
    exp = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(timespec="seconds")
    store.x("INSERT INTO usuarios(nome,email,perfil,area,status,token_hash,token_tipo,token_expira,convidado_por,criado_em) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)", (body.nome.strip(), email, "admin" if body.perfil == "admin" else "usuario",
                                             body.area.strip() or None, "pendente", th, "convite", exp, u["id"], store.now()))
    return {"ok": True, "link": _link(request, t), "expira_em": exp}


@app.post("/api/usuarios/{uid}/acao/{acao}")
def acao_usuario(uid: int, acao: str, request: Request, u: dict = Depends(auth.admin)):
    alvo = store.q("SELECT * FROM usuarios WHERE id=?", (uid,), one=True)
    if not alvo:
        raise HTTPException(404, "Usuário não encontrado.")
    if alvo["id"] == u["id"] and acao in ("bloquear",):
        raise HTTPException(400, "Você não pode bloquear a própria conta.")
    if acao in ("redefinir", "reenviar"):
        t, th = auth.novo_token()
        exp = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(timespec="seconds")
        tipo = "convite" if alvo["status"] == "pendente" else "reset"
        store.x("UPDATE usuarios SET token_hash=?, token_tipo=?, token_expira=?, convidado_por=? WHERE id=?",
                (th, tipo, exp, u["id"], uid))
        return {"ok": True, "link": _link(request, t), "expira_em": exp}
    if acao == "desbloquear":
        store.x("UPDATE usuarios SET status='ativo', falhas=0, bloqueado_ate=NULL WHERE id=?", (uid,))
        return {"ok": True}
    if acao == "bloquear":
        store.x("UPDATE usuarios SET status='bloqueado', bloqueado_ate=NULL WHERE id=?", (uid,))
        store.x("DELETE FROM sessoes WHERE usuario_id=?", (uid,))
        return {"ok": True}
    if acao in ("tornar_admin", "tornar_usuario"):
        if alvo["id"] == u["id"]:
            raise HTTPException(400, "Peça a outro Admin para mudar o seu perfil.")
        store.x("UPDATE usuarios SET perfil=? WHERE id=?", ("admin" if acao == "tornar_admin" else "usuario", uid))
        return {"ok": True}
    raise HTTPException(400, "Ação desconhecida.")


# ======================================================================= dados / matching
class SkillReq(BaseModel):
    nome: str
    obrigatoria: bool = True
    nivel: str = "basico"


class BuscaReq(BaseModel):
    nome: str
    descricao: str = ""
    skills: list[SkillReq] = Field(default_factory=list)
    duracao: str = "3–6 meses"
    inicio: str = "Em 15 dias"
    disponibilidade_min: int = 50
    senioridades: list[str] = Field(default_factory=list)
    tipo_servico: str | None = None
    metodologia: str | None = None
    briefing_nome: str | None = None
    briefing_texto: str | None = None
    briefing_hash: str | None = None
    rascunho: bool = False
    usar_ia: bool = True
    busca_id: int | None = None  # reexecutar/editar uma busca existente


class DecisaoReq(BaseModel):
    selecionados: list[dict]


class MatchReq(BaseModel):  # rota legada (/legado e testes)
    skills: list[SkillReq] = Field(default_factory=list)
    inicio: str | None = None
    duracao_meses: int = 3
    disponibilidade_min: int = 50
    senioridades: list[str] = Field(default_factory=list)
    tipo_servico: str | None = None
    metodologia: str | None = None
    texto: str = ""
    incluir_externos: bool = True
    usar_ia: bool = True


class Pergunta(BaseModel):
    pergunta: str


@app.get("/api/meta")
def meta(u: dict = Depends(auth.usuario_logado)):
    s = sgd.get()
    return {"catalogo": s.catalog, **s.options, "fonte_dados": s.source,
            "referencia": f"{s.ref_idx // 12}-{s.ref_idx % 12 + 1:02d}", "horizonte": sgd.idx_label(s.plan_horizon),
            "ia_ativa": llm.available(), "modelo": llm.model_name(), "provedor": llm.provider(), "ia_status": llm.STATUS,
            "colaboradores_ativos": sum(c["ativo"] for c in s.colabs.values()),
            "duracoes": list(buscas.DURACAO), "inicios": list(buscas.INICIO)}


@app.get("/api/dashboard")
def dashboard(u: dict = Depends(auth.usuario_logado)):
    return buscas.dashboard(sgd.get(), u)


@app.get("/api/buscas")
def listar_buscas(u: dict = Depends(auth.usuario_logado)):
    return buscas.listar(200)


_ia_lock = threading.Lock()


def _refinar_com_ia(bid: int, req: dict, res: dict):
    """Roda depois de a busca já ter sido salva: a tela mostra o ranking por regras e se atualiza sozinha."""
    try:
        info = llm.enrich_ranking(req, res)
    except Exception as e:  # noqa: BLE001
        log.warning("refino por IA falhou na busca %s: %s", bid, llm._limpa(str(e))[:200])
        info = {"usada": False}
    info.pop("erro", None)  # detalhe técnico fica só no log do servidor
    res["ia"] = info
    with _ia_lock:
        row = store.q("SELECT resultado_json FROM buscas WHERE id=?", (bid,), one=True)
        if not row or not row["resultado_json"]:
            return
        if json.loads(row["resultado_json"]).get("versao") != res.get("versao"):
            return  # a busca foi editada de novo enquanto a IA respondia
        store.x("UPDATE buscas SET resultado_json=? WHERE id=?", (store.dumps(res), bid))
    log.info("busca %s: refino por IA %s", bid, "aplicado" if info.get("usada") else "não aplicado (regras mantidas)")


class PreviaReq(BaseModel):
    skills: list[SkillReq] = Field(default_factory=list)
    duracao: str = ""
    inicio: str = ""
    disponibilidade_min: int = 50
    senioridades: list[str] = Field(default_factory=list)
    tipo_servico: str | None = None
    metodologia: str | None = None


@app.post("/api/buscas/previa")
def previa_busca(body: PreviaReq, u: dict = Depends(auth.usuario_logado)):
    p = body.model_dump()
    p["skills"] = [x.model_dump() for x in body.skills]
    return buscas.previa(sgd.get(), p)


@app.post("/api/buscas")
def criar_busca(body: BuscaReq, u: dict = Depends(auth.usuario_logado)):
    p = body.model_dump()
    p["skills"] = [x.model_dump() for x in body.skills]
    erros = {}
    if not body.nome.strip():
        erros["nome"] = "Dê um nome ao projeto para encontrá-lo depois no histórico."
    if not body.rascunho:
        falta = 40 - len(body.descricao.strip())
        if falta > 0:
            erros["descricao"] = f"Descreva a demanda com pelo menos 40 caracteres — faltam {falta}."
        if not body.skills:
            erros["skills"] = "Adicione ao menos uma skill: digite o nome e pressione Enter."
    if erros:
        raise HTTPException(400, {"erros": erros})
    dup = buscas.duplicada(body.nome, body.briefing_hash, body.busca_id)
    if dup:
        quando = dup["criado_em"][:10]
        if dup["campo"] == "nome":
            msg = f"Já existe uma busca chamada “{dup['nome']}” (criada em {quando} por {dup.get('autor') or '—'}). Use outro nome ou abra a existente."
        else:
            msg = f"Este briefing já foi usado na busca “{dup['nome']}” (criada em {quando}). Abra a busca existente em vez de criar outra."
        raise HTTPException(409, {"erros": {"nome" if dup["campo"] == "nome" else "briefing": msg}, "busca_id": dup["id"]})
    usar_ia = body.usar_ia
    p.pop("usar_ia", None)
    bid = p.pop("busca_id", None)
    rasc = p.pop("rascunho", False)
    existe = bid and store.q("SELECT 1 FROM buscas WHERE id=?", (bid,), one=True)
    fixar = buscas.fixados_da_busca(bid) if existe else None  # quem já está alocado continua no resultado
    req = res = None
    if not rasc:
        req, res = buscas.preparar(sgd.get(), p, get_rag(), fixar)  # ranking por regras: imediato
        res["versao"] = uuid.uuid4().hex
        if usar_ia and llm.available() and res["ranking"]:
            res["ia"] = {"usada": False, "pendente": True, "desde": time.time()}
    if existe:
        buscas.atualizar(bid, p, res)
    else:
        bid = buscas.salvar(u["id"], p, res)
    if res and res["ia"].get("pendente"):
        threading.Thread(target=_refinar_com_ia, args=(bid, req, res), daemon=True).start()
    log.info("busca %s: %d skills, rascunho=%s, ia=%s", bid, len(body.skills), rasc, bool(res and res["ia"].get("pendente")))
    return {"id": bid, "status": store.q("SELECT status FROM buscas WHERE id=?", (bid,), one=True)["status"],
            "resumo": res["resumo"] if res else None, "n_externos": len(res["externos"]) if res else 0}


@app.get("/api/buscas/{bid}")
def obter_busca(bid: int, u: dict = Depends(auth.usuario_logado)):
    b = buscas.carregar(bid)
    if not b:
        raise HTTPException(404, "Busca não encontrada.")
    ia = (b.get("resultado") or {}).get("ia") or {}
    if ia.get("pendente") and time.time() - ia.get("desde", 0) > 120:
        b["resultado"]["ia"] = {"usada": False}  # servidor reiniciou no meio do refino: fica o ranking por regras
    return b


@app.get("/api/buscas/{bid}/relatorio")
def relatorio_busca(bid: int, u: dict = Depends(auth.usuario_logado)):
    b = buscas.carregar(bid)
    if not b:
        raise HTTPException(404, "Busca não encontrada.")
    if not b.get("resultado"):
        raise HTTPException(400, "Este projeto ainda é um rascunho: gere o matchmaking antes do relatório.")
    return buscas.relatorio(sgd.get(), b)


@app.post("/api/buscas/{bid}/decisao")
def decidir(bid: int, body: DecisaoReq, u: dict = Depends(auth.usuario_logado)):
    b = buscas.carregar(bid)
    if not b or not b["resultado"]:
        raise HTTPException(404, "Busca não encontrada.")
    n = buscas.decidir(sgd.get(), b, u["id"], body.selecionados)
    if not n:
        raise HTTPException(400, "Nenhum talento válido selecionado.")
    return {"ok": True, "registrados": n}


@app.delete("/api/buscas/{bid}")
def excluir_busca(bid: int, u: dict = Depends(auth.usuario_logado)):
    b = store.q("SELECT id, nome, usuario_id FROM buscas WHERE id=?", (bid,), one=True)
    if not b:
        raise HTTPException(404, "Projeto não encontrado.")
    if b["usuario_id"] != u["id"] and u["perfil"] != "admin":
        raise HTTPException(403, "Só quem criou o projeto ou um Admin pode excluí-lo.")
    buscas.excluir(bid)
    log.info("busca %s excluída pelo usuário id=%s", bid, u["id"])
    return {"ok": True}


class PercentualReq(BaseModel):
    percentual: int


@app.delete("/api/buscas/{bid}/decisao/{origem}/{cid}")
def remover_da_alocacao(bid: int, origem: str, cid: int, u: dict = Depends(auth.usuario_logado)):
    if not buscas.carregar(bid):
        raise HTTPException(404, "Busca não encontrada.")
    return {"ok": True, "restantes": buscas.remover_decisao(bid, origem, cid)}


@app.patch("/api/buscas/{bid}/decisao/{origem}/{cid}")
def mudar_percentual(bid: int, origem: str, cid: int, body: PercentualReq, u: dict = Depends(auth.usuario_logado)):
    buscas.mudar_percentual(bid, origem, cid, body.percentual)
    return {"ok": True}


@app.get("/api/buscas/{bid}/candidatos/{origem}/{cid}")
def detalhe(bid: int, origem: str, cid: int, u: dict = Depends(auth.usuario_logado)):
    b = buscas.carregar(bid)
    if not b or not b["resultado"]:
        raise HTTPException(404, "Busca não encontrada.")
    s = sgd.get()
    d = buscas.detalhe_interno(s, b, cid) if origem == "interno" else buscas.detalhe_externo(s, b, cid)
    if not d:
        raise HTTPException(404, "Candidato não está no resultado desta busca.")
    return d


@app.post("/api/match")
def match(req: MatchReq, u: dict = Depends(auth.usuario_logado)):
    s = sgd.get()
    payload = req.model_dump()
    payload["skills"] = [x.model_dump() for x in req.skills]
    try:
        result = matching.run(s, payload)
    except ValueError as e:
        raise HTTPException(400, f"Parâmetro inválido: {e}") from e
    result["ia"] = llm.enrich_ranking(payload, result) if (req.usar_ia and llm.available()) else {"usada": False}
    q = " ".join([req.texto, " ".join(x.nome for x in req.skills), req.tipo_servico or ""])
    result["contexto_rag"] = get_rag().search(q, 3, only_docs=True) if q.strip() else []
    return result


@app.post("/api/extract")
async def extrair(arquivo: UploadFile | None = File(None), texto: str = Form(""), usar_ia: bool = Form(True),
                  ignorar_id: int | None = Form(None), u: dict = Depends(auth.usuario_logado)):
    s = sgd.get()
    conteudo = texto or ""
    bhash = None
    if arquivo is not None and arquivo.filename:
        data = await arquivo.read()
        if len(data) > 10 * 1024 * 1024:
            raise HTTPException(413, "O arquivo passa de 10 MB. Reduza imagens ou divida o documento.")
        bhash = hashlib.sha256(data).hexdigest()
        dup = buscas.duplicada(None, bhash, ignorar_id)
        if dup:
            raise HTTPException(409, {"mensagem": f"Este arquivo já foi usado na busca “{dup['nome']}” "
                                      f"(criada em {dup['criado_em'][:10]}). Abra a busca existente em vez de criar outra.",
                                      "busca_id": dup["id"]})
        try:
            conteudo = (extract.read_document(arquivo.filename, data) + "\n" + conteudo).strip()
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f"Não consegui ler o arquivo ({type(e).__name__}).") from e
    if not conteudo.strip():
        raise HTTPException(400, "Envie um arquivo ou um texto.")
    out = extract.extract(s, conteudo, use_ai=usar_ia)
    out.pop("aviso", None)  # detalhe técnico da IA fica só no log
    out["caracteres_lidos"] = len(conteudo)
    out["texto_completo"] = conteudo[:extract.MAX_CHARS]
    out["briefing_hash"] = bhash
    log.info("extract: %d caracteres, %d skills, origem=%s", len(conteudo), len(out["skills"]), out["origem"])
    return out


@app.get("/api/base/fontes")
def base_fontes(u: dict = Depends(auth.usuario_logado)):
    r, sg = get_rag(), sgd.get()
    n_proj = store.q("SELECT count(*) AS n FROM buscas", one=True)["n"]
    n_aloc = store.q("SELECT count(*) AS n FROM decisoes", one=True)["n"]
    return {"documentos": r.docs, "sgd": {"colaboradores": sum(c["ativo"] for c in sg.colabs.values()),
                                          "demandas": sum(d["ativa"] for d in sg.demandas.values()),
                                          "contratos": len(sg.contratos), "skills": len(sg.skills),
                                          "fonte": sg.source},
            "inhire": sum(t["ativo"] for t in sg.talentos.values()), "projetos": n_proj, "alocacoes": n_aloc,
            "trechos": len(r.chunks)}


@app.post("/api/base/documentos")
async def base_enviar(arquivo: UploadFile = File(...), u: dict = Depends(auth.usuario_logado)):
    import re as _re
    nome = _re.sub(r"[^\w.\- ]+", "_", (arquivo.filename or "documento").strip())[:120]
    if not nome.lower().endswith(rag.DOC_EXT):
        raise HTTPException(400, "Envie PDF, DOCX, TXT ou MD.")
    data = await arquivo.read()
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(413, "O arquivo passa de 15 MB.")
    destino = config.CORPUS_DIR / rag.ENVIADOS
    destino.mkdir(parents=True, exist_ok=True)
    (destino / nome).write_bytes(data)
    get_rag().recarregar()
    log.info("base: documento adicionado (%d bytes)", len(data))
    return {"ok": True, "nome": nome}


@app.delete("/api/base/documentos/{nome}")
def base_remover(nome: str, u: dict = Depends(auth.admin)):
    alvo = (config.CORPUS_DIR / rag.ENVIADOS / nome).resolve()
    if alvo.parent != (config.CORPUS_DIR / rag.ENVIADOS).resolve() or not alvo.exists():
        raise HTTPException(404, "Só documentos enviados pela tela podem ser removidos aqui.")
    alvo.unlink()
    get_rag().recarregar()
    return {"ok": True}


@app.post("/api/rag")
def perguntar(p: Pergunta, u: dict = Depends(auth.usuario_logado)):
    if not p.pergunta.strip():
        raise HTTPException(400, "Pergunta vazia.")
    return get_rag().answer(p.pergunta.strip())
