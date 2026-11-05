"""Servidor MCP do VINT Match — liga o matchmaking ao chat do Cursor (ou a qualquer cliente MCP).

No Cursor, o modelo do próprio Cursor faz o raciocínio; estas ferramentas entregam os dados do SGD.
Não precisa de chave de IA. Somente leitura. Por padrão os nomes saem pseudonimizados
("Colaborador 129"), porque o conteúdo vai para o modelo usado pelo Cursor. Para ver nomes reais
use a interface web, ou defina MCP_MOSTRAR_NOMES=1 no .env.
"""
from __future__ import annotations
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)  # stdout é do protocolo MCP

from mcp.server.mcpserver import MCPServer  # noqa: E402
from app import matching, rag, sgd  # noqa: E402
from app.sgd import idx_label, month_idx  # noqa: E402

MOSTRAR_NOMES = os.getenv("MCP_MOSTRAR_NOMES", "0") == "1"
server = MCPServer(
    name="vint-match",
    instructions=("Ferramentas de alocação de talentos da VINT GLOBAL sobre o SGD (somente leitura). "
                  "Use listar_skills para achar o nome exato das skills antes de buscar_talentos. "
                  "Responda em português e cite score, disponibilidade por mês e necessidade de remanejamento."),
)
_rag = None


def _nome(cid: int, real: str) -> str:
    return real if MOSTRAR_NOMES else f"Colaborador {cid:03d}"


def _resumo(c: dict) -> dict:
    out = {
        "id": c["id"], "nome": _nome(c["id"], c["nome"]), "cargo": c["cargo"], "senioridade": c["senioridade"],
        "score": c["score"], "selos": c.get("badges", []), "justificativa": c["justificativa"],
        "disponibilidade_por_mes": {m["mes"]: m["disp"] for m in c["disp_meses"]},
        "skills": {s["nome"]: s["nivel_atual"] for s in c["skills_match"]},
        "projetos_parecidos": [f'{h["demanda"]} ({h["tipo_servico"]}, {h["similaridade"]}%)' for h in c["historico_similar"]],
    }
    if c.get("remanejamento"):
        r = c["remanejamento"]
        out["remanejamento"] = {
            "liberar": {x["mes"]: x["liberar_pct"] for x in r["liberar_por_mes"]},
            "ocupado_em": [f'{a["demanda"]} ({a["andamento"]}, contrato {a["contrato"]}) — {a["facilidade"]}: {a["sugestao"]}'
                           for a in r["alocacoes"]],
        }
    if c.get("pdi"):
        out["pdi"] = [f'{p["skill"]}: {p["de"]} → {p["para"]} ({p["prazo_estimado"]})' for p in c["pdi"]]
    return out


@server.tool()
def listar_skills(busca: str = "") -> list[str]:
    """Lista o catálogo de skills do SGD (filtra por trecho do nome, ex.: 'java', 'postgre')."""
    s = sgd.get()
    b = busca.lower().strip()
    return [n for n in s.catalog if b in n.lower()][:60]


@server.tool()
def buscar_talentos(skills_obrigatorias: list[str], skills_desejaveis: list[str] | None = None,
                    nivel_minimo: str = "basico", inicio: str = "", duracao_meses: int = 3,
                    disponibilidade_min: int = 50, senioridades: list[str] | None = None,
                    tipo_servico: str = "", metodologia: str = "", descricao: str = "",
                    max_resultados: int = 5) -> dict:
    """Ranking de colaboradores do SGD para um projeto.
    nivel_minimo: basico | intermediario | avancado (vale para as obrigatórias).
    inicio: AAAA-MM (vazio = mês atual). disponibilidade_min: % livre exigido em cada mês.
    senioridades: ex. ['Pleno','Sênior']. tipo_servico: Desenvolvimento|Sustentação|Outsourcing|Apoio.
    metodologia: Scrum|Kanban|Waterfall|Híbrido. descricao: texto livre do projeto."""
    s = sgd.get()
    req = {"skills": [{"nome": n, "obrigatoria": True, "nivel": nivel_minimo} for n in skills_obrigatorias] +
                     [{"nome": n, "obrigatoria": False, "nivel": "basico"} for n in (skills_desejaveis or [])],
           "inicio": inicio or None, "duracao_meses": duracao_meses, "disponibilidade_min": disponibilidade_min,
           "senioridades": senioridades or [], "tipo_servico": tipo_servico or None,
           "metodologia": metodologia or None, "texto": descricao, "incluir_externos": True}
    r = matching.run(s, req)
    n = max(1, min(max_resultados, 15))
    return {
        "periodo": r["periodo"]["rotulo"], "avisos": r["avisos"], "resumo": r["resumo"],
        "ranking": [_resumo(c) for c in r["ranking"][:n]],
        "mais_viaveis_alocados": [_resumo(c) for c in r["ranking"] if c.get("mais_viavel_alocado")][:3],
        "quase_la_pdi": [_resumo(c) for c in r["quase_la"][:3]],
        "talentos_externos_inhire_SINTETICOS": [
            {"id": t["id"], "cargo": t["cargo"], "senioridade": t["senioridade"], "disponibilidade": t["disponibilidade"],
             "skills": t["skills_atendidas"], "score": t["score"]} for t in r["externos"][:3]],
    }


@server.tool()
def disponibilidade_colaborador(id_colaborador: int, inicio: str = "", meses: int = 3) -> dict:
    """Disponibilidade mensal (%) e alocações atuais de um colaborador do SGD, pelo id."""
    s = sgd.get()
    c = s.colabs.get(id_colaborador)
    if not c:
        return {"erro": "colaborador não encontrado"}
    start = month_idx(*map(int, inicio.split("-"))) if inicio else s.ref_idx
    ms = list(range(start, start + max(1, min(meses, 12))))
    disp = s.availability(id_colaborador, ms)
    atuais = []
    for h in s.history(id_colaborador):
        if h["ativa"]:
            d = s.demandas[h["demanda_id"]]
            atuais.append(f'{d["nome"]} ({d["tipo_servico"]}, {d["andamento"]}) {h["de"]}–{h["ate"]}')
    return {"id": id_colaborador, "nome": _nome(id_colaborador, c["nome"]), "ativo": c["ativo"],
            "cargo": c["cargo"], "senioridade": c["senioridade"],
            "disponibilidade_por_mes": {idx_label(m): v for m, v in disp.items()}, "alocacoes_atuais": atuais}


@server.tool()
def perguntar_base(pergunta: str, k: int = 5) -> list[dict]:
    """Busca semântica (RAG) nas anotações do cliente, documentação do banco e fichas de skills/demandas.
    Devolve trechos com fonte; use-os para responder citando a fonte."""
    global _rag
    if _rag is None:
        _rag = rag.RAG(sgd.get())
    return [{"fonte": f'{c["fonte"]} › {c["secao"]}', "texto": c["texto"]} for c in _rag.search(pergunta, max(1, min(k, 10)))]


if __name__ == "__main__":
    server.run()  # stdio
