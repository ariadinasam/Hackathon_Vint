"""Leitura de briefing (PDF/DOCX/TXT) e extração de requisitos (IA com fallback por regras)."""
from __future__ import annotations
import io
import json
import logging
import math
import re
from . import llm
from .sgd import SGD, mkey
from .textutil import fold

log = logging.getLogger("vintmatch.extract")
MAX_CHARS = 30000
CUES = (r"obrigat|desejav|diferencial|\bplus\b|experiencia|nocoes|nocao|conhecimento|dominio|avancad|"
        r"basic|intermediari|necessari|exig|requisit")
MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def read_document(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        txt = "\n".join((p.extract_text() or "") for p in reader.pages[:40])
    elif name.endswith(".docx"):
        import docx
        d = docx.Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        txt = "\n".join(parts)
    elif name.endswith((".txt", ".md")):
        txt = data.decode("utf-8", errors="replace")
    else:
        raise ValueError("Formato não suportado. Use PDF, DOCX, TXT ou MD.")
    return txt.strip()[:MAX_CHARS]


# ---------------------------------------------------------------- regras
def _sentences(text: str) -> list[str]:
    """Divide em orações (frases e trechos entre vírgulas) para decidir obrigatória/desejável e nível."""
    return [s for s in re.split(r"(?<=[.;:!?])\s+|\n+|,\s*|\s+mas\s+", text) if s.strip()]


def _short_forms(s: SGD) -> dict[str, str]:
    """Nomes curtos (<=2 letras) só casam com grafia exata para evitar falso positivo."""
    return {"JS": "JavaScript", "TS": "TypeScript", "UX": "UX/UI", "UI": "UX/UI", "Go": "Go", "Golang": "Go", "C#": "C#", "c#": "C#", "C++": "C++", "c++": "C++"}


def rules_extract(s: SGD, text: str) -> dict:
    ftext = fold(text)
    found: dict[str, dict] = {}
    keys = sorted((k for k in s.name_to_ids if len(k) > 2), key=len, reverse=True)
    sents = _sentences(text)

    def add(canon: str, pos_text: str):
        if canon in found:
            return
        # se a skill aparece em várias orações, usa a que fala de requisito (obrigatória, desejável, nível…)
        cands = [fold(x) for x in sents if fold(pos_text) in fold(x)]
        sent = next((x for x in cands if re.search(CUES, x)), cands[0] if cands else "")
        desej = bool(re.search(r"desejav|diferencial|\bplus\b|nice to have|seria bom|opcional", sent))
        if re.search(r"avancad|dominio|experiencia solida|solidos? conhecimentos?|profund|expert", sent):
            nivel = "avancado"
        elif re.search(r"basic|nocoes|nocao|introdut", sent):
            nivel = "basico"
        else:
            nivel = "basico" if desej else "intermediario"
        found[canon] = {"nome": canon, "obrigatoria": not desej, "nivel": nivel}

    spans: list[tuple[int, int]] = []
    for k in keys:  # mais longos primeiro; ignora ocorrências dentro de um nome maior já casado
        for mt in re.finditer(r"(?<![a-z0-9#+])" + re.escape(k) + r"(?![a-z0-9#+])", ftext):
            a, b = mt.span()
            if any(x <= a and b <= y for x, y in spans):
                continue
            spans.append((a, b))
            canon = s.canonical(k)
            if canon:
                add(canon, text[a:b])
    for short, canon in _short_forms(s).items():
        if re.search(r"(?<![\w#+])" + re.escape(short) + r"(?![\w#+])", text) and s.canonical(canon):
            add(s.canonical(canon), short)

    out = {"skills": list(found.values())}
    m = re.search(r"(\d{1,2})\s*(meses|mes)\b", ftext)
    w = re.search(r"(\d{1,2})\s*semanas", ftext)
    if m:
        out["duracao_meses"] = int(m.group(1))
    elif w:
        out["duracao_meses"] = max(1, math.ceil(int(w.group(1)) / 4))
    p = re.search(r"(\d{1,3})\s*%", ftext)
    if p and 0 < int(p.group(1)) <= 100:
        out["disponibilidade_min"] = int(p.group(1))
    elif re.search(r"tempo integral|dedicacao (integral|exclusiva|total)|full.?time|100 ?por ?cento", ftext):
        out["disponibilidade_min"] = 100
    elif re.search(r"meio periodo|meio-periodo|part.?time|parcial", ftext):
        out["disponibilidade_min"] = 50
    sens = [o for o in s.options["senioridades"] if re.search(r"\b" + re.escape(fold(o)), ftext)]
    if sens:
        out["senioridades"] = sens
    for campo, opts in (("tipo_servico", s.options["tipos_servico"]), ("metodologia", s.options["metodologias"])):
        hit = next((o for o in opts if re.search(r"\b" + re.escape(fold(o)), ftext)), None)
        if hit:
            out[campo] = hit
    ini = re.search(r"\b(" + "|".join(MESES_PT) + r")[a-z]*\.?\s*(?:de\s*|/)?\s*(20\d\d)", ftext) or \
        re.search(r"\b(0?[1-9]|1[0-2])/(20\d\d)\b", ftext)
    if ini:
        mes = ini.group(1)
        mes = MESES_PT.index(mes[:3]) + 1 if not mes.isdigit() else int(mes)
        out["inicio"] = f"{ini.group(2)}-{mes:02d}"
    out["texto"] = text.strip()[:1500]
    return out


# ---------------------------------------------------------------- IA
SYS_EXTRACT = """Você extrai requisitos de alocação de pessoas a partir de briefings de projetos de TI da VINT GLOBAL.
Use preferencialmente nomes do CATÁLOGO de skills fornecido (grafia exata). Inclua skills fora do catálogo só se
forem explicitamente pedidas. Não invente requisitos que não estejam no texto."""


def ai_extract(s: SGD, text: str, prazo: float = 25) -> dict:
    schema = {
        "skills": [{"nome": "nome do catálogo", "obrigatoria": True, "nivel": "basico|intermediario|avancado"}],
        "duracao_meses": "int ou null", "disponibilidade_min": "int 0-100 ou null", "inicio": "AAAA-MM ou null",
        "senioridades": ["valores de SENIORIDADES"], "tipo_servico": "um de TIPOS_SERVICO ou null",
        "metodologia": "uma de METODOLOGIAS ou null", "resumo": "resumo do projeto em até 400 caracteres",
    }
    user = (f"CATÁLOGO: {json.dumps(s.catalog, ensure_ascii=False)}\n"
            f"SENIORIDADES: {s.options['senioridades']}\nTIPOS_SERVICO: {s.options['tipos_servico']}\n"
            f"METODOLOGIAS: {s.options['metodologias']}\n\nFORMATO: {json.dumps(schema, ensure_ascii=False)}\n\n"
            f"BRIEFING:\n\"\"\"\n{text}\n\"\"\"")
    out = llm.as_json(SYS_EXTRACT, user, prazo=prazo)
    out["texto"] = (out.pop("resumo", None) or text)[:1500]
    return out


def extract(s: SGD, text: str, use_ai: bool = True) -> dict:
    origem, erro = "regras", None
    if use_ai and llm.available():
        try:
            out, origem = ai_extract(s, text), "ia"
        except Exception as e:  # noqa: BLE001
            log.warning("extração por IA falhou: %s", llm._limpa(str(e))[:300])
            erro = f"IA indisponível ({llm._limpa(str(e))[:160]}); usadas regras."
            out = rules_extract(s, text)
    else:
        out = rules_extract(s, text)
    # normaliza contra o catálogo
    skills, fora = [], []
    for sk in out.get("skills") or []:
        canon = s.canonical(sk.get("nome", ""))
        if canon:
            skills.append({"nome": canon, "obrigatoria": bool(sk.get("obrigatoria", True)),
                           "nivel": fold(sk.get("nivel") or "intermediario")})
        elif sk.get("nome"):
            fora.append(sk["nome"])
    out["skills"] = skills
    out["skills_fora_catalogo"] = fora
    out["senioridades"] = [x for x in (out.get("senioridades") or []) if x in s.options["senioridades"]]
    for campo, opts in (("tipo_servico", "tipos_servico"), ("metodologia", "metodologias")):
        if out.get(campo) not in s.options[opts]:
            out[campo] = None
    out["origem"] = origem
    if erro:
        out["aviso"] = erro
    return out
