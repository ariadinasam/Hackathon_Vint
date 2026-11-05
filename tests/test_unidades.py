"""Testes unitários das regras de negócio (pytest). Não usam rede nem gravam no banco."""
from datetime import date

import pytest

from app import buscas, extract, llm, matching, sgd
from app.textutil import fold

S = sgd.get()
INI = date(2026, 11, 20)


# ---------------------------------------------------------------- datas e duração (US03)
@pytest.mark.parametrize("valor, esperado", [
    ("2026-12-01", date(2026, 12, 1)),           # calendário (ISO)
    ("01/12/2026", date(2026, 12, 1)),           # digitado no padrão brasileiro
])
def test_data_inicio_aceita_datas(valor, esperado):
    assert buscas.data_inicio(valor) == esperado


def test_data_inicio_atalhos_e_texto():
    h = buscas.hoje()
    assert buscas.data_inicio("Imediato") == h
    assert (buscas.data_inicio("Em 30 dias") - h).days == 30
    assert (buscas.data_inicio("em 3 semanas") - h).days == 21
    assert (buscas.data_inicio("qualquer coisa") - h).days == 15     # padrão seguro


@pytest.mark.parametrize("valor, meses", [
    ("3–6 meses", 6), ("4 meses", 4), ("10 semanas", 3), ("1 ano", 12), ("2 a 4 meses", 4),
    ("40 meses", 24),                    # limite máximo
    ("2027-06-30", 8), ("30/06/2027", 8),  # data de término
])
def test_duracao_entendida(valor, meses):
    assert buscas.duracao_meses(valor, INI) == (meses, True)


def test_duracao_invalida_e_sinalizada():
    assert buscas.duracao_meses("xyz", INI) == (6, False)
    assert buscas.duracao_meses("2026-10-01", INI)[1] is False       # término antes do início


def test_fim_previsto():
    assert buscas.fim_previsto(date(2026, 12, 1), 3) == date(2027, 2, 28)
    assert buscas.fim_previsto(date(2027, 1, 31), 1) == date(2027, 2, 27)  # fevereiro curto


# ---------------------------------------------------------------- normalizações (US01, US03, US05)
@pytest.mark.parametrize("texto, nivel", [
    ("Avançado", 3), ("avancado", 3), ("sênior", 3), ("especialista", 3), ("3", 3),
    ("Intermediário", 2), ("pleno", 2), ("Básico", 1), ("", 1), ("qualquer", 1),
])
def test_nivel_digitado(texto, nivel):
    assert matching.nivel_num(texto) == nivel


def test_nome_de_projeto_normalizado_para_duplicidade():
    assert buscas.chave_nome("  Portal de SERVIÇOS! ") == buscas.chave_nome("portal de servicos")


def test_skill_por_apelido():
    assert S.canonical("AWS") == "AWS (Amazon Web Services)"
    assert fold("Ação") == "acao"


# ---------------------------------------------------------------- extração do briefing (US02)
def test_extracao_siglas_e_dedicacao():
    out = extract.extract(S, "Precisamos de JS, TS e C# com UX por 10 semanas, tempo integral.", use_ai=False)
    assert {"JavaScript", "TypeScript", "C#", "UX/UI"} <= {x["nome"] for x in out["skills"]}
    assert out["duracao_meses"] == 3 and out["disponibilidade_min"] == 100


# ---------------------------------------------------------------- ranking (US06–US09, US11)
REQ = {"skills": [{"nome": "Node.js", "nivel": "avancado"}, {"nome": "AWS", "nivel": "avancado"}],
       "duracao_meses": 3, "disponibilidade_min": 50, "senioridades": ["Sênior"]}


@pytest.fixture(scope="module")
def res():
    return matching.run(S, REQ)


def test_filtro_de_senioridade(res):
    assert all(c["senioridade"] == "Sênior" for c in res["ranking"] + res["quase_la"])


def test_proximos_do_ideal_tem_pdi(res):
    """US09: quem não tem 1–2 obrigatórias vai para 'Próximos do ideal' com PDI."""
    assert res["quase_la"]
    for c in res["quase_la"]:
        assert 1 <= len(c["faltando_obrigatorias"]) <= 2 and "PDI" in c["badges"]
        assert c["pdi"] and {"skill", "de", "para"} <= set(c["pdi"][0])


def test_remanejamento_diz_o_que_liberar(res):
    """US08: quem está ocupado traz quanto liberar por mês e a viabilidade."""
    ocupados = [c for c in res["ranking"] if not c["disponivel"]]
    assert ocupados
    for c in ocupados:
        r = c["remanejamento"]
        assert r["liberar_por_mes"] and r["viabilidade"] in {"Fácil", "Média", "Difícil"}
        assert all(0 < m["liberar_pct"] <= 100 for m in r["liberar_por_mes"])


def test_externos_ordenados_e_limitados(res):
    """US11: até 8 talentos externos, do maior para o menor match."""
    ext = res["externos"]
    assert 0 < len(ext) <= 8 and [t["score"] for t in ext] == sorted((t["score"] for t in ext), reverse=True)


def test_mais_dedicacao_exigida_nunca_aumenta_disponiveis():
    base = {**REQ, "senioridades": []}
    n = [matching.run(S, {**base, "disponibilidade_min": d})["resumo"]["disponiveis"] for d in (20, 50, 100)]
    assert n[0] >= n[1] >= n[2]


def test_skill_que_ninguem_tem_vira_lacuna():
    r = matching.run(S, {"skills": [{"nome": "Habilidade Inexistente XYZ"}, {"nome": "Java"}], "duracao_meses": 3,
                         "disponibilidade_min": 50})
    lac = r["requisitos"][0]
    assert lac["rebaixada"] and not lac["obrigatoria"] and not lac["no_catalogo"] and r["ranking"]
    assert any("não existe no catálogo" in a for a in r["avisos"])


def test_alocados_sempre_aparecem():
    """US12/US13: quem já foi alocado continua no resultado mesmo se os critérios mudarem."""
    alguem = next(cid for cid, c in S.colabs.items() if c["ativo"] and c["senioridade"] == "Júnior")
    r = matching.run(S, {**REQ, "fixar": {"interno": [alguem]}})
    ids = {c["id"] for c in r["ranking"] + r["quase_la"] + r["fixados"]}
    assert alguem in ids


# ---------------------------------------------------------------- prévia (US04)
def test_previa_sem_skills():
    p = buscas.previa(S, {"duracao": "xyz", "inicio": "2026-12-01"})
    assert p["tem_skills"] is False and p["duracao_entendida"] is False and p["inicio"] == "2026-12-01"


def test_previa_com_skills():
    p = buscas.previa(S, {"skills": REQ["skills"], "duracao": "3 meses", "inicio": "2026-12-01",
                          "disponibilidade_min": 50, "senioridades": ["Sênior"]})
    assert p["aptos"] >= p["disponiveis"] >= 0 and p["remanejamento"] == p["aptos"] - p["disponiveis"]
    assert p["fim"] == "2027-02-28" and p["externos"] > 0


# ---------------------------------------------------------------- IA: falha não trava (US10)
def test_provedor_que_falhou_fica_em_pausa(monkeypatch):
    """Gemini sobrecarregado: a 1ª pergunta cai no Groq; a 2ª já vai direto ao Groq (sem esperar o Gemini de novo)."""
    chamadas = []

    def gemini_falha(*a, **k):
        chamadas.append("gemini")
        raise llm.IAErro(503, "UNAVAILABLE", "alta demanda", "gemini")

    def groq_ok(*a, **k):
        chamadas.append("groq")
        return "ok"
    monkeypatch.setattr(llm, "cadeia", lambda: ["gemini", "groq"])
    monkeypatch.setitem(llm.CHAMADAS, "gemini", gemini_falha)
    monkeypatch.setitem(llm.CHAMADAS, "groq", groq_ok)
    assert llm.text("s", "u") == "ok" and llm.text("s", "u") == "ok"
    assert chamadas == ["gemini", "groq", "groq"]


def test_ia_falhando_nao_quebra_o_ranking(monkeypatch):
    r = matching.run(S, REQ)
    antes = [c["id"] for c in r["ranking"]]
    monkeypatch.setattr(llm, "as_json", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("HTTP 503")))
    info = llm.enrich_ranking(REQ, r)
    assert info["usada"] is False and [c["id"] for c in r["ranking"]] == antes
