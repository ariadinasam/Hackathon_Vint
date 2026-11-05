/* VINT Match — front-end (JS puro, sem build). */
const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const state = { skills: [], meta: null, last: null };
const NIVEIS = [["basico", "Básico"], ["intermediario", "Intermediário"], ["avancado", "Avançado"]];

function toast(msg, ms = 4000) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), ms); }
function nome(n) { // modo apresentação: mascara nomes (LGPD)
  if (!$("#mask").checked || !n) return esc(n);
  return esc(n.split(/\s+/).filter((p) => p && p !== "Mocado").map((p) => p[0] + ".").join(" "));
}
async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || `Erro ${r.status}`);
  return body;
}

/* ---------------- meta / formulário ---------------- */
async function init() {
  const m = await api("/api/meta");
  state.meta = m;
  $("#st-fonte").textContent = `SGD: ${m.fonte_dados === "postgres" ? "Postgres (somente leitura)" : "snapshot SQLite"} · ${m.colaboradores_ativos} ativos`;
  $("#st-ia").textContent = m.ia_ativa ? `IA ativa · ${m.modelo}` : "IA desligada (modo regras)";
  $("#st-ia").classList.toggle("on", m.ia_ativa);
  if (!m.ia_ativa) { $("#usar-ia").checked = false; $("#usar-ia").disabled = true; }
  $("#catalogo").innerHTML = m.catalogo.map((s) => `<option value="${esc(s)}">`).join("");
  $("#sens").innerHTML = m.senioridades.map((s) => `<label class="check"><input type="checkbox" value="${esc(s)}"> ${esc(s)}</label>`).join("");
  $("#tipo").innerHTML += m.tipos_servico.map((s) => `<option>${esc(s)}</option>`).join("");
  $("#metod").innerHTML += m.metodologias.map((s) => `<option>${esc(s)}</option>`).join("");
  $("#inicio").value = m.referencia;
}

function renderSkills() {
  $("#skills").innerHTML = state.skills.map((s, i) => `
    <div class="sk ${s.obrigatoria ? "" : "desej"}">
      <span class="name">${esc(s.nome)}</span>
      <select data-i="${i}" data-k="obrigatoria"><option value="1" ${s.obrigatoria ? "selected" : ""}>Obrigatória</option><option value="0" ${s.obrigatoria ? "" : "selected"}>Desejável</option></select>
      <select data-i="${i}" data-k="nivel">${NIVEIS.map(([v, l]) => `<option value="${v}" ${s.nivel === v ? "selected" : ""}>${l}</option>`).join("")}</select>
      <button type="button" class="x" data-del="${i}" title="Remover">×</button>
    </div>`).join("") || `<div class="muted small">Nenhuma skill ainda.</div>`;
}
function addSkill(nomeSkill, obrigatoria = true, nivel = "intermediario") {
  nomeSkill = (nomeSkill || "").trim();
  if (!nomeSkill) return;
  const canon = state.meta.catalogo.find((c) => c.toLowerCase() === nomeSkill.toLowerCase()) || nomeSkill;
  if (state.skills.some((s) => s.nome.toLowerCase() === canon.toLowerCase())) return;
  if (!state.meta.catalogo.includes(canon)) toast(`"${canon}" não está no catálogo do SGD — será tratada como lacuna.`);
  state.skills.push({ nome: canon, obrigatoria, nivel });
  renderSkills();
}
$("#skills").addEventListener("change", (e) => {
  const { i, k } = e.target.dataset; if (i === undefined) return;
  state.skills[i][k] = k === "obrigatoria" ? e.target.value === "1" : e.target.value; renderSkills();
});
$("#skills").addEventListener("click", (e) => { if (e.target.dataset.del !== undefined) { state.skills.splice(+e.target.dataset.del, 1); renderSkills(); } });
$("#skill-btn").onclick = () => { addSkill($("#skill-input").value); $("#skill-input").value = ""; };
$("#skill-input").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); $("#skill-btn").click(); } });
$("#disp").oninput = () => ($("#disp-out").textContent = $("#disp").value + "%");

function fillForm(x) {
  if (x.texto) $("#texto").value = x.texto;
  if (x.skills?.length) { state.skills = []; x.skills.forEach((s) => addSkill(s.nome, s.obrigatoria, s.nivel)); }
  if (x.duracao_meses) $("#duracao").value = x.duracao_meses;
  if (x.disponibilidade_min != null) { $("#disp").value = x.disponibilidade_min; $("#disp-out").textContent = x.disponibilidade_min + "%"; }
  if (x.inicio) $("#inicio").value = x.inicio;
  if (x.tipo_servico) $("#tipo").value = x.tipo_servico;
  if (x.metodologia) $("#metod").value = x.metodologia;
  if (x.senioridades) document.querySelectorAll("#sens input").forEach((c) => (c.checked = x.senioridades.includes(c.value)));
  const fora = x.skills_fora_catalogo?.length ? ` Fora do catálogo: ${x.skills_fora_catalogo.join(", ")}.` : "";
  toast(`Requisitos extraídos (${x.origem === "ia" ? "IA" : "regras"}): ${x.skills.length} skills.${fora}${x.aviso ? " " + x.aviso : ""}`, 6000);
}
async function extractFrom(file, texto) {
  const fd = new FormData();
  if (file) fd.append("arquivo", file);
  fd.append("texto", texto || "");
  fd.append("usar_ia", $("#usar-ia").checked ? "true" : "false");
  $("#file-status").innerHTML = `<span class="spinner"></span> Lendo ${file ? esc(file.name) : "texto"}…`;
  try {
    const x = await api("/api/extract", { method: "POST", body: fd });
    fillForm(x);
    $("#file-status").textContent = file ? `✔ ${file.name} — ${x.caracteres_lidos} caracteres lidos` : "";
  } catch (e) { $("#file-status").textContent = ""; toast(e.message); }
}
$("#pick").onclick = (e) => { e.preventDefault(); $("#file").click(); };
$("#file").onchange = () => $("#file").files[0] && extractFrom($("#file").files[0]);
const drop = $("#drop");
["dragover", "dragenter"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove("over")));
drop.addEventListener("drop", (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) extractFrom(f); });
$("#btn-extract-text").onclick = () => $("#texto").value.trim() ? extractFrom(null, $("#texto").value) : toast("Escreva a descrição primeiro.");

/* ---------------- matching ---------------- */
$("#form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const pend = $("#skill-input").value.trim(); if (pend) { addSkill(pend); $("#skill-input").value = ""; }
  const body = {
    skills: state.skills, inicio: $("#inicio").value || null, duracao_meses: +$("#duracao").value || 3,
    disponibilidade_min: +$("#disp").value, texto: $("#texto").value,
    senioridades: [...document.querySelectorAll("#sens input:checked")].map((c) => c.value),
    tipo_servico: $("#tipo").value || null, metodologia: $("#metod").value || null,
    incluir_externos: $("#externos").checked, usar_ia: $("#usar-ia").checked,
  };
  const btn = $("#btn-match"); btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> Buscando no SGD…`;
  const t0 = performance.now();
  try {
    state.last = await api("/api/match", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    state.last._total_s = ((performance.now() - t0) / 1000).toFixed(1);
    renderResults();
  } catch (err) { toast(err.message); } finally { btn.disabled = false; btn.textContent = "Encontrar talentos"; }
});
$("#mask").onchange = () => state.last && renderResults();

const bar = (l, v) => v == null ? "" : `<div class="bar"><div class="l"><span>${l}</span><b>${v}</b></div><div class="t"><div class="f" style="width:${v}%"></div></div></div>`;
function monthPills(c, need) {
  return c.disp_meses.map((m) => `<span class="m ${m.disp >= need ? "ok" : m.disp > 0 ? "part" : "no"}" title="livre no mês">${esc(m.mes)} · ${m.disp}%</span>`).join("");
}
function skillPills(c) {
  return c.skills_match.map((s) => {
    const cls = s.ok ? "ok" : s.nivel_atual !== "—" ? "low" : "miss";
    const tip = `${s.obrigatoria ? "Obrigatória" : "Desejável"} · pedido ${s.nivel_pedido} · atual ${s.nivel_atual}${s.evidencia_projeto ? " · usada em projeto" : ""}`;
    return `<span class="s ${cls}" title="${esc(tip)}">${esc(s.nome)}${s.evidencia_projeto ? " ★" : ""}</span>`;
  }).join("");
}
function remBox(r) {
  if (!r) return "";
  return `<div class="box red"><h4>O que precisaria ser remanejado</h4>
    <div>Liberar: ${r.liberar_por_mes.map((x) => `<b>${x.liberar_pct}%</b> em ${esc(x.mes)}`).join(", ")} · viabilidade <b>${esc(r.viabilidade)}</b></div>
    <table><tr><th>Demanda atual</th><th>Status</th><th>Contrato</th><th>Ocupação</th><th>Falar com</th><th>Sugestão</th></tr>
    ${r.alocacoes.map((a) => `<tr><td>${esc(a.demanda)}<div class="muted small">${esc(a.tipo_servico)}</div></td><td>${esc(a.andamento)}<div class="small"><b>${esc(a.facilidade)}</b></div></td>
      <td>${esc(a.contrato)}<div class="muted small">${esc(a.situacao_contrato)}</div></td><td>${a.meses.map((m) => `${esc(m.mes)}: ${m.pct}%`).join("<br>")}</td>
      <td>${nome(a.gerente)}</td><td>${esc(a.sugestao)}</td></tr>`).join("")}</table></div>`;
}
function pdiBox(c) {
  if (!c.pdi?.length && !c.pdi_resumo) return "";
  return `<div class="box"><h4>Sugestão de PDI</h4>${c.pdi_resumo ? `<p>${esc(c.pdi_resumo)}</p>` : ""}<ul>
    ${c.pdi.map((p) => `<li><b>${esc(p.skill)}</b>: ${esc(p.de)} → ${esc(p.para)} (estimativa ${esc(p.prazo_estimado)})
      ${p.base_existente.length ? `<br><span class="muted">Base que já tem: ${p.base_existente.map(esc).join(", ")}</span>` : ""}
      ${p.mentor_sugerido ? `<br>Mentor interno: ${nome(p.mentor_sugerido)}` : ""}
      ${p.pratica_em.length ? `<br>Praticar em: ${p.pratica_em.map(esc).join(", ")}` : ""}</li>`).join("")}</ul>
    <div class="muted small">Não há catálogo de cursos no SGD: trilha sugerida a partir das lacunas e de colegas avançados.</div></div>`;
}
function histBox(c) {
  if (!c.historico_similar.length) return `<div class="box muted">Sem histórico registrado em demandas parecidas.</div>`;
  return `<div class="box"><h4>Já participou de algo parecido?</h4><table><tr><th>Demanda</th><th>Tipo · método</th><th>Skills em comum</th><th>Período</th><th>Similar.</th></tr>
    ${c.historico_similar.map((h) => `<tr><td>${esc(h.demanda)}${h.em_andamento ? ' <span class="b">atual</span>' : ""}<div class="muted small">${esc(h.andamento)}</div></td>
      <td>${esc(h.tipo_servico)} · ${esc(h.metodologia)}</td><td>${h.skills_em_comum.map(esc).join(", ") || "—"}</td><td>${esc(h.periodo)}<div class="muted small">${h.fte_meses} FTE-mês</div></td><td>${h.similaridade}%</td></tr>`).join("")}</table></div>`;
}
function card(c, i, need, cls = "") {
  const k = c.componentes;
  return `<article class="card ${cls}" id="cand-${c.id}">
    <div><div class="score" style="--p:${c.score}"><span>${Math.round(c.score)}</span></div><div class="rank">#${i + 1}</div></div>
    <div>
      <div class="who"><div><div class="n">${nome(c.nome)}</div><div class="muted">${esc(c.cargo)} · ${esc(c.senioridade)} · ${esc(c.modalidade)} · ${esc(c.vinculo)}</div></div>
        <div class="badges">${c.badges.map((b) => `<span class="b ${esc(b.split(" ")[0])}">${esc(b)}</span>`).join("")}</div></div>
      <p class="just">${esc(c.justificativa)}</p>
      <div class="bars">${bar("Skills", k.skills)}${bar("Disponib.", k.disponibilidade)}${bar("Histórico", k.historico)}${bar(k.semantico_fonte === "IA" ? "Aderência IA" : "Semântico", k.semantico)}</div>
      <div class="months">${monthPills(c, need)}</div>
      <div class="skillrow">${skillPills(c)}</div>
      ${c.remanejamento ? remBox(c.remanejamento) : ""}
      <details><summary>Histórico, PDI e detalhes</summary>${histBox(c)}${pdiBox(c)}
        <div class="muted small" style="margin-top:6px">${c.n_skills_declaradas} skills declaradas no SGD${c.perfil_amplo ? " — perfil amplo, confirme com o líder" : ""}.</div></details>
    </div></article>`;
}
function renderResults() {
  const r = state.last, need = r.disponibilidade_min, s = r.resumo;
  const hot = r.ranking.filter((c) => c.mais_viavel_alocado);
  const ia = r.ia?.usada ? `IA (${esc(r.ia.modelo)})` : r.ia?.erro ? "regras (IA falhou)" : "regras";
  $("#results").innerHTML = `
    <div class="summary">
      <div class="kpi"><div class="v">${s.avaliados}</div><div class="l">ativos avaliados</div></div>
      <div class="kpi"><div class="v">${s.aptos}</div><div class="l">com as skills obrigatórias</div></div>
      <div class="kpi"><div class="v">${s.disponiveis}</div><div class="l">disponíveis ≥ ${need}%</div></div>
      <div class="kpi"><div class="v">${s.remanejamento}</div><div class="l">no ranking com remanejamento</div></div>
      <div class="kpi"><div class="v">${r._total_s}s</div><div class="l">tempo total · ${ia}</div></div>
    </div>
    ${hot.length ? `<div class="alert hot"><b>Remanejamento:</b> ${hot.map((c) => `<a href="#cand-${c.id}">${nome(c.nome)}</a>`).join(", ")}
      ${hot.length > 1 ? "têm" : "tem"} aderência técnica igual ou maior que o melhor candidato disponível, mas ${hot.length > 1 ? "estão alocados" : "está alocado(a)"} no período. Veja o que precisaria ser remanejado.</div>` : ""}
    ${r.avisos.map((a) => `<div class="alert">${esc(a)}</div>`).join("")}${r.ia?.erro ? `<div class="alert">${esc(r.ia.erro)}</div>` : ""}
    <div class="reqs"><span class="muted">Período ${esc(r.periodo.rotulo)} ·</span>${r.requisitos.map((q) => `<span class="chip" title="${q.colabs_com_skill} colaboradores ativos têm a skill">${esc(q.nome)} · ${esc(q.nivel)}${q.obrigatoria ? "" : " (desejável)"} · ${q.colabs_com_skill} pessoas</span>`).join("")}</div>
    <div class="section-title"><h3>Ranking de candidatos internos (SGD)</h3><span class="muted small">score = 40% skills · 25% disponibilidade · 20% histórico · 15% aderência</span></div>
    ${r.ranking.length ? r.ranking.map((c, i) => card(c, i, need, i === 0 ? "top" : "")).join("") : `<div class="empty">Ninguém atende a todas as skills obrigatórias. Veja "Quase lá" e os talentos externos.</div>`}
    ${r.quase_la.length ? `<div class="section-title"><h3>Quase lá — candidatos a PDI</h3><span class="muted small">faltam 1–2 skills obrigatórias</span></div>${r.quase_la.map((c, i) => card(c, i, need)).join("")}` : ""}
    ${r.externos.length ? `<div class="section-title"><h3>Talentos externos — InHire</h3><span class="b PDI">dados sintéticos de teste</span></div>
      <div class="panel"><table><tr><th>Talento</th><th>Perfil</th><th>Skills atendidas</th><th>Disp. informada</th><th>Score</th></tr>
      ${r.externos.map((t) => `<tr><td>${nome(t.nome)}</td><td>${esc(t.cargo)} · ${esc(t.senioridade)} · ${esc(t.modalidade)}</td><td>${t.skills_atendidas.map(esc).join(", ")}</td><td>${t.disponibilidade}%</td><td><b>${t.score}</b></td></tr>`).join("")}</table></div>` : ""}
    ${r.contexto_rag?.length ? `<div class="section-title"><h3>Base de conhecimento relacionada</h3></div>${r.contexto_rag.map((c) => `<div class="src"><b>${esc(c.fonte)} › ${esc(c.secao)}</b><div>${esc(c.texto.slice(0, 320))}…</div></div>`).join("")}` : ""}
    <p class="muted small">Fonte: ${r.fonte_dados === "postgres" ? "Postgres SGD (somente leitura)" : "snapshot SQLite do SGD"} · referência ${esc(r.periodo.referencia)} · planejamento registrado até ${esc(r.periodo.horizonte_planejamento)} · cálculo em ${r.tempo_ms} ms.</p>`;
}

/* ---------------- RAG ---------------- */
async function ask(q) {
  $("#rag-q").value = q;
  $("#rag-out").innerHTML = `<p><span class="spinner"></span> Consultando a base…</p>`;
  try {
    const r = await api("/api/rag", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pergunta: q }) });
    $("#rag-out").innerHTML = `<div class="answer">${esc(r.resposta)}</div><h3>Fontes</h3>${r.fontes.map((f, i) => `<div class="src"><b>[${i + 1}] ${esc(f.fonte)} › ${esc(f.secao)}</b><div>${esc(f.texto)}</div></div>`).join("")}`;
  } catch (e) { $("#rag-out").innerHTML = `<div class="alert">${esc(e.message)}</div>`; }
}
$("#rag-form").addEventListener("submit", (e) => { e.preventDefault(); const q = $("#rag-q").value.trim(); if (q) ask(q); });
document.querySelectorAll(".suggest .chip").forEach((b) => (b.onclick = () => ask(b.dataset.q)));

/* ---------------- abas ---------------- */
document.querySelectorAll(".tab").forEach((t) => (t.onclick = () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
  $("#tab-match").hidden = t.dataset.tab !== "match"; $("#tab-rag").hidden = t.dataset.tab !== "rag";
}));

renderSkills();
init().catch((e) => toast("Falha ao carregar metadados: " + e.message));
