"""Modelo em memória do SGD + base InHire (talentos). Somente leitura."""
from __future__ import annotations
import re
from collections import defaultdict
from . import config, db
from .textutil import fold

NIVEL = {318: 1, 320: 2, 321: 3}               # ids de dominios NIVEL_CONHECIMENTO
NIVEL_NOME = {1: "Básico", 2: "Intermediário", 3: "Avançado"}
NIVEL_POR_NOME = {"basico": 1, "intermediario": 2, "avancado": 3}

# Grupos de equivalência (catálogo tem quase-duplicatas) e apelidos comuns em briefings.
EQUIV = [
    {"postgresql", "postgre", "postgres"},
    {"laravel (php)", "laravel"},
    {"vue.js", "vue", "vuejs"},
    {"node.js", "node", "nodejs"},
    {"javascript", "js"},
    {"typescript", "ts"},
    {"react", "react.js", "reactjs"},
    {"kubernetes", "k8s"},
    {"aws (amazon web services)", "aws", "amazon web services"},
    {"gcp (google cloud platform)", "gcp", "google cloud"},
    {"ms sql server", "sql server", "sqlserver"},
    {"spring boot (java)", "spring boot", "spring"},
    {"django (python)", "django"},
    {"express (node.js)", "express"},
    {"jwt (json web token)", "jwt"},
    {"ux/ui", "ux", "ui", "ux/ui design"},
    {"ci/cd", "cicd"},
    {"powerbi", "power bi"},
]


def mkey(name: str) -> str:
    return re.sub(r"\s+", " ", fold(name).strip())


def month_idx(ano: int, mes: int) -> int:
    return ano * 12 + (mes - 1)


def idx_label(i: int) -> str:
    return f"{config.MESES[i % 12]}/{str(i // 12)[2:]}"


class SGD:
    def __init__(self):
        raw, self.source = db.load_all()
        self.dom = {d["id"]: d for d in raw["dominios"]}
        self.ref_idx = month_idx(*config.reference_month())

        # --- skills e sinônimos
        self.skills = {s["id"]: {"id": s["id"], "nome": s["nome_skill"], "area": self.dv(s["id_area_tecnologia"])}
                       for s in raw["skills"] if s["status"] and not s["deletado"]}
        self.name_to_ids: dict[str, set[int]] = defaultdict(set)
        for s in self.skills.values():
            self.name_to_ids[mkey(s["nome"])].add(s["id"])
        for grp in EQUIV:
            ids = set().union(*(self.name_to_ids.get(n, set()) for n in grp))
            if ids:
                for n in grp:
                    self.name_to_ids[n] = set(ids)
        self.catalog = sorted({s["nome"] for s in self.skills.values()}, key=str.lower)

        # --- colaboradores
        self.colabs = {}
        for c in raw["colaboradores"]:
            sen = self.dom.get(c["id_senioridade"])
            self.colabs[c["id"]] = {
                "id": c["id"], "nome": c["nome_abreviado"],
                "ativo": bool(c["status"] and not c["deletado"]),
                "cargo": self.dv(c["id_cargo"]),
                "senioridade": sen["valor_dominio"] if sen and sen["tipo_dominio"] == "SENIORIDADE" else "Não informada",
                "vinculo": self.dv(c["id_vinculo"]), "modalidade": self.dv(c["id_modalidade"]),
                "admissao": c["data_admissao"],
            }
        self.cskills: dict[int, dict[int, int]] = defaultdict(dict)
        for r in raw["colaborador_skills"]:
            if r["status"] and not r["deletado"] and r["id_skill"] in self.skills:
                lv = NIVEL.get(r["id_nivel_conhecimento"], 1)
                self.cskills[r["id_colaborador"]][r["id_skill"]] = max(lv, self.cskills[r["id_colaborador"]].get(r["id_skill"], 0))

        # --- contratos e demandas
        self.contratos = {k["id"]: {"id": k["id"], "nome": k["nome_contrato"], "situacao": self.dv(k["id_situacao"]),
                                    "inicio": k["data_inicio"], "termino": k["data_termino"]} for k in raw["contratos"]}
        self.dskills: dict[int, set[int]] = defaultdict(set)
        for r in raw["demanda_skills"]:
            if r["status"] and not r["deletado"]:
                self.dskills[r["id_demanda"]].add(r["id_skill"])
        self.demandas = {}
        for d in raw["demandas"]:
            ini, fim = d["dt_inicio_demanda"], d["dt_termino_demanda_prevista"]
            self.demandas[d["id"]] = {
                "id": d["id"], "nome": d["nome_demanda"], "ativa": bool(d["status"] and not d["deletado"]),
                "gerente_id": d["id_gerente"], "contrato_id": d["id_contrato"],
                "tipo_servico": self.dv(d["id_tipo_servico"]), "metodologia": self.dv(d["id_metodologia"]),
                "andamento": self.dv(d["id_andamento_demanda"]), "inicio": ini, "termino": fim,
                "datas_confiaveis": ini != fim, "skills": self.dskills.get(d["id"], set()),
            }

        # --- alocações e planejamentos
        self.aloc = {a["id"]: {"id": a["id"], "colab": a["id_colaborador"], "demanda": a["id_demanda"],
                               "ativa": bool(a["status"] and not a["deletado"])} for a in raw["alocacoes"]}
        self.plan: dict[int, dict[int, int]] = defaultdict(dict)
        for p in raw["planejamentos"]:
            if p["status"] and not p["deletado"] and p["mes"] in config.MESES:
                self.plan[p["id_alocacao"]][month_idx(p["ano"], config.MESES.index(p["mes"]) + 1)] = p["porcentagem"]
        self.plan_horizon = max((m for pl in self.plan.values() for m in pl), default=self.ref_idx)

        self.load: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))  # carga ativa por mês
        self.allocs_by_colab: dict[int, list[int]] = defaultdict(list)
        for a in self.aloc.values():
            self.allocs_by_colab[a["colab"]].append(a["id"])
            if a["ativa"]:
                for m, pct in self.plan.get(a["id"], {}).items():
                    self.load[a["colab"]][m] += pct

        # --- talentos externos (InHire) — dados sintéticos de teste
        self.talentos = {t["id"]: {"id": t["id"], "nome": t["nome_abreviado"], "ativo": bool(t["status"]),
                                   "cargo": self.dv(t["id_cargo"]), "senioridade": self.dv(t["id_senioridade"]),
                                   "modalidade": self.dv(t["id_modalidade"]),
                                   "disponibilidade": t["disponibilidade_informada_percentual"] or 0}
                         for t in raw["talentos"]}
        self.tskills: dict[int, dict[int, int]] = defaultdict(dict)
        for r in raw["talento_skills"]:
            if r["id_skill"] in self.skills:
                self.tskills[r["id_talento"]][r["id_skill"]] = NIVEL.get(r["id_nivel_conhecimento"], 1)

        self.options = {
            "senioridades": [d["valor_dominio"] for d in sorted(self.dom.values(), key=lambda x: x["id"])
                             if d["tipo_dominio"] == "SENIORIDADE" and not d["deletado"]],
            "tipos_servico": sorted({d["tipo_servico"] for d in self.demandas.values() if d["tipo_servico"]}),
            "metodologias": sorted({d["metodologia"] for d in self.demandas.values() if d["metodologia"]}),
        }

    # helpers ---------------------------------------------------------------
    def dv(self, dom_id):
        d = self.dom.get(dom_id)
        return d["valor_dominio"] if d else None

    def resolve_skill(self, name: str) -> set[int]:
        return set(self.name_to_ids.get(mkey(name), set()))

    def canonical(self, name: str) -> str | None:
        ids = self.resolve_skill(name)
        if not ids:
            return None
        nomes = sorted({self.skills[i]["nome"] for i in ids}, key=len, reverse=True)
        return nomes[0]

    def availability(self, colab_id: int, months: list[int]) -> dict[int, int]:
        ld = self.load.get(colab_id, {})
        return {m: 100 - ld.get(m, 0) for m in months}

    def history(self, colab_id: int) -> list[dict]:
        """Demandas em que o colaborador atuou (planejamento > 0), incluindo alocações encerradas."""
        out = []
        for aid in self.allocs_by_colab.get(colab_id, []):
            a = self.aloc[aid]
            pl = {m: p for m, p in self.plan.get(aid, {}).items() if p > 0}
            if not pl:
                continue
            past = {m: p for m, p in pl.items() if m <= self.ref_idx}
            out.append({"aloc_id": aid, "demanda_id": a["demanda"], "ativa": a["ativa"],
                        "meses": len(past), "fte_meses": round(sum(past.values()) / 100, 1),
                        "de": idx_label(min(pl)), "ate": idx_label(max(pl))})
        return out

    def profile_text(self, colab_id: int) -> str:
        c = self.colabs[colab_id]
        parts = [c["cargo"] or "", c["senioridade"]]
        for sid, lv in self.cskills.get(colab_id, {}).items():
            parts.append(self.skills[sid]["nome"] + (" avançado" if lv == 3 else ""))
        for h in self.history(colab_id):
            d = self.demandas[h["demanda_id"]]
            parts += [d["tipo_servico"] or "", d["metodologia"] or ""]
            parts += [self.skills[s]["nome"] for s in d["skills"] if s in self.skills]
        return " ".join(parts)


_SGD: SGD | None = None


def get() -> SGD:
    global _SGD
    if _SGD is None:
        _SGD = SGD()
    return _SGD
