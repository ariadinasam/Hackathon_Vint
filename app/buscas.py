"""Buscas (projetos), decisões, dashboard e detalhe de candidato — orquestra matching + banco do app."""
from __future__ import annotations
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from . import config, llm, matching, store
from .textutil import fold
from .sgd import NIVEL_NOME, SGD, idx_label, month_idx

DURACAO = {"Até 1 mês": 1, "1–3 meses": 3, "3–6 meses": 6, "6–12 meses": 12, "Mais de 12 meses": 12}
INICIO = {"Imediato": 0, "Em 15 dias": 15, "Em 30 dias": 30, "Em 60 dias": 60}
MESES_LONGOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def hoje() -> date:
    raw = (config.reference_month())
    t = date.today()
    return t if (t.year, t.month) == raw else date(raw[0], raw[1], 1)


def _parse_data(v) -> date | None:
    v = (v or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", v) or None
    try:
        if m:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", v)
        if m:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None
    return None


def data_inicio(valor: str | None) -> date:
    """Aceita data (AAAA-MM-DD ou DD/MM/AAAA), atalho ("Em 15 dias") ou texto ("em 3 semanas")."""
    d = _parse_data(valor)
    if d:
        return d
    v = fold(valor or "").strip()
    for k, dias in INICIO.items():
        if fold(k) == v:
            return hoje() + timedelta(days=dias)
    if re.search(r"imediat|agora|ja\b", v):
        return hoje()
    for pad, mult in ((r"(\d+)\s*dia", 1), (r"(\d+)\s*semana", 7), (r"(\d+)\s*mes", 30)):
        m = re.search(pad, v)
        if m:
            return hoje() + timedelta(days=int(m.group(1)) * mult)
    return hoje() + timedelta(days=15)


def duracao_meses(valor: str | None, ini: date | None = None) -> tuple[int, bool]:
    """Duração em meses (1–24) a partir de atalho, texto livre ("10 semanas", "1 ano") ou data de término.
    Devolve (meses, entendido)."""
    if not valor or not str(valor).strip():
        return 6, True
    if valor in DURACAO:
        return DURACAO[valor], True
    ini = ini or hoje()
    fim = _parse_data(valor)
    if fim:
        return max(1, min(24, math.ceil(max((fim - ini).days, 1) / 30.4))), fim > ini
    v = fold(str(valor)).replace(",", ".")
    for k, n in DURACAO.items():
        if fold(k) == v:
            return n, True
    faixa = re.search(r"(\d+)\s*(?:a|-|–|ate)\s*(\d+)", v)
    num = float(faixa.group(2)) if faixa else None
    if num is None:
        m = re.search(r"(\d+(?:\.\d+)?)", v)
        num = float(m.group(1)) if m else None
    if num is None:
        return 6, False
    if "ano" in v:
        n = num * 12
    elif "semana" in v:
        n = num / 4.345
    elif "dia" in v:
        n = num / 30.4
    else:
        n = num
    return max(1, min(24, math.ceil(n))), True


def fmt_data(d: date) -> str:
    return f"{d.day:02d} {MESES_LONGOS[d.month - 1]}"


def fim_previsto(ini: date, meses: int) -> date:
    y, m = divmod(ini.month - 1 + meses, 12)
    import calendar
    ano, mes = ini.year + y, m + 1
    return date(ano, mes, min(ini.day, calendar.monthrange(ano, mes)[1])) - timedelta(days=1)


def params_para_match(p: dict) -> dict:
    ini = data_inicio(p.get("inicio") or "Em 15 dias")
    meses, _ = duracao_meses(p.get("duracao") or "3–6 meses", ini)
    return {
        "skills": p.get("skills") or [], "inicio": f"{ini.year}-{ini.month:02d}",
        "duracao_meses": meses,
        "disponibilidade_min": int(p.get("disponibilidade_min") or 50),
        "senioridades": p.get("senioridades") or [], "tipo_servico": (p.get("tipo_servico") or "").strip() or None,
        "metodologia": (p.get("metodologia") or "").strip() or None,
        "texto": "\n".join(x for x in [p.get("nome"), p.get("descricao"), p.get("briefing_texto")] if x),
        "incluir_externos": True,
    }


def preparar(s: SGD, p: dict, rag=None, fixar: dict | None = None) -> tuple[dict, dict]:
    """Ranking determinístico (rápido). A IA, quando usada, refina depois."""
    req = params_para_match(p)
    req["fixar"] = fixar or {}
    res = matching.run(s, req)
    if rag is not None:
        q = " ".join([p.get("descricao") or "", " ".join(x["nome"] for x in req["skills"])])
        res["contexto_rag"] = rag.search(q, 3, only_docs=True) if q.strip() else []
    ini = data_inicio(p.get("inicio") or "Em 15 dias")
    res["inicio_data"] = ini.isoformat()
    res["fim_data"] = fim_previsto(ini, req["duracao_meses"]).isoformat()
    res["duracao_meses"] = req["duracao_meses"]
    res["ia"] = {"usada": False}
    return req, res


def executar(s: SGD, p: dict, rag=None, usar_ia: bool = True, fixar: dict | None = None) -> dict:
    req, res = preparar(s, p, rag, fixar)
    if usar_ia and llm.available():
        res["ia"] = llm.enrich_ranking(req, res)
    return res


def previa(s: SGD, p: dict) -> dict:
    """Números ao vivo para o painel do formulário (nada que já esteja escrito nos campos)."""
    req = params_para_match(p)
    ini = data_inicio(p.get("inicio") or "Em 15 dias")
    meses, ok = duracao_meses(p.get("duracao"), ini)
    res = matching.run(s, req) if req["skills"] else None
    out = {"inicio": ini.isoformat(), "fim": fim_previsto(ini, meses).isoformat(), "meses": meses,
           "duracao_entendida": ok, "tem_skills": bool(req["skills"])}
    if res:
        r = res["resumo"]
        out.update({
            "periodo": res["periodo"]["rotulo"], "aptos": r["aptos"], "disponiveis": r["disponiveis"],
            "remanejamento": r["aptos"] - r["disponiveis"], "quase_la": r.get("quase_la_total", r["quase_la"]),
            "externos": r.get("externos_total", len(res["externos"])),
            "sem_ninguem": [q["nome"] for q in res["requisitos"] if q["no_catalogo"] and q["colabs_com_skill"] == 0],
            "fora_catalogo": [q["nome"] for q in res["requisitos"] if not q["no_catalogo"]],
            "alem_planejamento": res["periodo"]["meses"][-1] if any("planejamento no SGD" in a for a in res["avisos"]) else None,
            "horizonte": res["periodo"]["horizonte_planejamento"],
        })
    return out


def chave_nome(nome: str) -> str:
    import re as _re
    import unicodedata as _u
    n = _u.normalize("NFKD", nome or "")
    n = "".join(c for c in n if not _u.combining(c)).lower()
    return _re.sub(r"[^a-z0-9]+", " ", n).strip()


def duplicada(nome: str | None, briefing_hash: str | None, ignorar_id: int | None = None) -> dict | None:
    """Já existe busca com o mesmo nome (sem acento/caixa/pontuação) ou com o mesmo arquivo de briefing?"""
    if nome:
        b = store.q("SELECT b.id, b.nome, b.criado_em, u.nome AS autor FROM buscas b LEFT JOIN usuarios u ON u.id=b.usuario_id "
                    "WHERE b.nome_chave=? AND b.id<>?", (chave_nome(nome), ignorar_id or 0), one=True)
        if b:
            return {"campo": "nome", **b}
    if briefing_hash:
        b = store.q("SELECT b.id, b.nome, b.criado_em, b.briefing_nome, u.nome AS autor FROM buscas b "
                    "LEFT JOIN usuarios u ON u.id=b.usuario_id WHERE b.briefing_hash=? AND b.id<>?",
                    (briefing_hash, ignorar_id or 0), one=True)
        if b:
            return {"campo": "briefing", **b}
    return None


def salvar(usuario_id: int, p: dict, res: dict | None) -> int:
    agora = store.now()
    n_t = (len(res["ranking"]) + len(res["externos"])) if res else None
    n_r = sum(1 for c in res["ranking"] if c.get("remanejamento")) if res else None
    params = {k: v for k, v in p.items() if k != "briefing_texto"}
    return store.x(
        "INSERT INTO buscas(usuario_id,nome,descricao,params_json,resultado_json,status,n_talentos,n_remanejamento,"
        "briefing_nome,briefing_hash,nome_chave,criado_em,atualizado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (usuario_id, p.get("nome") or "Sem nome", p.get("descricao"), store.dumps(params),
         store.dumps(res) if res else None, "aguardando" if res else "rascunho", n_t, n_r,
         p.get("briefing_nome"), p.get("briefing_hash"), chave_nome(p.get("nome") or ""), agora, agora))


def fixados_da_busca(busca_id: int) -> dict:
    ds = store.q("SELECT origem, candidato_id FROM decisoes WHERE busca_id=?", (busca_id,))
    return {"interno": [d["candidato_id"] for d in ds if d["origem"] == "interno"],
            "ihiring": [d["candidato_id"] for d in ds if d["origem"] == "ihiring"]}


def atualizar(busca_id: int, p: dict, res: dict | None):
    n_t = (len(res["ranking"]) + len(res["externos"])) if res else None
    n_r = sum(1 for c in res["ranking"] if c.get("remanejamento")) if res else None
    params = {k: v for k, v in p.items() if k != "briefing_texto"}
    store.x("UPDATE buscas SET nome=?,descricao=?,params_json=?,resultado_json=?,status=?,n_talentos=?,"
            "n_remanejamento=?,briefing_nome=?,briefing_hash=?,nome_chave=?,atualizado_em=? WHERE id=?",
            (p.get("nome") or "Sem nome", p.get("descricao"), store.dumps(params), store.dumps(res) if res else None,
             _status_apos_edicao(busca_id, res), n_t, n_r, p.get("briefing_nome"), p.get("briefing_hash"),
             chave_nome(p.get("nome") or ""), store.now(), busca_id))


def _status_apos_edicao(busca_id: int, res: dict | None) -> str:
    tem = store.q("SELECT 1 FROM decisoes WHERE busca_id=? LIMIT 1", (busca_id,), one=True)
    return "confirmada" if tem else ("aguardando" if res else "rascunho")


def carregar(busca_id: int) -> dict | None:
    b = store.q("SELECT b.*, u.nome AS autor FROM buscas b LEFT JOIN usuarios u ON u.id=b.usuario_id WHERE b.id=?",
                (busca_id,), one=True)
    if not b:
        return None
    b["params"] = json.loads(b.pop("params_json"))
    b["resultado"] = json.loads(b.pop("resultado_json")) if b.get("resultado_json") else None
    b["decisoes"] = store.q("SELECT origem, candidato_id, percentual, remanejamento, criado_em FROM decisoes "
                            "WHERE busca_id=?", (busca_id,))
    return b


def listar(limite: int = 50) -> list[dict]:
    rows = store.q("SELECT b.id,b.nome,b.status,b.n_talentos,b.n_remanejamento,b.criado_em,b.params_json,"
                   "u.nome AS autor, b.usuario_id, (SELECT count(*) FROM decisoes d WHERE d.busca_id=b.id) AS n_alocados "
                   "FROM buscas b LEFT JOIN usuarios u ON u.id=b.usuario_id "
                   "ORDER BY b.criado_em DESC, b.id DESC LIMIT ?", (limite,))
    for r in rows:
        p = json.loads(r.pop("params_json"))
        r["skills"] = [x["nome"] for x in p.get("skills", [])]
    return rows


def decidir(s: SGD, busca: dict, usuario_id: int, selecionados: list[dict]) -> int:
    res = busca["resultado"] or {}
    need = res.get("disponibilidade_min", 50)
    internos = {c["id"]: c for c in res.get("ranking", []) + res.get("quase_la", []) + res.get("fixados", [])}
    externos = {t["id"]: t for t in res.get("externos", []) + res.get("externos_fixados", [])}
    ja = {(d["origem"], d["candidato_id"]) for d in busca.get("decisoes", [])}
    n = 0
    for sel in selecionados:
        origem, cid = sel.get("origem"), int(sel.get("id"))
        base = internos if origem == "interno" else externos if origem == "ihiring" else {}
        if cid not in base or (origem, cid) in ja:
            continue
        rem = bool(origem == "interno" and base[cid].get("remanejamento"))
        store.x("INSERT INTO decisoes(busca_id,usuario_id,origem,candidato_id,percentual,remanejamento,criado_em) "
                "VALUES (?,?,?,?,?,?,?)", (busca["id"], usuario_id, origem, cid, need, int(rem), store.now()))
        n += 1
    if n:
        store.x("UPDATE buscas SET status='confirmada', atualizado_em=? WHERE id=?", (store.now(), busca["id"]))
    return n


def excluir(busca_id: int):
    """Apaga o projeto e as alocações registradas nele (só no banco do app; o SGD não é tocado)."""
    store.x("DELETE FROM decisoes WHERE busca_id=?", (busca_id,))
    store.x("DELETE FROM buscas WHERE id=?", (busca_id,))


def remover_decisao(busca_id: int, origem: str, cid: int) -> int:
    store.x("DELETE FROM decisoes WHERE busca_id=? AND origem=? AND candidato_id=?", (busca_id, origem, cid))
    resta = store.q("SELECT count(*) AS n FROM decisoes WHERE busca_id=?", (busca_id,), one=True)["n"]
    if not resta:
        store.x("UPDATE buscas SET status='aguardando', atualizado_em=? WHERE id=?", (store.now(), busca_id))
    return resta


def mudar_percentual(busca_id: int, origem: str, cid: int, pct: int):
    store.x("UPDATE decisoes SET percentual=? WHERE busca_id=? AND origem=? AND candidato_id=?",
            (max(5, min(100, int(pct))), busca_id, origem, cid))


def nome_candidato(s: SGD, origem: str, cid: int) -> str:
    if origem == "interno":
        return s.colabs.get(cid, {}).get("nome", f"Colaborador {cid}")
    return s.talentos.get(cid, {}).get("nome", f"Talento {cid}")


def dashboard(s: SGD, u: dict) -> dict:
    abertas = store.q("SELECT id, nome, usuario_id, n_remanejamento FROM buscas WHERE status='aguardando' "
                      "ORDER BY criado_em DESC")
    livres = sum(1 for cid, c in s.colabs.items() if c["ativo"] and s.availability(cid, [s.ref_idx])[s.ref_idx] >= 100)
    decs = store.q("SELECT d.*, b.nome AS projeto, u.nome AS autor FROM decisoes d JOIN buscas b ON b.id=d.busca_id "
                   "LEFT JOIN usuarios u ON u.id=d.usuario_id ORDER BY d.criado_em DESC, d.id DESC LIMIT 5")
    return {
        "projetos_abertos": len(abertas), "talentos_disponiveis": livres,
        "remanejamentos": sum(b["n_remanejamento"] or 0 for b in abertas),
        "minhas_pendentes": [{"id": b["id"], "nome": b["nome"]} for b in abertas if b["usuario_id"] == u["id"]][:3],
        "ultimas_decisoes": [{
            "candidato": nome_candidato(s, d["origem"], d["candidato_id"]), "origem": d["origem"],
            "projeto": d["projeto"], "busca_id": d["busca_id"], "percentual": d["percentual"],
            "remanejamento": bool(d["remanejamento"]), "criado_em": d["criado_em"],
            "por_voce": d["usuario_id"] == u["id"], "autor": d["autor"]} for d in decs],
        "buscas_recentes": listar(5), "mes_referencia": idx_label(s.ref_idx),
    }


# ------------------------------------------------------------------ detalhe do candidato
def _timeline(s: SGD, cid: int, res: dict) -> dict:
    meses_busca = [month_idx(int(m.split("/")[1]) + 2000, matching_mes(m)) for m in res["periodo"]["meses"]]
    ini = min(s.ref_idx, meses_busca[0])
    janela = list(range(ini, ini + 6))
    linhas = []
    for aid in s.allocs_by_colab.get(cid, []):
        a = s.aloc[aid]
        if not a["ativa"]:
            continue
        cel = {m: p for m, p in s.plan.get(aid, {}).items() if m in janela and p > 0}
        if not cel:
            continue
        d = s.demandas[a["demanda"]]
        linhas.append({"projeto": d["nome"], "andamento": d["andamento"], "tipo_servico": d["tipo_servico"],
                       "celulas": [cel.get(m, 0) for m in janela]})
    need = res.get("disponibilidade_min", 50)
    proposta = [need if m in meses_busca else 0 for m in janela]
    total = [s.load.get(cid, {}).get(m, 0) for m in janela]
    return {"meses": [idx_label(m) for m in janela], "linhas": linhas, "proposta": proposta, "total": total}


def matching_mes(rotulo: str) -> int:
    from . import config as _c
    return _c.MESES.index(rotulo.split("/")[0]) + 1


def motivos_interno(res: dict, c: dict) -> list[dict]:
    """Motivos legíveis do match (usados no detalhe e no relatório)."""
    mot = []
    tem = [x for x in c["skills_match"] if x["ok"]]
    if tem:
        ev = [x["nome"] for x in tem if x["evidencia_projeto"]]
        mot.append({"ok": True, "forte": f"Atende {len(tem)} das {len(c['skills_match'])} skills pedidas",
                    "texto": ", ".join(f'{x["nome"]} ({x["nivel_atual"].lower()})' for x in tem)
                    + (f" — {', '.join(ev)} usada(s) em projetos registrados." if ev else ".")})
    if c["historico_similar"]:
        hs = c["historico_similar"]
        mot.append({"ok": True, "forte": f"{len(hs)} projeto(s) similar(es)",
                    "texto": "; ".join(f'{h["demanda"]} ({h["tipo_servico"]} · {h["metodologia"]}, {h["periodo"]}, '
                                       f'{h["similaridade"]}% similar)' for h in hs) + "."})
    if c["disponivel"]:
        mot.append({"ok": True, "forte": "Disponível no período",
                    "texto": f"média de {c['disp_media']}% livre em {res['periodo']['rotulo']}."})
    elif c.get("remanejamento"):
        r = c["remanejamento"]
        mot.append({"ok": True, "forte": "Disponibilidade negociável",
                    "texto": "precisa liberar " + ", ".join(f'{x["liberar_pct"]}% em {x["mes"]}' for x in r["liberar_por_mes"])
                    + f" — viabilidade {r['viabilidade'].lower()}."})
    if c.get("justificativa_regra"):  # houve IA: mostra a leitura da IA também
        mot.append({"ok": True, "forte": "Leitura da IA", "texto": c["justificativa"]})
    lacunas = [x for x in c["skills_match"] if not x["ok"]]
    for x in lacunas[:3]:
        outro = next((o for o in res["ranking"] if o["id"] != c["id"] and
                      any(k["nome"] == x["nome"] and k["ok"] for k in o["skills_match"])), None)
        txt = (f'{x["nome"]} — pedido {x["nivel_pedido"].lower()}, atual {x["nivel_atual"].lower()}.'
               if x["nivel_atual"] != "—" else f'sem {x["nome"]} registrado no SGD.')
        if outro:
            txt += f' Compense no squad com {outro["nome"]} ({round(outro["score"])}%).'
        mot.append({"ok": False, "forte": "Lacuna:", "texto": txt, "par_id": outro["id"] if outro else None})
    return mot


def detalhe_interno(s: SGD, busca: dict, cid: int) -> dict | None:
    res = busca["resultado"]
    pool = res.get("ranking", []) + res.get("quase_la", []) + res.get("fixados", [])
    c = next((x for x in pool if x["id"] == cid), None)
    if not c:
        return None
    col = s.colabs[cid]
    need = res.get("disponibilidade_min", 50)
    tl = _timeline(s, cid, res)
    # ficha
    ref = s.ref_idx
    atuais = [h for h in s.history(cid) if h["ativa"] and s.plan.get(h["aloc_id"], {}).get(ref, 0) > 0]
    principal = max(atuais, key=lambda h: s.plan[h["aloc_id"]].get(ref, 0), default=None)
    gestor = s.colabs.get(s.demandas[principal["demanda_id"]]["gerente_id"], {}).get("nome") if principal else None
    pode = next((m["mes"] for m in c["disp_meses"] if m["disp"] >= need), None)
    mot = motivos_interno(res, c)
    # remanejamento sugerido + quem cobre
    rem = None
    if c.get("remanejamento") and c["remanejamento"]["alocacoes"]:
        a0 = c["remanejamento"]["alocacoes"][0]
        dem = next((d for d in s.demandas.values() if d["nome"] == a0["demanda"]), None)
        cobre = None
        if dem and dem["skills"]:
            meses_conf = [m["mes"] for m in a0["meses"]]
            req = {"skills": [{"nome": s.skills[k]["nome"], "obrigatoria": False} for k in dem["skills"] if k in s.skills],
                   "inicio": None, "duracao_meses": 1, "disponibilidade_min": max(m["pct"] for m in a0["meses"]),
                   "incluir_externos": True}
            ini = meses_conf[0]
            req["inicio"] = f"{2000 + int(ini.split('/')[1])}-{matching_mes(ini):02d}"
            req["duracao_meses"] = len(meses_conf)
            alt = matching.run(s, req)
            cand = next((o for o in alt["ranking"] if o["id"] != cid and o["disponivel"]), None)
            if cand:
                cobre = {"origem": "interno", "id": cand["id"], "nome": cand["nome"], "score": cand["score"]}
            elif alt["externos"]:
                e = alt["externos"][0]
                cobre = {"origem": "ihiring", "id": e["id"], "nome": e["nome"], "score": e["score"]}
        rem = {**c["remanejamento"], "principal": a0, "cobre": cobre}
    return {
        "origem": "interno", "candidato": c, "rem": rem, "motivos": mot, "timeline": tl,
        "ficha": {"email": None, "gestor": gestor, "local": f'{col["modalidade"]} · {col["vinculo"]}',
                  "desde": (col["admissao"] or "")[:4] or None,
                  "alocacao_hoje": s.load.get(cid, {}).get(ref, 0), "n_projetos_hoje": len(atuais),
                  "pode_comecar": (f"{res['periodo']['meses'][0]}" if c["disponivel"] else
                                   f"{res['periodo']['meses'][0]} com remanejamento" + (f" · livre sem mexer a partir de {pode}" if pode else ""))},
        "busca": {"id": busca["id"], "nome": busca["nome"], "status": busca["status"]},
        "selecionado": any(d["origem"] == "interno" and d["candidato_id"] == cid for d in busca["decisoes"]),
    }


def detalhe_externo(s: SGD, busca: dict, tid: int) -> dict | None:
    res = busca["resultado"]
    e = next((x for x in res.get("externos", []) + res.get("externos_fixados", []) if x["id"] == tid), None)
    t = s.talentos.get(tid)
    if not e or not t:
        return None
    pedidas = {x["nome"] for x in res.get("requisitos", [])}
    skills = [{"nome": s.skills[k]["nome"], "nivel": NIVEL_NOME[lv], "pedida": s.skills[k]["nome"] in pedidas}
              for k, lv in s.tskills.get(tid, {}).items()]
    return {"origem": "ihiring", "candidato": e, "skills": skills,
            "faltando": [x for x in pedidas if x not in e["skills_atendidas"]],
            "busca": {"id": busca["id"], "nome": busca["nome"], "status": busca["status"]},
            "selecionado": any(d["origem"] == "ihiring" and d["candidato_id"] == tid for d in busca["decisoes"])}


def relatorio(s: SGD, busca: dict) -> dict:
    """Relatório do projeto: quem foi alocado, por quê, cobertura das skills e pontos de atenção."""
    res = busca["resultado"] or {}
    p = busca["params"]
    need = res.get("disponibilidade_min", 50)
    internos = {c["id"]: c for c in res.get("fixados", []) + res.get("quase_la", []) + res.get("ranking", [])}
    externos = {t["id"]: t for t in res.get("externos_fixados", []) + res.get("externos", [])}
    decs = store.q("SELECT d.origem, d.candidato_id, d.percentual, d.remanejamento, d.criado_em, u.nome AS por "
                   "FROM decisoes d LEFT JOIN usuarios u ON u.id=d.usuario_id WHERE d.busca_id=? ORDER BY d.criado_em, d.id",
                   (busca["id"],))
    pessoas = []
    for d in decs:
        base = {"origem": d["origem"], "id": d["candidato_id"], "percentual": d["percentual"],
                "alocado_em": d["criado_em"], "alocado_por": d["por"]}
        if d["origem"] == "interno" and d["candidato_id"] in internos:
            c = internos[d["candidato_id"]]
            rem = c.get("remanejamento")
            pessoas.append({**base, "nome": c["nome"], "cargo": c["cargo"], "senioridade": c["senioridade"],
                            "modalidade": c.get("modalidade"), "score": c["score"],
                            "justificativa": c.get("justificativa"), "justificativa_ia": bool(c.get("justificativa_regra")),
                            "motivos": motivos_interno(res, c),
                            "skills": [{"nome": x["nome"], "obrigatoria": x["obrigatoria"], "pedido": x["nivel_pedido"],
                                        "atual": x["nivel_atual"], "ok": x["ok"]} for x in c["skills_match"]],
                            "disp_meses": c["disp_meses"], "disponivel": c["disponivel"],
                            "remanejamento": {"liberar_por_mes": rem["liberar_por_mes"], "viabilidade": rem["viabilidade"],
                                              "alocacoes": [a["demanda"] for a in rem.get("alocacoes", [])][:3]} if rem else None,
                            "historico": [{"demanda": h["demanda"], "tipo_servico": h["tipo_servico"],
                                           "similaridade": h["similaridade"]} for h in c.get("historico_similar", [])][:3],
                            "pdi": [{"skill": x["skill"], "de": x["de"], "para": x["para"],
                                     "mentor": x.get("mentor_sugerido")} for x in c.get("pdi", [])],
                            "pdi_resumo": c.get("pdi_resumo")})
        elif d["origem"] == "ihiring" and d["candidato_id"] in externos:
            t = externos[d["candidato_id"]]
            pedidas = [r["nome"] for r in res.get("requisitos", [])]
            pessoas.append({**base, "nome": t["nome"], "cargo": t["cargo"], "senioridade": t["senioridade"],
                            "modalidade": t.get("modalidade"), "score": t["score"],
                            "justificativa": f"Talento externo com {len(t['skills_atendidas'])} das {len(pedidas)} skills "
                                             f"pedidas e {t['disponibilidade']}% de disponibilidade informada.",
                            "skills": [{"nome": n, "ok": n in t["skills_atendidas"]} for n in pedidas],
                            "disponibilidade_informada": t["disponibilidade"], "fonte": t.get("fonte")})
    # cobertura: cada skill pedida é atendida por alguém do time?
    cobertura = []
    for r in res.get("requisitos", []):
        quem = [{"nome": x["nome"], "nivel": next((k.get("atual") for k in x["skills"] if k["nome"] == r["nome"]), None)}
                for x in pessoas if any(k["nome"] == r["nome"] and k["ok"] for k in x["skills"])]
        parcial = [x["nome"] for x in pessoas if x["origem"] == "interno" and any(
            k["nome"] == r["nome"] and not k["ok"] and k["atual"] != "—" for k in x["skills"])]
        cobertura.append({"skill": r["nome"], "obrigatoria": r["obrigatoria"] or r.get("rebaixada", False),
                          "nivel": r["nivel"], "atendida_por": quem, "abaixo_do_nivel": parcial})
    atencao = []
    sem = [c["skill"] for c in cobertura if not c["atendida_por"]]
    if sem:
        atencao.append(f"Ninguém do time atende no nível pedido: {', '.join(sem)}.")
    nrem = [x["nome"] for x in pessoas if x.get("remanejamento")]
    if nrem:
        atencao.append(f"Depende de remanejamento: {', '.join(nrem)} — combinar com os gestores atuais.")
    if any(x["origem"] == "ihiring" for x in pessoas):
        atencao.append("Há talentos do iHiring no time: a base de teste é sintética; confirmar disponibilidade e contratação.")
    if (res.get("periodo") or {}).get("meses") and res["periodo"].get("horizonte_planejamento") and \
            any("planejamento no SGD" in a for a in res.get("avisos", [])):
        atencao.append(f"O planejamento do SGD vai só até {res['periodo']['horizonte_planejamento']}; "
                       "a disponibilidade depois disso é estimada.")
    outros = [{"nome": c["nome"], "cargo": c["cargo"], "score": c["score"], "disponivel": c["disponivel"]}
              for c in res.get("ranking", []) if c["id"] not in {x["id"] for x in pessoas if x["origem"] == "interno"}][:5]
    return {
        "projeto": {"id": busca["id"], "nome": busca["nome"], "descricao": p.get("descricao"), "autor": busca.get("autor"),
                    "criado_em": busca["criado_em"], "atualizado_em": busca.get("atualizado_em"), "status": busca["status"],
                    "periodo": (res.get("periodo") or {}).get("rotulo"), "inicio": res.get("inicio_data"),
                    "fim": res.get("fim_data"), "duracao_meses": res.get("duracao_meses"), "dedicacao_min": need,
                    "tipo_servico": p.get("tipo_servico"), "metodologia": p.get("metodologia"),
                    "senioridades": p.get("senioridades") or [], "briefing": p.get("briefing_nome"),
                    "requisitos": res.get("requisitos", []), "ia_usada": bool((res.get("ia") or {}).get("usada"))},
        "pessoas": pessoas,
        "resumo": {"total": len(pessoas), "internos": sum(x["origem"] == "interno" for x in pessoas),
                   "externos": sum(x["origem"] == "ihiring" for x in pessoas), "remanejamento": len(nrem),
                   "skills_cobertas": sum(1 for c in cobertura if c["atendida_por"]), "skills_total": len(cobertura),
                   "dedicacao_total": sum(x["percentual"] or 0 for x in pessoas),
                   "dedicacao_media": round(sum(x["percentual"] or 0 for x in pessoas) / len(pessoas)) if pessoas else 0},
        "cobertura": cobertura, "atencao": atencao, "outros_sugeridos": outros,
        "gerado_em": store.now(),
    }
