"""Matching híbrido: filtro determinístico (skills + disponibilidade) + scoring + histórico + semântico.

Score (0–100) = 40% skills (ponderado por nível e obrigatoriedade)
              + 25% disponibilidade no período
              + 20% histórico em projetos parecidos
              + 15% aderência semântica (TF-IDF do texto livre; substituído pelo julgamento da IA se ativa)
              − penalidade de "perfil amplo" (catálogo quase todo declarado, dado pouco confiável)
"""
from __future__ import annotations
import time
from .sgd import SGD, NIVEL_NOME, NIVEL_POR_NOME, idx_label, month_idx
from .textutil import TfIdf, fold

W = {"skills": 0.40, "disp": 0.25, "hist": 0.20, "sem": 0.15}
PERFIL_AMPLO = 100          # nº de skills declaradas a partir do qual o perfil é considerado inflado
FACILIDADE = {"Concluída": "Fácil", "Não Iniciada": "Fácil", "Iniciada": "Média",
              "Em Desenvolvimento": "Média", "Em Atenção": "Difícil", "Crítica": "Difícil"}
TEMPO_PDI = {(0, 1): "2–4 semanas", (1, 2): "4–6 semanas", (2, 3): "8–12 semanas",
             (0, 2): "6–10 semanas", (0, 3): "3–4 meses", (1, 3): "3–4 meses"}


def credit(atual: int, pedido: int) -> float:
    if atual <= 0:
        return 0.0
    if atual >= pedido:
        return 1.0
    return 0.6 if pedido - atual == 1 else 0.35


def parse_req(s: SGD, req: dict) -> tuple[list[dict], list[str]]:
    reqs, avisos, seen = [], [], set()
    for it in req.get("skills", []):
        nome = (it.get("nome") or "").strip()
        if not nome:
            continue
        ids = s.resolve_skill(nome)
        canon = s.canonical(nome) or nome
        if fold(canon) in seen:
            continue
        seen.add(fold(canon))
        nivel = nivel_num(it.get("nivel"))
        reqs.append({"nome": canon, "ids": ids, "obrigatoria": bool(it.get("obrigatoria", True)), "nivel": nivel})
        if not ids:
            avisos.append(f"Skill '{nome}' não existe no catálogo do SGD — ninguém pode atendê-la internamente; "
                          "considere talentos externos ou PDI.")
    return reqs, avisos


def nivel_num(v) -> int:
    """Nível digitado livremente → 1 básico, 2 intermediário, 3 avançado."""
    f = fold(str(v or "")).strip()
    if f in NIVEL_POR_NOME:
        return NIVEL_POR_NOME[f]
    if f[:1].isdigit():
        return max(1, min(3, int(f[0])))
    if f.startswith(("ava", "exp", "esp", "sen", "alt", "adv")):
        return 3
    if f.startswith(("int", "med", "ple", "mid")):
        return 2
    return 1


def period(s: SGD, req: dict) -> list[int]:
    ini = req.get("inicio")
    start = month_idx(*map(int, ini.split("-"))) if ini else s.ref_idx
    n = max(1, min(int(req.get("duracao_meses") or 3), 24))
    return list(range(start, start + n))


def skill_eval(cs: dict[int, int], reqs: list[dict], hist_skills: set[int]) -> tuple[float, list, list, list]:
    num = den = 0.0
    det, faltando, abaixo = [], [], []
    for r in reqs:
        atual = max((cs.get(i, 0) for i in r["ids"]), default=0)
        w = 2.0 if r["obrigatoria"] else 1.0
        num += w * credit(atual, r["nivel"])
        den += w
        item = {"nome": r["nome"], "obrigatoria": r["obrigatoria"], "nivel_pedido": NIVEL_NOME[r["nivel"]],
                "nivel_atual": NIVEL_NOME.get(atual, "—"), "ok": atual >= r["nivel"],
                "evidencia_projeto": bool(r["ids"] & hist_skills)}
        det.append(item)
        if atual == 0:
            faltando.append((r, atual))
        elif atual < r["nivel"]:
            abaixo.append((r, atual))
    return (num / den if den else 0.0), det, faltando, abaixo


def history_eval(s: SGD, colab_id: int, reqs: list[dict], req: dict) -> tuple[float, list, set]:
    best, similares, skills_vistas = 0.0, [], set()
    ids_req = [r["ids"] for r in reqs if r["ids"]]
    for h in s.history(colab_id):
        d = s.demandas[h["demanda_id"]]
        skills_vistas |= d["skills"]
        comuns = [r["nome"] for r in reqs if r["ids"] & d["skills"]]
        sim = 0.7 * (len(comuns) / len(ids_req)) if ids_req and d["skills"] else 0.0
        if req.get("tipo_servico") and fold(d["tipo_servico"] or "") == fold(req["tipo_servico"]).strip():
            sim += 0.2
        if req.get("metodologia") and fold(d["metodologia"] or "") == fold(req["metodologia"]).strip():
            sim += 0.1
        sim = min(sim, 1.0)
        best = max(best, sim)
        if sim >= 0.3:
            similares.append({"demanda": d["nome"], "tipo_servico": d["tipo_servico"], "metodologia": d["metodologia"],
                              "andamento": d["andamento"], "skills_em_comum": comuns, "periodo": f'{h["de"]}–{h["ate"]}',
                              "fte_meses": h["fte_meses"], "em_andamento": h["ativa"], "similaridade": round(sim * 100)})
    similares.sort(key=lambda x: -x["similaridade"])
    return best, similares[:3], skills_vistas


def remanejamento(s: SGD, colab_id: int, months: list[int], need: int) -> dict:
    disp = s.availability(colab_id, months)
    falta = [{"mes": idx_label(m), "liberar_pct": max(0, need - d)} for m, d in disp.items() if d < need]
    alocs = []
    for aid in s.allocs_by_colab.get(colab_id, []):
        a = s.aloc[aid]
        if not a["ativa"]:
            continue
        meses = [{"mes": idx_label(m), "pct": p} for m, p in sorted(s.plan.get(aid, {}).items()) if m in months and p > 0]
        if not meses:
            continue
        d = s.demandas[a["demanda"]]
        k = s.contratos.get(d["contrato_id"], {})
        g = s.colabs.get(d["gerente_id"], {})
        fac = FACILIDADE.get(d["andamento"], "Média")
        if k.get("situacao") in ("Vencido", "Encerrado", "Cancelado"):
            fac = "Fácil"
        if d["andamento"] == "Concluída":
            sug = "Demanda já concluída — a alocação provavelmente pode ser encerrada."
        elif d["andamento"] == "Não Iniciada":
            sug = "Demanda ainda não iniciada — dá para adiar a entrada ou substituir o profissional."
        elif k.get("situacao") in ("Vencido", "Encerrado", "Cancelado"):
            sug = f'Contrato {k.get("situacao", "").lower()} — confirmar se a alocação ainda faz sentido.'
        elif fac == "Difícil":
            sug = "Demanda em situação sensível — remanejar só com substituto definido."
        else:
            sug = "Negociar redução parcial de % com o gerente da demanda."
        alocs.append({"demanda": d["nome"], "andamento": d["andamento"], "tipo_servico": d["tipo_servico"],
                      "contrato": k.get("nome"), "situacao_contrato": k.get("situacao"),
                      "gerente": g.get("nome", "—"), "meses": meses, "facilidade": fac, "sugestao": sug})
    ordem = {"Fácil": 0, "Média": 1, "Difícil": 2}
    alocs.sort(key=lambda x: ordem[x["facilidade"]])
    return {"necessario": bool(falta), "liberar_por_mes": falta, "alocacoes": alocs,
            "viabilidade": alocs[0]["facilidade"] if alocs else "—"}


def pdi(s: SGD, colab_id: int, gaps: list[tuple[dict, int]], months: list[int]) -> list[dict]:
    out = []
    cs = s.cskills.get(colab_id, {})
    for r, atual in gaps[:4]:
        if not r["ids"]:
            continue
        area = s.skills[next(iter(r["ids"]))]["area"]
        base = sorted(((sid, lv) for sid, lv in cs.items() if s.skills[sid]["area"] == area and sid not in r["ids"]),
                      key=lambda x: -x[1])[:3]
        mentores = []
        for cid, sk in s.cskills.items():
            if cid == colab_id or not s.colabs.get(cid, {}).get("ativo"):
                continue
            if max((sk.get(i, 0) for i in r["ids"]), default=0) == 3:
                disp = s.availability(cid, months)
                mentores.append((sum(disp.values()) / len(disp), cid))
        mentores.sort(reverse=True)
        pratica = [d["nome"] for d in s.demandas.values()
                   if d["ativa"] and d["andamento"] in ("Em Desenvolvimento", "Iniciada") and d["skills"] & r["ids"]][:2]
        out.append({
            "skill": r["nome"], "area": area, "de": NIVEL_NOME.get(atual, "Nenhum"), "para": NIVEL_NOME[r["nivel"]],
            "prazo_estimado": TEMPO_PDI.get((atual, r["nivel"]), "4–8 semanas"),
            "base_existente": [f'{s.skills[sid]["nome"]} ({NIVEL_NOME[lv]})' for sid, lv in base],
            "mentor_sugerido": s.colabs[mentores[0][1]]["nome"] if mentores else None,
            "pratica_em": pratica,
        })
    return out


def justificativa(c: dict, reqs: list[dict], meses_lbl: str) -> str:
    ok = sum(1 for x in c["skills_match"] if x["ok"])
    tem = sum(1 for x in c["skills_match"] if x["nivel_atual"] != "—")
    partes = [f"Atende {ok}/{len(reqs)} skills no nível pedido" + (f" (possui {tem}/{len(reqs)})" if tem > ok else "")]
    partes.append(f"disponibilidade média de {c['disp_media']}% em {meses_lbl}" if c["disponivel"]
                  else f"hoje com só {c['disp_min']}% livre no pior mês — exige remanejamento")
    if c["historico_similar"]:
        h = c["historico_similar"][0]
        partes.append(f"já atuou em {h['demanda']} ({h['tipo_servico']}, {h['similaridade']}% similar)")
    if c["perfil_amplo"]:
        partes.append("perfil declara skills demais — validar com o líder")
    return "; ".join(partes) + "."


def run(s: SGD, req: dict) -> dict:
    t0 = time.time()
    reqs, avisos = parse_req(s, req)
    months = period(s, req)
    need = max(0, min(int(req.get("disponibilidade_min") or 0), 100))
    sens = set(req.get("senioridades") or [])
    meses_lbl = f"{idx_label(months[0])}–{idx_label(months[-1])}"
    if months[-1] > s.plan_horizon:
        avisos.append(f"O planejamento no SGD vai só até {idx_label(s.plan_horizon)}; meses seguintes aparecem como 100% livres.")
    if not reqs:
        avisos.append("Nenhuma skill informada — o ranking usa apenas disponibilidade, histórico e texto livre.")

    # skill obrigatória que ninguém ativo possui não pode bloquear o ranking: vira lacuna (PDI / externos)
    for r in reqs:
        n = sum(1 for cid, c in s.colabs.items() if c["ativo"] and r["ids"] & s.cskills.get(cid, {}).keys())
        if r["ids"] and n == 0:
            avisos.append(f"Nenhum colaborador ativo tem '{r['nome']}' — tratada como desejável (lacuna para PDI "
                          "ou contratação via InHire).")
            if r["obrigatoria"]:
                r["obrigatoria"] = False
                r["era_obrigatoria"] = True
        elif not r["ids"] and r["obrigatoria"]:
            r["obrigatoria"] = False
            r["era_obrigatoria"] = True

    query_text = " ".join([req.get("texto") or "", " ".join(r["nome"] for r in reqs),
                           req.get("tipo_servico") or "", req.get("metodologia") or ""])
    ativos = [cid for cid, c in s.colabs.items() if c["ativo"] and (not sens or c["senioridade"] in sens)]
    tf = TfIdf([s.profile_text(cid) for cid in ativos]) if (req.get("texto") or "").strip() else None
    sem_raw = dict(zip(ativos, tf.query(query_text))) if tf else {}
    sem_max = max(sem_raw.values(), default=0) or 1.0

    # pessoas já alocadas nesta busca entram sempre (mesmo se o novo filtro as excluiria), para a alocação não "sumir"
    fix_int = {int(x) for x in (req.get("fixar") or {}).get("interno", [])}
    fix_ext = {int(x) for x in (req.get("fixar") or {}).get("ihiring", [])}
    ativos_set = set(ativos)
    avaliar = ativos + [cid for cid in fix_int if cid not in ativos_set and cid in s.colabs]
    aptos, quase = [], []
    for cid in avaliar:
        c = s.colabs[cid]
        cs = s.cskills.get(cid, {})
        hist_score, similares, hist_skills = history_eval(s, cid, reqs, req)
        sk_score, det, faltando, abaixo = skill_eval(cs, reqs, hist_skills)
        obrig_falt = [r for r, _ in faltando if r["obrigatoria"]]
        if reqs and sk_score == 0 and cid not in fix_int:
            continue
        disp = s.availability(cid, months)
        disp_ok = [min(max(d, 0) / need, 1.0) if need else 1.0 for d in disp.values()]
        av_score = sum(disp_ok) / len(disp_ok)
        sem = (sem_raw.get(cid, 0) / sem_max) if tf else None
        w = dict(W)
        if sem is None:
            w["sem"] = 0.0
        tot_w = sum(w.values())
        fit = (w["skills"] * sk_score + w["hist"] * hist_score + w["sem"] * (sem or 0)) / (tot_w - w["disp"])
        score = (w["skills"] * sk_score + w["disp"] * av_score + w["hist"] * hist_score + w["sem"] * (sem or 0)) / tot_w
        amplo = len(cs) >= PERFIL_AMPLO
        score = score * 100 - (8 if amplo else 0)
        cand = {
            "id": cid, "nome": c["nome"], "cargo": c["cargo"], "senioridade": c["senioridade"],
            "modalidade": c["modalidade"], "vinculo": c["vinculo"],
            "score": round(max(score, 0), 1), "fit": round(fit * 100, 1),
            "componentes": {"skills": round(sk_score * 100), "disponibilidade": round(av_score * 100),
                            "historico": round(hist_score * 100), "semantico": None if sem is None else round(sem * 100)},
            "disponivel": all(d >= need for d in disp.values()),
            "disp_meses": [{"mes": idx_label(m), "disp": d} for m, d in disp.items()],
            "disp_media": round(sum(disp.values()) / len(disp)), "disp_min": min(disp.values()),
            "skills_match": det, "n_skills_declaradas": len(cs), "perfil_amplo": amplo,
            "historico_similar": similares,
            "faltando_obrigatorias": [r["nome"] for r in obrig_falt],
            "_gaps": faltando + abaixo,
        }
        (quase if obrig_falt else aptos).append(cand)

    aptos.sort(key=lambda x: -x["score"])
    best_fit_disp = max((c["fit"] for c in aptos if c["disponivel"]), default=0)
    top = aptos[:10]
    # o mais viável alocado: entra no ranking mesmo sem disponibilidade
    extra = [c for c in aptos[10:] if not c["disponivel"] and c["fit"] >= best_fit_disp][:3]
    ranking = sorted(top + extra, key=lambda x: -x["score"])
    quase.sort(key=lambda x: (len(x["faltando_obrigatorias"]), -x["score"]))
    n_quase_total = sum(1 for c in quase if len(c["faltando_obrigatorias"]) <= 2)
    quase_top = [c for c in quase if len(c["faltando_obrigatorias"]) <= 2][:5]
    vistos = {c["id"] for c in ranking + quase_top}
    fixados = [c for c in aptos + quase if c["id"] in fix_int and c["id"] not in vistos]
    for c in ranking + fixados:
        c["remanejamento"] = remanejamento(s, c["id"], months, need) if not c["disponivel"] else None
        c["mais_viavel_alocado"] = bool(c["remanejamento"] and c["fit"] >= best_fit_disp)
        c["pdi"] = pdi(s, c["id"], c["_gaps"], months)
        c["justificativa"] = justificativa(c, reqs, meses_lbl)
        c["badges"] = (["Disponível"] if c["disponivel"] else ["Remanejamento"]) + \
                      (["Mais viável"] if c["mais_viavel_alocado"] else []) + \
                      (["PDI"] if c["pdi"] else []) + (["Perfil amplo"] if c["perfil_amplo"] else []) + \
                      (["Já fez parecido"] if c["historico_similar"] else [])

    quase = quase_top
    for c in quase:
        c["pdi"] = pdi(s, c["id"], c["_gaps"], months)
        c["remanejamento"] = None
        c["justificativa"] = (f"Falta(m) {', '.join(c['faltando_obrigatorias'])} — candidato a PDI; "
                              f"disponibilidade média {c['disp_media']}% no período.")
        c["badges"] = ["PDI"] + (["Disponível"] if c["disponivel"] else [])
    for c in fixados:
        if c["faltando_obrigatorias"]:
            c["justificativa"] = f"Já alocado(a) nesta busca. Falta(m) {', '.join(c['faltando_obrigatorias'])} pelos critérios atuais."
        c["badges"] = ["Alocado"] + c["badges"]
    for c in ranking + quase + fixados:
        c.pop("_gaps", None)

    todos_ext = externos_rank(s, reqs, need, limite=None) if (req.get("incluir_externos", True) or fix_ext) else []
    externos = todos_ext[:8] if req.get("incluir_externos", True) else []
    ids_ext = {t["id"] for t in externos}
    externos_fixados = [t for t in todos_ext if t["id"] in fix_ext and t["id"] not in ids_ext]
    externos_fixados += [externo_card(s, tid, reqs, need) for tid in fix_ext
                         if tid not in ids_ext and tid not in {t["id"] for t in externos_fixados} and tid in s.talentos]
    for t in externos_fixados:
        t.pop("_sk", None)
    return {
        "periodo": {"meses": [idx_label(m) for m in months], "rotulo": meses_lbl,
                    "referencia": idx_label(s.ref_idx), "horizonte_planejamento": idx_label(s.plan_horizon)},
        "requisitos": [{"nome": r["nome"], "obrigatoria": r["obrigatoria"], "rebaixada": r.get("era_obrigatoria", False), "nivel": NIVEL_NOME[r["nivel"]],
                        "no_catalogo": bool(r["ids"]),
                        "colabs_com_skill": sum(1 for cid in ativos if r["ids"] & s.cskills.get(cid, {}).keys())}
                       for r in reqs],
        "disponibilidade_min": need,
        "resumo": {"avaliados": len(ativos), "aptos": len(aptos), "disponiveis": sum(c["disponivel"] for c in aptos),
                   "remanejamento": sum(1 for c in ranking if c["remanejamento"]), "quase_la": len(quase),
                   "quase_la_total": n_quase_total, "externos_total": len(todos_ext)},
        "ranking": ranking, "quase_la": quase, "externos": externos, "avisos": avisos,
        "fixados": fixados, "externos_fixados": externos_fixados,
        "fonte_dados": s.source, "tempo_ms": round((time.time() - t0) * 1000),
    }


def externo_card(s: SGD, tid: int, reqs: list[dict], need: int) -> dict:
    t = s.talentos[tid]
    sk, det, _, _ = skill_eval(s.tskills.get(tid, {}), reqs, set())
    av = min(t["disponibilidade"] / need, 1.0) if need else 1.0
    return {"id": tid, "nome": t["nome"], "cargo": t["cargo"], "senioridade": t["senioridade"],
            "modalidade": t["modalidade"], "disponibilidade": t["disponibilidade"],
            "score": round((0.7 * sk + 0.3 * av) * 100, 1),
            "skills_atendidas": [x["nome"] for x in det if x["nivel_atual"] != "—"],
            "fonte": "InHire (dados sintéticos de teste)", "_sk": sk}


def externos_rank(s: SGD, reqs: list[dict], need: int, limite: int | None = 8) -> list[dict]:
    out = []
    for tid, t in s.talentos.items():
        if not t["ativo"]:
            continue
        card = externo_card(s, tid, reqs, need)
        if reqs and card["_sk"] == 0:
            continue
        out.append(card)
    for c in out:
        c.pop("_sk", None)
    out.sort(key=lambda x: -x["score"])
    return out[:limite] if limite else out
