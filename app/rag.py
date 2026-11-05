"""Base de conhecimento (RAG) do VINT Match.

Fontes: (1) consultas AO VIVO ao SGD conforme a pergunta (skills, disponibilidade, contratos, pessoas, contagens);
(2) fichas indexadas de skills, demandas, contratos, colaboradores e talentos; (3) projetos/alocações do app (data/app.db);
(4) documentos em docs/corpus (md, txt, pdf, docx — inclusive os enviados pela tela).
Para a IA, pessoas viram pseudônimos ("Colaborador 129", "Talento 029"); a resposta volta com os nomes reais.
"""
from __future__ import annotations
import logging
import re
from collections import Counter
import json
import unicodedata
from pathlib import Path
from . import config, llm, store
from .sgd import SGD, NIVEL_NOME, idx_label, month_idx
from .textutil import TfIdf

log = logging.getLogger("vintmatch.rag")


def _chunk_markdown(name: str, text: str, size: int = 900) -> list[dict]:
    chunks, title, buf = [], name, []

    def flush():
        body = "\n".join(buf).strip()
        while body:
            piece, body = body[:size], body[size:]
            if body:  # corta no último fim de linha para não quebrar tabela/frase
                cut = piece.rfind("\n")
                if cut > size // 2:
                    body = piece[cut:] + body
                    piece = piece[:cut]
            chunks.append({"fonte": name, "secao": title, "texto": piece.strip()})
        buf.clear()

    for line in text.splitlines():
        if re.match(r"^#{1,4} ", line):
            flush()
            title = line.lstrip("# ").strip()
        else:
            buf.append(line)
    flush()
    return [c for c in chunks if len(c["texto"]) > 40]


def _fichas(s: SGD) -> list[dict]:
    out = []
    ativos = {cid for cid, c in s.colabs.items() if c["ativo"]}
    dem_por_skill: dict[int, list] = {}
    for d in s.demandas.values():
        for sid in d["skills"]:
            dem_por_skill.setdefault(sid, []).append(d)
    for sid, sk in s.skills.items():
        niveis = Counter(s.cskills[c][sid] for c in ativos if sid in s.cskills.get(c, {}))
        dems = dem_por_skill.get(sid, [])
        tal = sum(1 for t in s.tskills.values() if sid in t)
        txt = (f"Skill {sk['nome']} (área {sk['area']}). Colaboradores ativos com a skill: {sum(niveis.values())} "
               f"({niveis.get(3, 0)} avançados, {niveis.get(2, 0)} intermediários, {niveis.get(1, 0)} básicos). "
               f"Demandas que exigem: {len(dems)}"
               + (f" ({', '.join(d['nome'] + ' - ' + (d['tipo_servico'] or '') for d in dems[:6])})" if dems else "")
               + f". Talentos externos InHire (sintéticos) com a skill: {tal}.")
        out.append({"fonte": "SGD · ficha de skill", "secao": sk["nome"], "texto": txt})
    for d in s.demandas.values():
        if not d["ativa"]:
            continue
        k = s.contratos.get(d["contrato_id"], {})
        equipe = sum(1 for a in s.aloc.values() if a["demanda"] == d["id"] and a["ativa"])
        txt = (f"{d['nome']}: contrato {k.get('nome')} ({k.get('situacao')}), serviço {d['tipo_servico']}, "
               f"metodologia {d['metodologia']}, andamento {d['andamento']}, período {d['inicio']} a {d['termino']}"
               + ("" if d["datas_confiaveis"] else " (datas de placeholder, não confiáveis)")
               + f". Equipe alocada ativa: {equipe} pessoas. Skills exigidas: "
               + (", ".join(s.skills[x]["nome"] for x in d["skills"] if x in s.skills) or "não cadastradas") + ".")
        out.append({"fonte": "SGD · ficha de demanda", "secao": d["nome"], "texto": txt})
    return out


MESES_TXT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DOC_EXT = (".md", ".txt", ".pdf", ".docx")
ENVIADOS = "enviados"


def _fold(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def pc(cid: int) -> str:
    return f"Colaborador {cid:03d}"


def pt(tid: int) -> str:
    return f"Talento {tid:03d}"


def _ler_documento(p: Path) -> str:
    if p.suffix.lower() in (".md", ".txt"):
        return p.read_text(encoding="utf-8", errors="replace")
    from .extract import read_document
    return read_document(p.name, p.read_bytes())


def _fichas_extra(s: SGD) -> list[dict]:
    """Fichas de contratos, colaboradores ativos e talentos (pseudonimizados) + visão geral do SGD."""
    out = []
    ref = s.ref_idx
    meses = list(range(ref, ref + 4))
    for k in s.contratos.values():
        dems = [d for d in s.demandas.values() if d["contrato_id"] == k["id"] and d["ativa"]]
        pessoas = {a["colab"] for a in s.aloc.values() if a["ativa"] and s.demandas[a["demanda"]]["contrato_id"] == k["id"]
                   and s.plan.get(a["id"], {}).get(ref, 0) > 0}
        out.append({"fonte": "SGD · ficha de contrato", "secao": k["nome"],
                    "texto": f"{k['nome']}: situação {k['situacao']}, vigência {k['inicio']} a {k['termino']}. "
                             f"{len(dems)} demandas ativas; {len(pessoas)} pessoas alocadas em {idx_label(ref)}."})
    for cid, c in s.colabs.items():
        if not c["ativo"]:
            continue
        cs = s.cskills.get(cid, {})
        av = sorted((s.skills[k]["nome"] for k, lv in cs.items() if lv == 3))[:20]
        it = sorted((s.skills[k]["nome"] for k, lv in cs.items() if lv == 2))[:12]
        disp = s.availability(cid, meses)
        hist = []
        for h in s.history(cid)[:6]:
            d = s.demandas[h["demanda_id"]]
            hist.append(f"{d['nome']} ({d['tipo_servico']}, {d['metodologia']}, {h['de']}–{h['ate']}{', atual' if h['ativa'] else ''})")
        out.append({"fonte": "SGD · ficha de colaborador", "secao": pc(cid), "pessoa": ("interno", cid),
                    "texto": f"{pc(cid)}: {c['cargo']}, {c['senioridade']}, {c['modalidade']}, {c['vinculo']}, admissão {c['admissao'] or '—'}. "
                             f"Skills avançadas: {', '.join(av) or 'nenhuma'}. Intermediárias: {', '.join(it) or 'nenhuma'}. "
                             f"{len(cs)} skills declaradas. Livre: " + ", ".join(f"{idx_label(m)} {v}%" for m, v in disp.items())
                             + f". Projetos: {'; '.join(hist) or 'sem histórico no SGD'}."})
    for tid, t in s.talentos.items():
        if not t["ativo"]:
            continue
        sk = ", ".join(f"{s.skills[k]['nome']} ({NIVEL_NOME[lv].lower()})" for k, lv in s.tskills.get(tid, {}).items())
        out.append({"fonte": "InHire · talento externo (sintético)", "secao": pt(tid), "pessoa": ("ihiring", tid),
                    "texto": f"{pt(tid)}: {t['cargo']}, {t['senioridade']}, {t['modalidade']}, disponibilidade informada "
                             f"{t['disponibilidade']}%. Skills: {sk}."})
    out.append(_visao_geral(s))
    return out


def _visao_geral(s: SGD) -> dict:
    ativos = [c for c in s.colabs.values() if c["ativo"]]
    sen = Counter(c["senioridade"] for c in ativos).most_common()
    car = Counter(c["cargo"] for c in ativos).most_common(8)
    mod = Counter(c["modalidade"] for c in ativos).most_common()
    vin = Counter(c["vinculo"] for c in ativos).most_common()
    txt = (f"O SGD tem {len(ativos)} colaboradores ativos ({len(s.colabs)} cadastrados), {len(s.skills)} skills no catálogo, "
           f"{sum(d['ativa'] for d in s.demandas.values())} demandas ativas, {len(s.contratos)} contratos e "
           f"{sum(t['ativo'] for t in s.talentos.values())} talentos externos no InHire (base sintética). "
           f"Por senioridade: {', '.join(f'{k} {v}' for k, v in sen)}. Cargos mais comuns: {', '.join(f'{k} {v}' for k, v in car)}. "
           f"Modalidade: {', '.join(f'{k} {v}' for k, v in mod)}. Vínculo: {', '.join(f'{k} {v}' for k, v in vin)}. "
           f"Planejamento registrado até {idx_label(s.plan_horizon)}.")
    return {"fonte": "SGD · visão geral", "secao": "Totais do banco", "texto": txt}


class RAG:
    def __init__(self, s: SGD):
        self.s = s
        self.recarregar()

    # ------------------------------------------------------------ índice
    def documentos(self) -> list[Path]:
        base = config.CORPUS_DIR
        arqs = [p for p in base.glob("*") if p.suffix.lower() in DOC_EXT]
        arqs += [p for p in (base / ENVIADOS).glob("*") if p.suffix.lower() in DOC_EXT]
        return sorted(arqs, key=lambda p: (p.parent.name == ENVIADOS, p.name.lower()))

    def recarregar(self):
        self.chunks, self.docs = [], []
        for p in self.documentos():
            try:
                txt = _ler_documento(p)
            except Exception as e:  # noqa: BLE001
                log.warning("RAG: não consegui ler %s (%s)", p.name, type(e).__name__)
                continue
            ch = _chunk_markdown(p.name, txt)
            self.chunks += ch
            self.docs.append({"nome": p.name, "trechos": len(ch), "enviado": p.parent.name == ENVIADOS,
                              "bytes": p.stat().st_size})
        self.chunks += _fichas(self.s) + _fichas_extra(self.s)
        self.index = TfIdf([f"{c['secao']} {c['secao']} {c['texto']}" for c in self.chunks])
        log.info("RAG: %d trechos indexados (%d documentos)", len(self.chunks), len(self.docs))

    def search(self, q: str, k: int = 5, only_docs: bool = False) -> list[dict]:
        res = []
        for i, sc in self.index.top(q, len(self.chunks) if only_docs else k):
            c = self.chunks[i]
            if only_docs and (c["fonte"].startswith("SGD") or c["fonte"].startswith("InHire")):
                continue
            res.append({**c, "score": round(sc, 3)})
            if len(res) == k:
                break
        return res

    # ------------------------------------------------------------ consultas ao vivo
    def _meses_da_pergunta(self, q: str) -> list[int]:
        f = _fold(q)
        achados = []
        for m in re.finditer(r"\b(" + "|".join(MESES_TXT) + r")[a-z]*\.?(?:\s*(?:de\s*|/)?\s*(20\d\d|\d\d)\b)?", f):
            mes = MESES_TXT.index(m.group(1)[:3]) + 1
            ano = m.group(2)
            ano = (int(ano) + (2000 if len(ano) == 2 else 0)) if ano else None
            if ano is None:
                ref_ano, ref_mes = divmod(self.s.ref_idx, 12)
                ano = ref_ano if mes >= ref_mes + 1 else ref_ano + 1
            achados.append(month_idx(ano, mes))
        return sorted(set(achados)) or list(range(self.s.ref_idx, self.s.ref_idx + 3))

    def _pessoas_citadas(self, q: str) -> list[int]:
        f = _fold(q)
        ids = [int(x) for x in re.findall(r"colaborador\s+(\d{1,4})", f)]
        for cid, c in self.s.colabs.items():
            partes = [p for p in _fold(c["nome"]).split() if p != "mocado"]
            if len(partes) >= 2 and " ".join(partes[:2]) in f:
                ids.append(cid)
        return list(dict.fromkeys(i for i in ids if i in self.s.colabs))[:3]

    def consulta_ao_vivo(self, q: str) -> list[dict]:
        from .extract import rules_extract
        s, f, out = self.s, _fold(q), []
        meses = self._meses_da_pergunta(q)
        rot = ", ".join(idx_label(m) for m in meses)
        skills = [x["nome"] for x in rules_extract(s, q).get("skills", [])][:4]
        ativos = [cid for cid, c in s.colabs.items() if c["ativo"]]
        quer_disp = bool(re.search(r"livre|dispon|ocios|bench|capacidad|folga|sem projeto|alocad", f))
        for nome in skills:
            ids = s.resolve_skill(nome)
            tem = [(cid, max(s.cskills.get(cid, {}).get(i, 0) for i in ids)) for cid in ativos]
            nivel_min = 3 if re.search(r"avancad|senior|especialista", f) else 2 if "intermedi" in f else 1
            tem = [(cid, lv) for cid, lv in tem if lv >= nivel_min]
            linhas = []
            for cid, lv in tem:
                disp = s.availability(cid, meses)
                linhas.append((lv, min(disp.values()), sum(disp.values()) / len(disp), cid, disp))
            linhas.sort(key=lambda x: (-x[0], -x[2]) if not quer_disp else (-x[1], -x[0]))
            cont = Counter(lv for _, lv in tem)
            livres = sum(1 for l in linhas if l[1] >= 50)
            filtro = {3: " no nível avançado", 2: " no nível intermediário ou acima"}.get(nivel_min, "")
            txt = (f"{nome}: {len(tem)} colaboradores ativos têm a skill{filtro} ({cont.get(3, 0)} avançados, {cont.get(2, 0)} intermediários, "
                   f"{cont.get(1, 0)} básicos); {livres} têm pelo menos 50% livre em todos os meses de {rot}. Principais: "
                   + "; ".join(f"{pc(cid)} ({s.colabs[cid]['cargo']}, {s.colabs[cid]['senioridade']}) — {NIVEL_NOME[lv].lower()} — livre "
                               + ", ".join(f"{idx_label(m)} {v}%" for m, v in disp.items())
                               for lv, _, _, cid, disp in linhas[:10]) + ".")
            dem = [d["nome"] for d in s.demandas.values() if d["ativa"] and d["skills"] & ids]
            if dem:
                txt += f" Demandas ativas que pedem {nome}: {', '.join(dem[:8])}."
            tal = sorted(((tid, lv) for tid, sk in s.tskills.items() for i, lv in sk.items() if i in ids and s.talentos[tid]["ativo"]),
                         key=lambda x: -x[1])[:5]
            if tal:
                txt += " No InHire (sintético): " + ", ".join(f"{pt(tid)} ({NIVEL_NOME[lv].lower()}, {s.talentos[tid]['disponibilidade']}% disp.)" for tid, lv in tal) + "."
            out.append({"fonte": "SGD · consulta ao vivo", "secao": f"Quem tem {nome}", "texto": txt})
        if quer_disp and not skills:
            linhas = []
            for m in meses:
                d = [s.availability(cid, [m])[m] for cid in ativos]
                linhas.append(f"{idx_label(m)}: {sum(1 for v in d if v >= 100)} pessoas 100% livres, "
                              f"{sum(1 for v in d if v <= 0)} totalmente alocadas, {round(sum(max(v, 0) for v in d) / 100, 1)} FTE livres")
            livres = [cid for cid in ativos if all(v >= 100 for v in s.availability(cid, meses).values())]
            top = []
            for cid in livres[:12]:
                av = [s.skills[k]["nome"] for k, lv in s.cskills.get(cid, {}).items() if lv == 3][:4]
                top.append(f"{pc(cid)} ({s.colabs[cid]['cargo']}, {s.colabs[cid]['senioridade']}; avançado em {', '.join(av) or '—'})")
            out.append({"fonte": "SGD · consulta ao vivo", "secao": f"Capacidade livre ({rot})",
                        "texto": "; ".join(linhas) + f". {len(livres)} pessoas estão 100% livres em todos esses meses, por exemplo: "
                                 + "; ".join(top) + "."})
        if re.search(r"contrato|vencid|vence|renov|cliente|vigenc", f):
            ref = s.ref_idx
            lins = []
            for k in sorted(s.contratos.values(), key=lambda k: k["termino"] or ""):
                pessoas = {a["colab"] for a in s.aloc.values() if a["ativa"] and s.demandas[a["demanda"]]["contrato_id"] == k["id"]
                           and s.plan.get(a["id"], {}).get(ref, 0) > 0}
                lins.append(f"{k['nome']} — {k['situacao']}, termina em {k['termino']}, {len(pessoas)} pessoas alocadas em {idx_label(ref)}")
            out.append({"fonte": "SGD · consulta ao vivo", "secao": "Contratos", "texto": "; ".join(lins) + "."})
        for dn in re.findall(r"demanda\s+(\d{1,4})", f)[:2]:
            d = next((x for x in s.demandas.values() if x["nome"].lower() == f"demanda {dn}"), None)
            if d:
                eq = [(a["colab"], s.plan.get(a["id"], {}).get(s.ref_idx, 0)) for a in s.aloc.values() if a["demanda"] == d["id"] and a["ativa"]]
                k = s.contratos.get(d["contrato_id"], {})
                out.append({"fonte": "SGD · consulta ao vivo", "secao": d["nome"],
                            "texto": f"{d['nome']}: {d['tipo_servico']}, {d['metodologia']}, {d['andamento']}, contrato {k.get('nome')} ({k.get('situacao')}), "
                                     f"{d['inicio']} a {d['termino']}. Skills: {', '.join(s.skills[x]['nome'] for x in d['skills'] if x in s.skills) or 'não cadastradas'}. "
                                     f"Equipe ativa: " + (", ".join(f"{pc(c)} ({p}% em {idx_label(s.ref_idx)})" for c, p in eq) or "ninguém") + "."})
        for cid in self._pessoas_citadas(q):
            ficha = next((c for c in self.chunks if c.get("pessoa") == ("interno", cid)), None)
            if ficha:
                out.append({**ficha, "fonte": "SGD · consulta ao vivo"})
        if re.search(r"quant[oa]s|total|distribui|perfil da equipe|senioridade", f) and not skills:
            out.append(_visao_geral(s))
        return out[:5]

    def projetos(self) -> list[dict]:
        """Projetos e alocações registrados no app (sempre atualizados)."""
        out = []
        try:
            rows = store.q("SELECT b.id, b.nome, b.status, b.params_json, b.criado_em, u.nome AS autor FROM buscas b "
                           "LEFT JOIN usuarios u ON u.id=b.usuario_id ORDER BY b.criado_em DESC LIMIT 60")
        except Exception:  # noqa: BLE001
            return out
        st = {"aguardando": "aguardando decisão", "confirmada": "alocação confirmada", "rascunho": "rascunho"}
        for b in rows:
            p = json.loads(b["params_json"])
            ds = store.q("SELECT origem, candidato_id, percentual FROM decisoes WHERE busca_id=?", (b["id"],))
            equipe = ", ".join(f"{pc(d['candidato_id']) if d['origem'] == 'interno' else pt(d['candidato_id'])} ({d['percentual']}%)" for d in ds)
            out.append({"fonte": "VINT Match · projeto", "secao": b["nome"],
                        "texto": f"Projeto {b['nome']}: {st.get(b['status'], b['status'])}, criado em {b['criado_em'][:10]} por {b['autor'] or '—'}. "
                                 f"Skills: {', '.join(x['nome'] for x in p.get('skills', [])) or '—'}. Duração {p.get('duracao')}, início {p.get('inicio')}, "
                                 f"dedicação mínima {p.get('disponibilidade_min')}%. Alocados: {equipe or 'ninguém ainda'}. "
                                 f"Descrição: {(p.get('descricao') or '')[:300]}"})
        return out

    # ------------------------------------------------------------ resposta
    def _nomes(self, txt: str) -> str:
        txt = re.sub(r"\bColaborador (\d{1,4})\b",
                     lambda m: self.s.colabs[int(m.group(1))]["nome"] if int(m.group(1)) in self.s.colabs else m.group(0), txt)
        return re.sub(r"\bTalento (\d{1,4})\b",
                      lambda m: self.s.talentos[int(m.group(1))]["nome"] + " (InHire)" if int(m.group(1)) in self.s.talentos else m.group(0), txt)

    def contexto(self, pergunta: str) -> list[dict]:
        vivo = self.consulta_ao_vivo(pergunta)
        proj = self.projetos()
        f = _fold(pergunta)
        if proj:
            idx = TfIdf([f"{c['secao']} {c['texto']}" for c in proj])
            quer_proj = bool(re.search(r"projeto|busca|alocad|selecion|decis|aguardando|confirmad", f))
            tops = [proj[i] for i, sc in idx.top(pergunta, 3) if sc > (0.08 if quer_proj else 0.2)] or (proj[:3] if quer_proj else [])
        else:
            tops = []
        vistos = {(c["fonte"], c["secao"]) for c in vivo + tops}
        docs = [c for c in self.search(pergunta, 8) if (c["fonte"], c["secao"]) not in vistos]
        return (vivo + tops + docs)[:8]

    def answer(self, pergunta: str) -> dict:
        ctx = self.contexto(pergunta)
        fontes = [{k: v for k, v in {**c, "texto": self._nomes(c["texto"])}.items() if k != "pessoa"} for c in ctx]
        if not ctx:
            return {"resposta": "Não encontrei nada na base de conhecimento sobre isso.", "fontes": [], "ia": False}
        if not llm.available():
            return {"resposta": "Encontrei estas informações no banco e nos documentos:",
                    "fontes": fontes, "ia": False}
        contexto = "\n\n".join(f"[{i}] ({c['fonte']} › {c['secao']})\n{c['texto'][:1500]}" for i, c in enumerate(ctx, 1))
        try:
            resp = llm.text(
                "Você é o assistente do VINT Match (alocação de talentos da VINT GLOBAL). Responda em português, de forma "
                "objetiva, usando SOMENTE o contexto: consultas ao vivo do banco SGD, projetos do app e documentos. Quando citar "
                "pessoas, use o identificador exatamente como aparece (ex.: Colaborador 129, Talento 029). Use listas curtas "
                "quando listar pessoas. Cite as fontes como [n]. Se o contexto não bastar, diga o que falta.",
                f"CONTEXTO:\n{contexto}\n\nPERGUNTA: {pergunta}", 1200, prazo=30)
            return {"resposta": self._nomes(resp), "fontes": fontes, "ia": True,
                    "modelo": f'{llm.NOMES.get(llm.ULTIMO["provedor"], "")} {llm.ULTIMO["modelo"]}'.strip()}
        except Exception as e:  # noqa: BLE001
            log.warning("RAG sem IA: %s", llm._limpa(str(e))[:300])
            return {"resposta": "Encontrei estas informações no banco e nos documentos:",
                    "fontes": fontes, "ia": False}
