"""Teste de aceite: o cenário do slide do hackathon, rodado no SGD real (snapshot, somente leitura).

José precisa de 1 desenvolvedor Sênior com Node.js e AWS e 50% de disponibilidade mensal, por 3 meses.
"""
import time

from app import buscas, sgd

PEDIDO = {"nome": "Projeto estratégico", "descricao": "Projeto estratégico com prazo apertado: 1 desenvolvedor sênior "
          "Node.js e AWS com 50% de disponibilidade mensal.",
          "skills": [{"nome": "Node.js", "obrigatoria": True, "nivel": "Avançado"},
                     {"nome": "AWS", "obrigatoria": True, "nivel": "Avançado"}],
          "duracao": "3 meses", "inicio": "2026-11-19", "disponibilidade_min": 50, "senioridades": ["Sênior"]}


def test_jose_encontra_quem_atende_e_esta_livre():
    _, res = buscas.preparar(sgd.get(), PEDIDO)
    assert [r["nome"] for r in res["requisitos"]] == ["Node.js", "AWS (Amazon Web Services)"]
    assert len(res["periodo"]["meses"]) == 3
    top = res["ranking"][0]
    assert top["senioridade"] == "Sênior" and top["disponivel"], "1º lugar deve estar livre no período"
    assert all(s["ok"] for s in top["skills_match"]), "1º lugar deve ter Node.js e AWS no nível pedido"
    assert all(m["disp"] >= 50 for m in top["disp_meses"])
    assert top["justificativa"]


def test_jose_ve_alternativas_internas_e_externas():
    _, res = buscas.preparar(sgd.get(), PEDIDO)
    assert any(c["remanejamento"] for c in res["ranking"]), "deve mostrar quem pode ser remanejado"
    assert res["quase_la"], "deve mostrar quem está perto do ideal (PDI)"
    assert res["externos"], "deve mostrar talentos do banco externo no mesmo fluxo"


def test_desempenho_do_cruzamento_das_bases():
    """Cruzar 279 colaboradores e 300 talentos: mediana abaixo de 1 s (meta do produto: decidir em menos de 5 min)."""
    s = sgd.get()
    tempos = []
    for _ in range(20):
        t = time.perf_counter()
        buscas.preparar(s, PEDIDO)
        tempos.append(time.perf_counter() - t)
    tempos.sort()
    print(f"\ncruzamento SGD + iHiring: mediana {tempos[10]*1000:.0f} ms, máx {tempos[-1]*1000:.0f} ms "
          f"({len(s.colabs)} colaboradores, {len(s.talentos)} talentos)")
    assert tempos[10] < 1.0 and tempos[-1] < 5.0
