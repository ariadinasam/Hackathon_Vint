"""Camada de IA com vários provedores e reserva automática.

Ordem: o provedor de LLM_PROVIDER (ou o primeiro com chave: Gemini → Groq → Claude) e, se ele falhar, os outros que
tiverem chave. No Gemini há novas tentativas e modelos reserva para erros de capacidade (503/429).
Nenhum nome de pessoa é enviado à IA (pseudônimos C1, C2...) e nenhuma chave aparece em logs.
"""
from __future__ import annotations
import json
import logging
import time
import urllib.error
import urllib.request
from . import config

log = logging.getLogger("vintmatch.llm")
_client = None
_modelo_gemini: str | None = None   # modelo efetivo do Gemini (pode mudar sozinho)
_superficie = "studio"              # "studio" (AI Studio) ou "vertex" (Vertex AI modo express)
_reservas_cache: list[str] | None = None
ULTIMO: dict = {"provedor": None, "modelo": None}
STATUS: dict = {"ok": None, "mensagem": "IA ainda não verificada.", "verificado_em": None, "provedores": {}}
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"          # Google AI Studio (chaves AIza… e AQ.…)
VERTEX_EXPRESS = "https://aiplatform.googleapis.com/v1/publishers/google"  # Vertex AI modo express (chaves AQ.…)
TRANSITORIOS = (429, 500, 502, 503, 504)
PAUSA_FALHA = 120          # s: provedor que falhou por capacidade/rede fica de fora por 2 min (demo não trava)
_falhou_em: dict = {}
_prazo = __import__("threading").local()  # prazo (time.monotonic) da chamada atual


def _restante(padrao: float = 90) -> float:
    fim = getattr(_prazo, "fim", None)
    return padrao if fim is None else max(1.0, min(padrao, fim - time.monotonic()))


def _sem_tempo() -> bool:
    fim = getattr(_prazo, "fim", None)
    return fim is not None and fim - time.monotonic() < 3
NOMES = {"gemini": "Gemini", "groq": "Groq", "claude": "Claude"}
MOTIVOS = {
    400: "Chave inválida ou mal copiada.",
    401: "Chave não autorizada.",
    403: "A chave não tem permissão para esta API (chave restrita ou de outro serviço).",
    404: "O modelo configurado não existe para esta chave.",
    429: "Limite de uso atingido (cota do plano gratuito).",
    503: "O Google está sem capacidade para este modelo agora (alta demanda). É temporário.",
}


class IAErro(RuntimeError):
    def __init__(self, code: int, status: str, message: str, provedor: str = "gemini"):
        self.code, self.status, self.message, self.provedor = code, status, message, provedor
        nome = NOMES.get(provedor, provedor)
        super().__init__(f"{nome} HTTP {code} {status}: {message}" if code else f"Sem conexão com {nome}: {message}")


GeminiErro = IAErro  # compatibilidade


# ---------------------------------------------------------------- provedores e cadeia
def _tem_chave(p: str) -> bool:
    return bool({"gemini": config.GEMINI_API_KEY, "groq": config.GROQ_API_KEY, "claude": config.ANTHROPIC_API_KEY}.get(p))


def cadeia() -> list[str]:
    """Provedores na ordem em que serão tentados."""
    p = config.LLM_PROVIDER
    if p == "none":
        return []
    todos = [x for x in ("gemini", "groq", "claude") if _tem_chave(x)]
    if p in todos:
        return [p] + [x for x in todos if x != p]
    return todos


def provider() -> str | None:
    c = cadeia()
    return c[0] if c else None


def _bloqueado(p: str) -> bool:
    return bool(STATUS.get("provedores", {}).get(p, {}).get("bloqueante"))


def available() -> bool:
    return any(not _bloqueado(p) for p in cadeia())


def _modelo_de(p: str) -> str:
    return {"gemini": _modelo_gemini or config.GEMINI_MODEL, "groq": config.GROQ_MODEL, "claude": config.ANTHROPIC_MODEL}[p]


def model_name() -> str | None:
    vivos = [p for p in cadeia() if not _bloqueado(p)]
    if not vivos:
        return None
    nomes = [f"{NOMES[p]} {_modelo_de(p)}" for p in vivos]
    return nomes[0] + (f" (reserva: {', '.join(nomes[1:])})" if len(nomes) > 1 else "")


def _limpa(msg: str) -> str:
    for segredo in (config.GEMINI_API_KEY, config.ANTHROPIC_API_KEY, config.GROQ_API_KEY):
        if segredo:
            msg = msg.replace(segredo, "***")
    return msg


def _http(method: str, url: str, body: dict | None, headers: dict, provedor: str, timeout: int = 90) -> dict:
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode("utf-8") if body is not None else None,
                                 headers={"Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": "VINT-Match/1.0 (hackathon)", **headers})
    try:
        with urllib.request.urlopen(req, timeout=_restante(timeout)) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8")).get("error", {})
            if isinstance(err, str):
                err = {"message": err}
        except Exception:  # noqa: BLE001
            err = {}
        raise IAErro(e.code, str(err.get("status") or err.get("type") or ""), _limpa(str(err.get("message", ""))[:300]), provedor) from None
    except urllib.error.URLError as e:
        motivo = "TIMEOUT" if "timed out" in str(e.reason) else "REDE"
        raise IAErro(0, motivo, _limpa(str(e.reason))[:200], provedor) from None
    except TimeoutError:
        raise IAErro(0, "TIMEOUT", "a resposta demorou demais", provedor) from None


def _gemini_http(method: str, path: str, body: dict | None = None, timeout: int = 90) -> dict:
    url = path if path.startswith("https://") else f"{GEMINI_BASE}/{path}"
    return _http(method, url, body, {"x-goog-api-key": config.GEMINI_API_KEY}, "gemini", timeout)


# ---------------------------------------------------------------- Gemini
def _listar_gemini() -> list[str]:
    global _reservas_cache
    if _reservas_cache is None:
        try:
            data = _gemini_http("GET", "models?pageSize=200", timeout=20)
            nomes = [m["name"].split("/", 1)[1] for m in data.get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])]
        except IAErro:
            nomes = []
        ruins = ("image", "tts", "audio", "live", "embedding", "vision", "computer", "robotics")
        flash = [n for n in nomes if n.startswith("gemini") and "flash" in n and not any(r in n for r in ruins)]
        estaveis = sorted([n for n in flash if "preview" not in n and "exp" not in n], reverse=True)
        _reservas_cache = estaveis + sorted([n for n in flash if n not in estaveis], reverse=True)
    return _reservas_cache


def _modelos_gemini() -> list[str]:
    """Modelo principal + reservas (do .env ou descobertas pela própria chave)."""
    prim = _modelo_gemini or config.GEMINI_MODEL
    extras = config.GEMINI_MODELOS_RESERVA or (_listar_gemini() if _superficie == "studio" else [])
    out = [prim] + [m for m in extras if m != prim]
    return out[:4]


_sem_thinking: set = set()


def _thinking(modelo: str) -> dict | None:
    """Pede raciocínio mínimo: extração e ranking não precisam pensar muito, e isso corta segundos da resposta."""
    if modelo in _sem_thinking:
        return None
    if modelo.startswith("gemini-2.5"):
        return {"thinkingBudget": 0 if "flash" in modelo else 128}
    if modelo.startswith("gemini-3") or modelo.startswith("gemini-4"):
        return {"thinkingLevel": "low"}
    return None


def _gemini_um(modelo: str, system: str, user: str, max_tokens: int, json_mode: bool) -> str:
    gen = {"maxOutputTokens": max_tokens, "temperature": 0.2}
    if json_mode:
        gen["responseMimeType"] = "application/json"
    pensar = _thinking(modelo)
    if pensar:
        gen["thinkingConfig"] = pensar
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": gen}
    base = VERTEX_EXPRESS if _superficie == "vertex" else GEMINI_BASE
    try:
        data = _gemini_http("POST", f"{base}/models/{modelo}:generateContent", body)
    except IAErro as e:
        if e.code == 400 and pensar and "think" in e.message.lower():
            _sem_thinking.add(modelo)
            gen.pop("thinkingConfig", None)
            data = _gemini_http("POST", f"{base}/models/{modelo}:generateContent", body)
        else:
            raise
    cand = (data.get("candidates") or [{}])[0]
    txt = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought")).strip()
    if not txt:
        raise IAErro(200, "VAZIO", f"resposta sem texto (finishReason={cand.get('finishReason')})", "gemini")
    return txt


def _gemini(system: str, user: str, max_tokens: int, json_mode: bool) -> str:
    """Modelo principal (com 1 nova tentativa); em erro de capacidade (503/429…) ou 404, tenta modelos reserva."""
    prim = _modelo_gemini or config.GEMINI_MODEL
    try:
        try:
            txt = _gemini_um(prim, system, user, max_tokens, json_mode)
        except IAErro as e:
            if e.code not in TRANSITORIOS or _sem_tempo():
                raise
            time.sleep(1)
            txt = _gemini_um(prim, system, user, max_tokens, json_mode)
        ULTIMO.update(provedor="gemini", modelo=prim)
        return txt
    except IAErro as e:
        if e.code not in TRANSITORIOS and e.code != 404:
            raise
        ultimo = e
    for alt in [m for m in _modelos_gemini() if m != prim][:2]:
        if _sem_tempo():
            break
        try:
            txt = _gemini_um(alt, system, user, max_tokens, json_mode)
            ULTIMO.update(provedor="gemini", modelo=alt)
            log.warning("IA: %s indisponível (%s); respondido pelo modelo reserva %s", prim, ultimo.code, alt)
            return txt
        except IAErro as e:
            ultimo = e
    raise ultimo


# ---------------------------------------------------------------- Groq (API compatível com OpenAI) e Claude
def _groq(system: str, user: str, max_tokens: int, json_mode: bool) -> str:
    body = {"model": config.GROQ_MODEL, "temperature": 0.2, "max_tokens": min(max_tokens, 4000),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    for tentativa in range(2):
        try:
            data = _http("POST", f"{config.GROQ_BASE}/chat/completions", body,
                         {"Authorization": f"Bearer {config.GROQ_API_KEY}"}, "groq")
            txt = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
            if not txt:
                raise IAErro(200, "VAZIO", "resposta sem texto", "groq")
            ULTIMO.update(provedor="groq", modelo=config.GROQ_MODEL)
            return txt
        except IAErro as e:
            if e.code in TRANSITORIOS and tentativa == 0 and not _sem_tempo():
                time.sleep(1)
                continue
            raise
    raise IAErro(0, "", "sem resposta", "groq")


def _claude(system: str, user: str, max_tokens: int, json_mode: bool = False) -> str:
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=90.0, max_retries=1)
    resp = _client.messages.create(model=config.ANTHROPIC_MODEL, max_tokens=max_tokens, system=system,
                                   messages=[{"role": "user", "content": user}])
    ULTIMO.update(provedor="claude", modelo=config.ANTHROPIC_MODEL)
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


CHAMADAS = {"gemini": lambda s, u, m, j: _gemini(s, u, m * 2, j), "groq": _groq, "claude": _claude}


def text(system: str, user: str, max_tokens: int = 1500, json_mode: bool = False, prazo: float | None = None) -> str:
    """Tenta os provedores em ordem dentro do prazo (s). Provedor que acabou de falhar por capacidade/rede é pulado."""
    erros = []
    _prazo.fim = time.monotonic() + prazo if prazo else None
    try:
        vivos = [p for p in cadeia() if not _bloqueado(p)]
        frescos = [p for p in vivos if time.monotonic() - _falhou_em.get(p, -1e9) > PAUSA_FALHA]
        for p in frescos or vivos[:1]:
            if _sem_tempo():
                erros.append("prazo esgotado")
                break
            try:
                txt = CHAMADAS[p](system, user, max_tokens, json_mode)
                _falhou_em.pop(p, None)
                return txt
            except Exception as e:  # noqa: BLE001
                if not isinstance(e, IAErro) or e.code in TRANSITORIOS or e.code == 0:
                    _falhou_em[p] = time.monotonic()
                erros.append(_limpa(str(e))[:200])
                log.warning("IA: %s falhou (%s); tentando o próximo provedor", NOMES.get(p, p), erros[-1])
        raise RuntimeError(" | ".join(erros) or "Nenhum provedor de IA configurado")
    finally:
        _prazo.fim = None


def as_json(system: str, user: str, max_tokens: int = 2500, prazo: float | None = None):
    raw = text(system + "\nResponda SOMENTE com JSON válido (um objeto), sem markdown e sem comentários.", user, max_tokens,
               json_mode=True, prazo=prazo)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    starts = [i for i in (raw.find("{"), raw.find("[")) if i >= 0]
    if not starts:
        raise ValueError("resposta sem JSON")
    i = min(starts)
    j = max(raw.rfind("}"), raw.rfind("]"))
    return json.loads(raw[i:j + 1])


# ---------------------------------------------------------------- verificação na subida
def _verificar_gemini() -> dict:
    global _modelo_gemini, _superficie
    teste = {"contents": [{"role": "user", "parts": [{"text": "Responda apenas: ok"}]}], "generationConfig": {"maxOutputTokens": 256}}
    try:
        _gemini_http("POST", f"models/{config.GEMINI_MODEL}:generateContent", teste, timeout=30)
        _modelo_gemini, _superficie = config.GEMINI_MODEL, "studio"
        return {"ok": True, "bloqueante": False, "mensagem": f"Gemini OK ({config.GEMINI_MODEL})."}
    except IAErro as e:
        if e.code in TRANSITORIOS or e.code == 404:
            for alt in [m for m in (config.GEMINI_MODELOS_RESERVA or _listar_gemini()) if m != config.GEMINI_MODEL][:3]:
                try:
                    _gemini_http("POST", f"models/{alt}:generateContent", teste, timeout=30)
                    _modelo_gemini = alt
                    motivo = "não existe para esta chave" if e.code == 404 else f"está indisponível agora (HTTP {e.code})"
                    return {"ok": True, "bloqueante": False,
                            "mensagem": f"O modelo {config.GEMINI_MODEL} {motivo}; usando {alt}."
                                        + (f" Ajuste GEMINI_MODEL={alt} no .env." if e.code == 404 else "")}
                except IAErro:
                    continue
            return {"ok": False, "bloqueante": False,
                    "mensagem": f"{MOTIVOS.get(e.code, 'Erro do Gemini.')} Detalhe: {e}. O app tenta de novo a cada busca."}
        if e.code in (400, 401, 403) and config.GEMINI_API_KEY.startswith("AQ."):
            try:
                _gemini_http("POST", f"{VERTEX_EXPRESS}/models/{config.GEMINI_MODEL}:generateContent", teste, timeout=30)
                _superficie, _modelo_gemini = "vertex", config.GEMINI_MODEL
                return {"ok": True, "bloqueante": False,
                        "mensagem": f"Chave do Vertex AI (modo express) detectada; usando aiplatform.googleapis.com ({config.GEMINI_MODEL})."}
            except IAErro:
                pass
        dica = (" Gere uma chave em https://aistudio.google.com/apikey (a assinatura Gemini Pro do app não é uma chave de API)."
                if e.code in (400, 401, 403) else "")
        rede = "Sem acesso ao Google (internet, proxy ou firewall)." if e.code == 0 else ""
        return {"ok": False, "bloqueante": e.code in (400, 401, 403),
                "mensagem": f"{rede or MOTIVOS.get(e.code, 'Erro do Gemini.')}{dica} Detalhe: {e}"}


def _verificar_groq() -> dict:
    try:
        _groq("Você responde com uma palavra.", "Responda apenas: ok", 16, False)
        return {"ok": True, "bloqueante": False, "mensagem": f"Groq OK ({config.GROQ_MODEL})."}
    except IAErro as e:
        dica = " Gere uma chave grátis em https://console.groq.com/keys." if e.code in (401, 403) else ""
        return {"ok": False, "bloqueante": e.code == 401,
                "mensagem": f"{MOTIVOS.get(e.code, 'Erro do Groq.')}{dica} Detalhe: {e}"}


def verificar() -> dict:
    """Testa cada provedor com chave (uma chamada mínima) e guarda o motivo exato em STATUS. Nunca registra a chave."""
    from datetime import datetime, timezone
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    provs = {}
    for p in cadeia():
        provs[p] = (_verificar_gemini() if p == "gemini" else _verificar_groq() if p == "groq"
                    else {"ok": True, "bloqueante": False, "mensagem": f"Claude configurado ({config.ANTHROPIC_MODEL})."})
        log.log(logging.INFO if provs[p]["ok"] else logging.WARNING, "IA %s: %s", NOMES[p], provs[p]["mensagem"])
    if not provs:
        STATUS.update(ok=False, bloqueante=False, verificado_em=agora, provedores={},
                      mensagem="IA desligada: nenhuma chave no .env (GEMINI_API_KEY, GROQ_API_KEY ou ANTHROPIC_API_KEY).")
        return STATUS
    ok = [p for p, v in provs.items() if v["ok"]]
    STATUS.update(ok=bool(ok), bloqueante=all(v["bloqueante"] for v in provs.values()), verificado_em=agora, provedores=provs,
                  mensagem=" · ".join(f"{NOMES[p]}: {v['mensagem']}" for p, v in provs.items()))
    return STATUS


# ---------------------------------------------------------------- matching
SYS_MATCH = """Você é especialista em alocação de profissionais de TI da VINT GLOBAL.
Avalie a aderência de cada candidato ao projeto descrito, considerando o texto do projeto, as skills e o nível
exigidos, o histórico de demandas parecidas e a disponibilidade no período. Seja objetivo e factual: use apenas
os dados fornecidos, não invente experiências. Escreva em português do Brasil."""


def enrich_ranking(req: dict, result: dict, n: int = 8, prazo: float = 45) -> dict:
    """Pede à IA um score semântico + justificativa + resumo de PDI para os top-N. Altera result in-place."""
    cands = result["ranking"][:n]
    if not cands:
        return {"usada": False}
    perfis = []
    for i, c in enumerate(cands, 1):
        c["_ref"] = f"C{i}"
        perfis.append({
            "ref": c["_ref"], "cargo": c["cargo"], "senioridade": c["senioridade"],
            "skills_pedidas": [{k: x[k] for k in ("nome", "obrigatoria", "nivel_pedido", "nivel_atual", "evidencia_projeto")}
                               for x in c["skills_match"]],
            "total_skills_declaradas": c["n_skills_declaradas"],
            "historico_similar": [{k: h[k] for k in ("tipo_servico", "metodologia", "andamento", "skills_em_comum",
                                                     "periodo", "similaridade")} for h in c["historico_similar"]],
            "disponibilidade_por_mes": c["disp_meses"], "precisa_remanejamento": bool(c["remanejamento"]),
            "lacunas_pdi": [p["skill"] + f' ({p["de"]}→{p["para"]})' for p in c.get("pdi", [])],
        })
    projeto = {"texto_livre": req.get("texto") or "", "tipo_servico": req.get("tipo_servico"),
               "metodologia": req.get("metodologia"), "periodo": result["periodo"]["rotulo"],
               "disponibilidade_minima_pct": result["disponibilidade_min"], "requisitos": result["requisitos"]}
    user = ("PROJETO:\n" + json.dumps(projeto, ensure_ascii=False) + "\n\nCANDIDATOS:\n" +
            json.dumps(perfis, ensure_ascii=False) +
            '\n\nDevolva um objeto JSON: {"candidatos": [{"ref":"C1","aderencia":0-100,"justificativa":"até 240 caracteres",'
            '"pdi":"até 200 caracteres ou vazio"}]}. "aderencia" mede o quanto o perfil combina com o projeto '
            "(contexto, domínio, tipo de serviço), não a disponibilidade.")
    try:
        out = as_json(SYS_MATCH, user, prazo=prazo)
        if isinstance(out, dict):
            out = out.get("candidatos") or next((v for v in out.values() if isinstance(v, list)), [])
        by_ref = {o.get("ref"): o for o in out if isinstance(o, dict)}
        for c in cands:
            o = by_ref.get(c.pop("_ref"))
            if not o:
                continue
            sem = max(0, min(100, int(o.get("aderencia", 0))))
            comp = c["componentes"]
            comp["semantico"] = sem
            comp["semantico_fonte"] = "IA"
            sc = 0.40 * comp["skills"] + 0.25 * comp["disponibilidade"] + 0.20 * comp["historico"] + 0.15 * sem
            c["score"] = round(max(sc - (8 if c["perfil_amplo"] else 0), 0), 1)
            c["justificativa_regra"] = c["justificativa"]
            c["justificativa"] = (o.get("justificativa") or c["justificativa"]).strip()
            if o.get("pdi"):
                c["pdi_resumo"] = o["pdi"].strip()
        result["ranking"].sort(key=lambda x: -x["score"])
        return {"usada": True, "modelo": f'{NOMES.get(ULTIMO["provedor"], "")} {ULTIMO["modelo"]}'.strip()}
    except Exception as e:  # noqa: BLE001
        for c in cands:
            c.pop("_ref", None)
        log.warning("IA indisponível no matching: %s", _limpa(str(e))[:300])
        return {"usada": False, "erro": f"IA indisponível: {_limpa(str(e))[:240]}. Usado o score por regras."}
