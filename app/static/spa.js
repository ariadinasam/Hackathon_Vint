/* VINT Match — SPA (JS puro, sem build) sobre o design "Vint_Global — Alocação de talento".
   Rotas por hash: #/login, #/primeiro-acesso, #/, #/buscas, #/buscas/nova, #/buscas/:id, #/buscas/:id/:origem/:cid,
   #/usuarios (admin), #/perfil, #/base. Todos os dados vêm da API (SGD somente leitura + banco do app). */
"use strict";

/* ============================================================ utilidades */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const fold = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

const ICON = {
  arrow: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  back: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  alert: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  warn: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  eyeoff: '<path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/>',
  eye: '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
  circle: '<circle cx="12" cy="12" r="8"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  pencil: '<path d="M12 20h9"/><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838.838-2.872a2 2 0 0 1 .506-.854z"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  mail: '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
  book: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
  printer: '<path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  report: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M8 18v-2"/><path d="M12 18v-5"/><path d="M16 18v-3"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
};
const ic = (n, cls = "") => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICON[n] || ""}</svg>`;

const S = { me: null, meta: null, sel: new Map(), remOn: true, q: "", tema: "claro" };
try { S.tema = localStorage.getItem("vm_tema") === "escuro" ? "escuro" : "claro"; } catch (_) { /* sem storage */ }
function aplicaTema() { document.documentElement.dataset.theme = S.tema === "escuro" ? "dark" : "light"; }
aplicaTema();

const ini = (n) => (n || "?").split(/\s+/).filter((p) => p && p !== "Mocado").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
const nm = (n) => esc(n);
function fmtDate(iso, withTime = false) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return esc(iso);
  const base = `${String(d.getDate()).padStart(2, "0")} ${MES[d.getMonth()]} ${d.getFullYear()}`;
  return withTime ? `${base}, ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}` : base;
}
function fmtRel(iso) {
  if (!iso) return "—";
  const d = new Date(iso), now = new Date();
  const hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  const day = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const diff = Math.round((day(now) - day(d)) / 864e5);
  if (diff === 0) return `Hoje, ${hm}`;
  if (diff === 1) return `Ontem, ${hm}`;
  return fmtDate(iso);
}
function toast(msg, ms = 5000) {
  const t = $("#toast"); t.textContent = msg; t.hidden = false;
  clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), ms);
}
async function api(path, opts = {}) {
  const o = { credentials: "same-origin", ...opts };
  if (o.json !== undefined) { o.body = JSON.stringify(o.json); o.headers = { "Content-Type": "application/json", ...(o.headers || {}) }; delete o.json; }
  const r = await fetch(path, o);
  let body = null;
  try { body = await r.json(); } catch (_) { body = null; }
  if (r.status === 401 && !path.startsWith("/api/auth/")) { S.me = null; go("#/login"); throw new Error("Sessão expirada."); }
  if (!r.ok) {
    const d = body && body.detail;
    const err = new Error(typeof d === "string" ? d : (d && d.mensagem) || `Erro ${r.status}`);
    err.status = r.status; err.detail = d; throw err;
  }
  return body;
}
const go = (h) => { if (location.hash !== h) location.hash = h; else render(); };
const logo = (cls = "logo") => `<img class="${cls} logo-claro" src="/static/img/logo-vint-global.png" alt="Vint_Global"><img class="${cls} logo-escuro" src="/static/img/logo-vint-global-escuro.png" alt="Vint_Global">`;
const perfilLabel = (p) => (p === "admin" ? "Admin" : "Usuário");

/* ============================================================ layout */
function header(active) {
  const me = S.me, admin = me.perfil === "admin";
  const nav = [["inicio", "#/", "Início"], ["buscas", "#/buscas", "Buscas"], ["base", "#/base", "Base de conhecimento"]];
  return `<header class="app-header"><div class="wrap">
    <a class="brand" href="#/" aria-label="Vint_Global — início">${logo()}</a>
    <nav class="nav" aria-label="Principal">${nav.map(([k, h, l]) => `<a href="${h}" ${k === active ? 'aria-current="page"' : ""}>${l}</a>`).join("")}</nav>
    <div class="user">
      <button type="button" class="user-btn" id="user-btn" aria-haspopup="menu" aria-expanded="false">
        <span class="avatar avatar-sm" aria-hidden="true">${esc(ini(me.nome))}</span>
        <span class="hide-sm" style="font-weight:600;font-size:14px">${esc(me.nome)}</span>
        <span class="chip chip-role">${perfilLabel(me.perfil)}</span>${ic("chevron", "i-sm")}
      </button>
      <div class="menu" id="user-menu" role="menu" hidden>
        <div class="menu-meta"><div class="t-strong">${esc(me.nome)}</div><div class="t-small t-2">${esc(me.email)}</div></div>
        <a role="menuitem" href="#/perfil">${ic("user")}Meu perfil</a>
        ${admin ? `<a role="menuitem" href="#/usuarios">${ic("users")}Usuários</a>` : ""}
        <button type="button" class="toggle" role="menuitemcheckbox" aria-checked="${S.tema === "escuro"}" id="tema-tg">Modo escuro<span class="track" aria-hidden="true"></span></button>
        <button type="button" role="menuitem" id="logout">${ic("logout")}Sair</button>
      </div>
    </div>
  </div></header>`;
}
function bindHeader() {
  const btn = $("#user-btn"), menu = $("#user-menu");
  if (!btn) return;
  btn.onclick = (e) => { e.stopPropagation(); menu.hidden = !menu.hidden; btn.setAttribute("aria-expanded", String(!menu.hidden)); };
  document.addEventListener("click", (e) => { if (!menu.contains(e.target)) { menu.hidden = true; btn.setAttribute("aria-expanded", "false"); } }, { once: true });
  $("#logout").onclick = async () => { await api("/api/auth/logout", { method: "POST" }).catch(() => {}); S.me = null; go("#/login"); };
  $("#tema-tg").onclick = (e) => {
    e.stopPropagation();
    S.tema = S.tema === "escuro" ? "claro" : "escuro"; aplicaTema();
    try { localStorage.setItem("vm_tema", S.tema); } catch (_) { /* ok */ }
    e.currentTarget.setAttribute("aria-checked", String(S.tema === "escuro"));
  };
}
function shell(active, inner) {
  $("#app").innerHTML = `${header(active)}${inner}`;
  bindHeader();
  window.scrollTo(0, 0);
}
function band(inner, extra = "") { return `<div class="bleed band" style="padding-top:32px;padding-bottom:40px;${extra}">${inner}</div>`; }
const crumbs = (items) => `<nav aria-label="Trilha" class="t-small t-2" style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">${items.map(([l, h], i) => (h ? `<a href="${h}">${esc(l)}</a>` : `<span aria-current="page">${esc(l)}</span>`) + (i < items.length - 1 ? '<span aria-hidden="true">›</span>' : "")).join("")}</nav>`;
function errorView(active, e) {
  shell(active, `<main class="wrap-narrow" style="flex:1"><div class="center-box">${ic("alert", "i-lg")}<h1 class="t-h1">Algo deu errado</h1><p class="t-2">${esc(e.message)}</p><a class="btn btn-secondary" href="#/">Voltar ao início</a></div></main>`);
}
function loadingView(active) { shell(active, `<main class="wrap-narrow" style="flex:1"><div class="center-box"><span class="spin"></span><p class="t-2">Carregando…</p></div></main>`); }

/* ============================================================ modal */
function modal(html, onMount) {
  const root = $("#modal-root");
  const prev = document.activeElement;
  root.innerHTML = `<div class="backdrop" id="bd"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="m-title">${html}</div></div>`;
  const close = () => { root.innerHTML = ""; document.removeEventListener("keydown", onKey); if (prev && prev.focus) prev.focus(); };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onKey);
  $("#bd").addEventListener("mousedown", (e) => { if (e.target.id === "bd") close(); });
  $$("[data-close]", root).forEach((b) => (b.onclick = close));
  const f = $("input,button,select,textarea", root); if (f) f.focus();
  if (onMount) onMount(root, close);
  return close;
}
function linkModal(title, texto, link) {
  modal(`<h2 id="m-title" class="t-h1">${esc(title)}</h2><p class="t-2" style="margin-top:8px">${esc(texto)}</p>
    <div class="copy-box" style="margin-top:20px"><input class="input" id="lk" readonly value="${esc(link)}"><button class="btn btn-secondary" id="cp">${ic("copy", "i-sm")}Copiar</button></div>
    <p class="help" style="margin-top:8px">O envio por e-mail ainda não está configurado: copie o link e envie pelo canal corporativo.</p>
    <div class="row" style="justify-content:flex-end;margin-top:24px"><button class="btn btn-primary" data-close>Concluir</button></div>`,
  (root) => { $("#cp", root).onclick = async () => { const i = $("#lk", root); i.select(); try { await navigator.clipboard.writeText(i.value); } catch (_) { document.execCommand("copy"); } toast("Link copiado."); }; });
}

/* ============================================================ senha (componentes) */
const REGRAS = [["12 ou mais caracteres", (p) => p.length >= 12], ["1 letra maiúscula", (p) => /[A-ZÀ-Ý]/.test(p)], ["1 número", (p) => /\d/.test(p)], ["1 símbolo, como ! @ # $", (p) => /[^A-Za-z0-9À-ÿ\s]/.test(p)]];
function regrasHtml(p1, p2) {
  const checks = [...REGRAS.map(([l, f]) => [l, f(p1)]), ["As duas senhas coincidem", p1.length > 0 && p1 === p2]];
  const met = checks.filter((c) => c[1]).length;
  return { met, html: `<ul class="rules" aria-label="Requisitos da senha">${checks.map(([l, ok]) => `<li style="color:${ok ? "var(--ink)" : "var(--ink-2)"};font-weight:${ok ? 500 : 400}">${ok ? `<span class="t-ok">${ic("check")}</span>` : ic("circle")}${l}<span class="sr-only">${ok ? " — atendido" : " — pendente"}</span></li>`).join("")}</ul>`, txt: met === 5 ? "Todos os requisitos atendidos." : `${met} de 5 requisitos atendidos.` };
}
function pwField(id, label, autocomplete = "new-password") {
  return `<div class="field"><label class="label" for="${id}">${label}</label><div class="input-wrap"><input class="input" id="${id}" type="password" autocomplete="${autocomplete}"><button type="button" class="icon-btn" data-eye="${id}" aria-label="Mostrar senha">${ic("eye")}</button></div></div>`;
}
function bindEyes(root = document) {
  $$("[data-eye]", root).forEach((b) => (b.onclick = () => {
    const i = $("#" + b.dataset.eye); const show = i.type === "password"; i.type = show ? "text" : "password";
    b.innerHTML = ic(show ? "eyeoff" : "eye"); b.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
  }));
}

/* ============================================================ 01 · login / setup */
async function pageLogin() {
  let st = { precisa_setup: false, dominio: "vintglobal.com" };
  try { st = await api("/api/auth/estado"); if (st.logado) { S.me = null; return go("#/"); } } catch (_) { /* segue */ }
  const dom = st.dominio ? `nome.sobrenome@${st.dominio}` : "nome.sobrenome@empresa.com";
  const brand = `<aside class="login-brand">${logo("logo logo-lg")}
      <div><h1 class="login-hero">Alocação de talento, <em>em segundos.</em></h1>
      <p class="t-2" style="font-size:17px;line-height:28px;margin-top:24px;max-width:440px">Descreva a demanda do projeto e compare, lado a lado, quem já está na Vint_Global e quem está mapeado no banco iHiring.</p></div>
      <p class="t-small t-2">Uso interno · acesso restrito a gerentes de projeto</p></aside>`;
  if (st.precisa_setup) {
    $("#app").innerHTML = `<div class="login">${brand}<main class="login-form"><div style="width:100%;max-width:420px">
      <p class="t-cap">Primeiro uso</p><h2 class="t-h1" style="margin-top:8px">Crie o administrador</h2>
      <p class="t-2" style="margin-top:8px">Ainda não há usuários. Esta conta poderá convidar o restante do time.</p>
      <form id="f" class="card pad" style="margin-top:24px;display:flex;flex-direction:column;gap:16px" novalidate>
        <div id="err"></div>
        <div class="field"><label class="label" for="nome">Nome completo</label><input class="input" id="nome" autocomplete="name"></div>
        <div class="field"><label class="label" for="email">E-mail corporativo</label><input class="input" id="email" type="email" placeholder="${esc(dom)}" autocomplete="username"></div>
        <div class="field"><label class="label" for="area">Área <span class="opt">(opcional)</span></label><input class="input" id="area" placeholder="Ex.: PMO de Tecnologia"></div>
        ${pwField("p1", "Senha")}${pwField("p2", "Confirmar senha")}
        <div id="rules"></div>
        <button class="btn btn-primary btn-block" id="ok" disabled>Criar e entrar</button>
      </form></div></main></div>`;
    bindEyes();
    const upd = () => { const r = regrasHtml($("#p1").value, $("#p2").value); $("#rules").innerHTML = r.html + `<p class="help">${r.txt}</p>`; $("#ok").disabled = r.met < 5; };
    $("#p1").oninput = upd; $("#p2").oninput = upd; upd();
    $("#f").onsubmit = async (e) => {
      e.preventDefault();
      try { await api("/api/auth/setup", { method: "POST", json: { nome: $("#nome").value, email: $("#email").value, area: $("#area").value, senha: $("#p1").value } }); S.me = null; go("#/"); }
      catch (err) { $("#err").innerHTML = `<div class="alert alert-error" role="alert">${ic("alert")}<p>${esc(err.message)}</p></div>`; }
    };
    return;
  }
  $("#app").innerHTML = `<div class="login">${brand}<div class="login-mhead">${logo()}</div><main class="login-form">
    <div style="width:100%;max-width:420px">
      <h2 class="t-h1">Entrar</h2><p class="t-2" style="margin-top:8px">Use o e-mail corporativo ou o usuário enviado no convite.</p>
      <form id="f" class="card pad" style="margin-top:32px;display:flex;flex-direction:column;gap:20px" novalidate>
        <div id="err" aria-live="assertive"></div>
        <div class="field"><label class="label" for="id">E-mail ou usuário</label><input class="input" id="id" autocomplete="username" placeholder="${esc(dom)}"><div id="id-err"></div></div>
        <div class="field"><label class="label" for="pw">Senha</label><div class="input-wrap"><input class="input" id="pw" type="password" autocomplete="current-password"><button type="button" class="icon-btn" data-eye="pw" aria-label="Mostrar senha">${ic("eye")}</button></div><div id="pw-err"></div></div>
        <div class="between"><label class="check"><input type="checkbox" id="rem" checked> Manter conectado</label><button type="button" class="link-btn t-small" id="forgot" style="font-weight:500">Esqueci minha senha</button></div>
        <button class="btn btn-primary btn-block" id="ok">Entrar</button>
      </form>
      <p class="t-small t-2" style="margin-top:24px">Recebeu um convite por e-mail? Abra o link do convite para definir sua senha.</p>
    </div></main></div>`;
  bindEyes();
  const fe = (id, msg) => { $(`#${id}-err`).innerHTML = msg ? `<p class="err-msg">${ic("alert")}${esc(msg)}</p>` : ""; $("#" + id).setAttribute("aria-invalid", msg ? "true" : "false"); };
  $("#forgot").onclick = () => { $("#err").innerHTML = `<div class="alert alert-info">${ic("info")}<p>Peça a um Admin para redefinir sua senha em <b>Usuários</b>. Você receberá um link válido por 48 horas.</p></div>`; };
  $("#f").onsubmit = async (e) => {
    e.preventDefault();
    const id = $("#id").value.trim(), pw = $("#pw").value;
    fe("id", ""); fe("pw", ""); $("#err").innerHTML = "";
    let bad = false;
    if (!id) { fe("id", "Informe seu e-mail corporativo ou usuário."); bad = true; }
    else if (st.dominio && id.includes("@") && !id.toLowerCase().endsWith("@" + st.dominio)) { fe("id", `Use o e-mail corporativo, terminado em @${st.dominio}.`); bad = true; }
    if (!pw) { fe("pw", "Informe sua senha."); bad = true; }
    if (bad) return;
    const b = $("#ok"); b.disabled = true; b.textContent = "Verificando…";
    try { await api("/api/auth/login", { method: "POST", json: { identificador: id, senha: pw, lembrar: $("#rem").checked } }); S.me = null; go("#/"); }
    catch (err) {
      b.disabled = false; b.textContent = "Entrar"; $("#pw").value = "";
      const d = err.detail || {};
      if (d.codigo === "bloqueado") { $("#err").innerHTML = `<div class="alert alert-error" role="alert">${ic("lock")}<div><p class="t-strong">Conta bloqueada temporariamente</p><p>${esc(d.mensagem)}</p></div></div>`; b.disabled = true; }
      else if (d.codigo === "credenciais") {
        $("#id").setAttribute("aria-invalid", "true"); $("#pw").setAttribute("aria-invalid", "true");
        const left = d.restantes; $("#err").innerHTML = `<div class="alert alert-error" role="alert">${ic("alert")}<div><p class="t-strong">${esc(d.mensagem)}</p>${left !== undefined ? `<p>${left === 1 ? "Resta 1 tentativa antes do bloqueio temporário." : `Restam ${left} tentativas antes do bloqueio temporário.`}</p>` : ""}</div></div>`;
      } else $("#err").innerHTML = `<div class="alert alert-error" role="alert">${ic("alert")}<p>${esc(err.message)}</p></div>`;
    }
  };
}

/* ============================================================ 02 · primeiro acesso / redefinição */
async function pagePrimeiroAcesso(params) {
  const token = params.get("token");
  const top = `<header class="app-header"><div class="wrap">${`<a class="brand" href="#/login">${logo()}</a>`}</div></header>`;
  if (!token) {
    $("#app").innerHTML = `${top}<main class="wrap-narrow" style="flex:1"><div class="center-box">${ic("mail", "i-lg")}<h1 class="t-h1">Use o link do convite</h1><p class="t-2">O link chega do administrador e vale por 48 horas. Se expirou, peça um novo.</p><a class="btn btn-secondary" href="#/login">Ir para o login</a></div></main>`;
    return;
  }
  let info;
  try { info = await api(`/api/auth/convite/${encodeURIComponent(token)}`); }
  catch (e) {
    $("#app").innerHTML = `${top}<main class="wrap-narrow" style="flex:1"><div class="center-box">${ic("alert", "i-lg")}<h1 class="t-h1">Link inválido ou expirado</h1><p class="t-2">${esc(e.message)}</p><a class="btn btn-secondary" href="#/login">Ir para o login</a></div></main>`;
    return;
  }
  const reset = info.tipo === "reset";
  $("#app").innerHTML = `${top}<main class="wrap-narrow" style="flex:1;padding-top:64px;padding-bottom:64px"><div style="max-width:760px;margin:0 auto">
    <p class="t-cap">${reset ? "Redefinição de senha" : "Primeiro acesso"}</p><h1 class="t-display" style="margin-top:8px">${reset ? "Crie uma nova senha" : "Defina sua senha"}</h1>
    <p class="t-2" style="margin-top:12px">${reset ? "Pedido feito" : "Convite enviado"}${info.convidado_por ? ` por ${esc(info.convidado_por)}` : ""} para <b style="color:var(--ink)">${esc(info.email)}</b>. O link expira em ${fmtDate(info.expira_em, true)}.</p>
    <form id="f" class="card" style="margin-top:32px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,300px)" novalidate>
      <div class="pad" style="display:flex;flex-direction:column;gap:20px">${pwField("p1", "Nova senha")}${pwField("p2", "Confirmar senha")}<div id="mm"></div>
        <button class="btn btn-primary btn-block" id="ok" disabled>Definir senha e entrar</button><div id="err"></div>
        <p class="help">Não reutilize senhas de outros sistemas. O administrador nunca vê a sua senha.</p></div>
      <div class="pad" style="background:var(--table-head);border-left:1px solid var(--line);border-radius:0 16px 16px 0;display:flex;flex-direction:column;justify-content:space-between;gap:16px"><div><p class="t-cap">A senha precisa ter</p><div id="rules" style="margin-top:12px"></div></div><p class="t-small t-2" id="met" aria-live="polite"></p></div>
    </form></div></main>`;
  bindEyes();
  const upd = () => {
    const p1 = $("#p1").value, p2 = $("#p2").value, r = regrasHtml(p1, p2);
    $("#rules").innerHTML = r.html; $("#met").textContent = r.txt; $("#ok").disabled = r.met < 5;
    $("#mm").innerHTML = p2.length && p2.length >= p1.length && p1 !== p2 ? `<p class="err-msg">${ic("alert")}As senhas não coincidem.</p>` : "";
  };
  $("#p1").oninput = upd; $("#p2").oninput = upd; upd();
  $("#f").onsubmit = async (e) => {
    e.preventDefault();
    try { await api("/api/auth/definir-senha", { method: "POST", json: { token, senha: $("#p1").value } }); S.me = null; history.replaceState(null, "", "#/"); toast("Senha definida. Bem-vindo(a)!"); render(); }
    catch (err) { $("#err").innerHTML = `<div class="alert alert-error">${ic("alert")}<p>${esc(err.message)}</p></div>`; }
  };
}

/* ============================================================ status de busca */
function statusBusca(st, n) {
  if (st === "confirmada") return `<span class="status s-ok">${ic("check")}Alocação confirmada${n ? ` · ${n} pessoa${n === 1 ? "" : "s"}` : ""}</span>`;
  if (st === "rascunho") return `<span class="status s-muted">${ic("pencil")}Rascunho</span>`;
  return `<span class="status s-muted">${ic("clock")}Aguardando decisão</span>`;
}
const buscaHref = (b) => (b.status === "rascunho" ? `#/buscas/nova?de=${b.id}` : `#/buscas/${b.id}`);
function tabelaBuscas(rows, comAutor = false) {
  if (!rows.length) return `<div class="empty-box">${ic("info")}<div><p class="t-strong">Nenhuma busca ainda.</p><p class="t-2">Comece por “Nova busca”: descreva o projeto e o ranking sai em segundos.</p></div></div>`;
  return `<div class="table-box"><table class="table"><thead><tr><th>Projeto</th><th>Data</th>${comAutor ? "<th>Autor</th>" : ""}<th>Status</th><th style="width:56px"><span class="sr-only">Editar</span></th></tr></thead><tbody>
    ${rows.map((b) => `<tr><td><a class="row-link" href="${buscaHref(b)}">${esc(b.nome)}</a><div class="t-small t-2">${esc(b.skills.slice(0, 4).join(" · "))}</div></td>
      <td class="t-num">${fmtDate(b.criado_em)}</td>${comAutor ? `<td>${esc(b.autor || "—")}</td>` : ""}<td>${statusBusca(b.status, b.n_alocados)}</td><td style="text-align:right"><a class="icon-btn" href="#/buscas/nova?de=${b.id}" title="Editar projeto" aria-label="Editar o projeto ${esc(b.nome)}">${ic("pencil")}</a></td></tr>`).join("")}
  </tbody></table></div>`;
}

/* ============================================================ 03 · dashboard */
async function pageDashboard() {
  loadingView("inicio");
  let d; try { d = await api("/api/dashboard"); } catch (e) { return errorView("inicio", e); }
  const first = S.me.nome.split(" ")[0];
  const pend = d.minhas_pendentes;
  const sub = pend.length ? `${pend.length === 1 ? "Uma busca aguarda" : `${pend.length === 2 ? "Duas" : pend.length} buscas aguardam`} sua decisão: ${pend.map((b) => `<a href="#/buscas/${b.id}">${esc(b.nome)}</a>`).join(" e ")}.` : "Nenhuma busca sua aguardando decisão. Que tal começar uma nova?";
  const dec = d.ultimas_decisoes.length ? d.ultimas_decisoes.map((x) => `<li><p><span class="t-strong">${nm(x.candidato)}</span> ${x.origem === "ihiring" ? "selecionado(a) via iHiring" : x.remanejamento ? "realocado(a)" : "selecionado(a)"} para <a href="#/buscas/${x.busca_id}">${esc(x.projeto)}</a>${x.percentual ? ` (${x.percentual}%)` : ""}.</p><p class="t-small t-2" style="margin-top:4px">${fmtDate(x.criado_em).slice(0, 6)} · ${x.por_voce ? "por você" : `por ${esc(x.autor || "—")}`}</p></li>`).join("") : `<li class="t-2">Nenhuma decisão registrada ainda.</li>`;
  shell("inicio", `<main class="wrap" style="flex:1;padding-bottom:96px">
    ${band(`<p class="t-small t-2 t-num" style="padding-bottom:24px;border-bottom:1px solid var(--line)"><b style="color:var(--ink)">${d.projetos_abertos}</b> ${d.projetos_abertos === 1 ? "projeto" : "projetos"} em aberto · <b style="color:var(--ink)">${d.talentos_disponiveis}</b> talentos 100% disponíveis em ${esc(d.mes_referencia)} · <b style="color:var(--ink)">${d.remanejamentos}</b> ${d.remanejamentos === 1 ? "remanejamento" : "remanejamentos"} em análise</p>
      <h1 class="t-display" style="font-size:48px;line-height:56px;font-weight:900;margin-top:56px">Olá, ${esc(first)}</h1><p class="t-2" style="font-size:18px;line-height:28px;margin-top:12px">${sub}</p>`, "padding-bottom:120px;padding-top:24px")}
    <div class="dash-grid">
      <section class="card pad" aria-labelledby="nb"><p class="t-cap">Nova busca</p><h2 id="nb" class="t-h1" style="font-size:30px;line-height:38px;margin-top:12px">Descreva o projeto</h2>
        <p class="t-2" style="margin-top:12px;max-width:540px">Escopo, skills e prazo. O sistema cruza com o histórico dos colaboradores Vint_Global e com o banco iHiring e devolve um ranking em menos de um minuto.</p>
        <div style="margin-top:24px;padding:20px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)"><p class="t-cap">Exemplo de descrição</p><p style="margin-top:8px">“Sustentação do portal de serviços de uma secretaria estadual em Laravel + Vue.js, banco PostgreSQL, Kanban, 4 meses a partir de dezembro, 80% de dedicação.”</p></div>
        <div class="row stack-sm" style="margin-top:24px;gap:16px"><a class="btn btn-primary" href="#/buscas/nova" style="min-height:48px;padding:0 24px">Iniciar busca ${ic("arrow")}</a><span class="t-small t-2">Você também pode anexar o briefing em PDF ou DOCX.</span></div>
      </section>
      <aside style="padding-top:104px" aria-labelledby="ud"><p id="ud" class="t-cap">Últimas decisões</p><ul class="dash-dec" style="margin-top:12px">${dec}</ul></aside>
    </div>
    <section style="margin-top:64px" aria-labelledby="br"><div class="between" style="margin-bottom:16px"><h2 id="br" class="t-h2">Buscas recentes</h2><a href="#/buscas">Ver todas</a></div>${tabelaBuscas(d.buscas_recentes)}</section>
  </main>`);
}

/* ============================================================ buscas (lista) */
async function pageBuscas() {
  loadingView("buscas");
  let rows; try { rows = await api("/api/buscas"); } catch (e) { return errorView("buscas", e); }
  shell("buscas", `<main class="wrap" style="flex:1;padding-bottom:96px">
    ${band(`<div class="between"><div><h1 class="t-display">Buscas</h1><p class="t-2" style="margin-top:8px">${rows.length} busca(s) do time · ${rows.filter((b) => b.status === "aguardando").length} aguardando decisão</p></div><a class="btn btn-primary" href="#/buscas/nova">${ic("plus")}Nova busca</a></div>`)}
    <div class="field" style="margin:32px 0 16px;max-width:420px"><label class="label" for="bq">Filtrar</label><div style="position:relative">${ic("search", "i-sm").replace('class="i', 'style="position:absolute;left:12px;top:14px;color:var(--ink-2)" class="i')}<input id="bq" class="input" type="search" placeholder="Projeto, skill ou autor" style="padding-left:36px"></div></div>
    <div id="tb">${tabelaBuscas(rows, true)}</div></main>`);
  $("#bq").oninput = (e) => { const q = fold(e.target.value); $("#tb").innerHTML = tabelaBuscas(rows.filter((b) => fold(`${b.nome} ${b.skills.join(" ")} ${b.autor}`).includes(q)), true); };
}

/* ============================================================ 04 · nova busca */
const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const INI_ATALHOS = { "Imediato": 0, "Em 15 dias": 15, "Em 30 dias": 30, "Em 60 dias": 60 };
function dataInicio(v) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(v || "")) return v;
  const br = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(v || ""); if (br) return `${br[3]}-${br[2].padStart(2, "0")}-${br[1].padStart(2, "0")}`;
  const d = new Date(); d.setDate(d.getDate() + (INI_ATALHOS[v] ?? 15)); return isoLocal(d);
}
function fmtDia(iso) { if (!iso) return ""; const [y, m, d] = iso.split("-").map(Number); return `${String(d).padStart(2, "0")} ${MES[m - 1]} ${y}`; }
const FORM0 = () => ({ nome: "", descricao: "", skills: [], duracao: "3–6 meses", inicio: dataInicio("Em 15 dias"), disponibilidade_min: 50, senioridades: [], tipo_servico: null, metodologia: null, nivel: "", usar_ia: true, briefing_nome: null, briefing_texto: null, file: null });
let F = FORM0();
let marcaAtalhosAtual = null;
function sugestoes() {
  if (!S.meta) return [];
  const txt = fold(F.descricao), have = new Set(F.skills.map((s) => fold(s.nome)));
  const out = [];
  for (const nome of S.meta.catalogo) {
    const k = fold(nome);
    if (have.has(k) || out.length >= 6) continue;
    if (k.length <= 2 && !["c#", "c++"].includes(k)) continue;
    const base = k.replace(/\s*\(.*\)\s*/, "").trim(); // "Laravel (PHP)" também casa com "laravel"
    const hit = [k, base].filter((x) => x.length > 2 || ["c#", "c++"].includes(x)).some((x) => new RegExp(`(^|[^a-z0-9#+])${x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}($|[^a-z0-9#+])`).test(txt));
    if (hit && !out.some((o) => fold(o).replace(/\s*\(.*\)\s*/, "") === base)) out.push(nome);
  }
  return out;
}
function renderResumo() { clearTimeout(F._pv); F._pv = setTimeout(carregarPrevia, 350); if ($("#sum")) $("#sum").classList.add("is-loading"); }
async function carregarPrevia() {
  const el = $("#prev"); if (!el) return;
  const seq = (F._pvSeq = (F._pvSeq || 0) + 1);
  let x;
  try { x = await api("/api/buscas/previa", { method: "POST", json: { skills: F.skills, duracao: F.duracao, inicio: F.inicio, disponibilidade_min: F.disponibilidade_min, senioridades: F.senioridades, tipo_servico: F.tipo_servico, metodologia: F.metodologia } }); }
  catch (_) { return; }
  if (seq !== F._pvSeq || !$("#prev")) return;
  const ed = $("#e-dur"); if (ed) ed.innerHTML = x.duracao_entendida ? "" : `<p class="err-msg">${ic("alert")}Não entendi a duração. Ex.: 4 meses, 10 semanas ou 30/06/2027.</p>`;
  const linha = (dt, dd) => `<div><dt>${dt}</dt><dd class="t-num">${dd}</dd></div>`;
  const pl = (n, um, varios) => `${n} ${n === 1 ? um : varios}`;
  let h = linha("Término previsto", `${fmtDia(x.fim)} <span class="t-2" style="font-weight:400">(${pl(x.meses, "mês", "meses")})</span>`);
  if (x.tem_skills) {
    h += linha("Atendem às skills obrigatórias", pl(x.aptos, "colaborador", "colaboradores"))
      + linha("Livres no período todo", `${x.disponiveis} de ${x.aptos}`)
      + linha("Precisariam de remanejamento", x.remanejamento)
      + linha("Próximos do ideal (PDI)", x.quase_la)
      + linha("Talentos compatíveis no iHiring", x.externos);
  }
  let notas = "";
  if (!x.tem_skills) notas += `<p class="prev-note">${ic("info", "i-sm")}Adicione skills para ver quantas pessoas atendem.</p>`;
  if (x.sem_ninguem?.length) notas += `<p class="prev-note warn">${ic("warn", "i-sm")}Ninguém no SGD tem ${esc(x.sem_ninguem.join(", "))} — vale olhar o iHiring ou PDI.</p>`;
  if (x.fora_catalogo?.length) notas += `<p class="prev-note warn">${ic("warn", "i-sm")}Fora do catálogo do SGD: ${esc(x.fora_catalogo.join(", "))}.</p>`;
  if (x.alem_planejamento) notas += `<p class="prev-note">${ic("info", "i-sm")}O planejamento do SGD vai até ${esc(x.horizonte)}; depois disso as pessoas aparecem livres.</p>`;
  el.innerHTML = `<dl class="sum-list" id="sum" style="margin-top:8px">${h}</dl>${notas}`;
}
function renderChips() {
  $("#chips").innerHTML = F.skills.map((s, i) => `<li class="chip chip-rm ${s.obrigatoria ? "" : "desej"}"><button type="button" class="chip-lbl" data-tg="${i}" title="Clique para alternar obrigatória/desejável" aria-label="${esc(s.nome)}, ${s.obrigatoria ? "obrigatória" : "desejável"}. Alternar">${esc(s.nome)}</button><button type="button" data-rm="${i}" aria-label="Remover ${esc(s.nome)}">${ic("x", "i-sm")}</button></li>`).join("");
  const sg = sugestoes();
  $("#sugg").innerHTML = sg.length ? `<span class="t-small t-2">Citadas na descrição:</span>${sg.map((n) => `<button type="button" class="sugg" data-add="${esc(n)}">${ic("plus", "i-sm")}${esc(n)}</button>`).join("")}` : "";
  renderResumo();
}
function addSkill(raw, obrig = true) {
  const v = (raw || "").trim().replace(/,$/, ""); if (!v) return;
  const canon = S.meta.catalogo.find((c) => fold(c) === fold(v)) || v;
  if (F.skills.some((s) => fold(s.nome) === fold(canon))) return;
  if (!S.meta.catalogo.includes(canon)) toast(`“${canon}” não está no catálogo do SGD — vai aparecer como lacuna (PDI ou iHiring).`);
  F.skills.push({ nome: canon, obrigatoria: obrig, nivel: F.nivel || "basico" }); setErr("skills", ""); renderChips();
}
function setErr(campo, msg) {
  const el = $(`#e-${campo}`); if (!el) return;
  el.innerHTML = msg ? `<p class="err-msg">${ic("alert")}${esc(msg)}</p>` : "";
  const inp = { nome: "#f-nome", descricao: "#f-desc", skills: "#skill-in" }[campo]; if (inp) $(inp).setAttribute("aria-invalid", msg ? "true" : "false");
}
function opt(list, cur) { return list.map((v) => `<option ${v === cur ? "selected" : ""}>${esc(v)}</option>`).join(""); }
async function pageNovaBusca(params, manter = false) {
  if (!manter) F = FORM0();
  const de = manter ? null : params.get("de");
  if (de) {
    try {
      const b = await api(`/api/buscas/${de}`); const p = b.params;
      Object.assign(F, { nome: p.nome || b.nome, descricao: p.descricao || "", skills: p.skills || [], duracao: p.duracao || F.duracao, inicio: dataInicio(p.inicio || F.inicio), disponibilidade_min: p.disponibilidade_min ?? 50, senioridades: p.senioridades || [], tipo_servico: p.tipo_servico, metodologia: p.metodologia, briefing_nome: p.briefing_nome, briefing_hash: p.briefing_hash || null });
      F.busca_id = b.id;
      F.n_alocados = (b.decisoes || []).length;
      F.autor_id = b.usuario_id;
    } catch (e) { toast(e.message); }
  }
  const m = S.meta;
  shell("buscas", `<main class="wrap" style="flex:1;padding-bottom:96px" id="nb-main">
    ${band(`${crumbs([["Buscas", "#/buscas"], [F.busca_id ? "Editar projeto" : "Nova busca"]])}<h1 class="t-display" style="margin-top:24px">${F.busca_id ? "Editar projeto" : "Nova busca"}</h1><p class="t-2" style="margin-top:8px;max-width:560px">Descreva a demanda como explicaria para outro gerente. O ranking considera skills, projetos anteriores e alocação atual.</p>`)}
    <div class="form-grid" style="margin-top:48px">
      <form id="f" novalidate>
        ${F.n_alocados ? `<div class="alert alert-info" style="margin-bottom:24px">${ic("info")}<p>Este projeto já tem <b>${F.n_alocados} pessoa${F.n_alocados === 1 ? "" : "s"} alocada${F.n_alocados === 1 ? "" : "s"}</b>. Ao gerar de novo, elas continuam no projeto e são reavaliadas com os novos critérios.</p></div>` : ""}
        <div id="err-sum"></div>
        <section class="fsec" aria-labelledby="s1"><div class="fsec-h"><span class="n">01</span><h2 id="s1" class="t-h2">Sobre o projeto</h2></div>
          <div class="field"><label class="label" for="f-nome">Nome do projeto</label><input class="input" id="f-nome" value="${esc(F.nome)}" placeholder="Ex.: Portal de serviços SEFAZ"><div id="e-nome"></div></div>
          <div class="field"><div class="between"><label class="label" for="f-desc">Descrição da demanda</label><span class="t-small t-2 t-num" id="cnt"></span></div>
            <textarea class="textarea" id="f-desc" placeholder="Objetivo, stack atual, restrições, prazos…">${esc(F.descricao)}</textarea><div id="e-descricao"></div>
            <p class="help">Inclua objetivo, stack atual e restrições. Nomes de sistemas e prazos melhoram o ranking.</p></div>
        </section>
        <section class="fsec" aria-labelledby="s2"><div class="fsec-h"><span class="n">02</span><h2 id="s2" class="t-h2">Skills necessárias</h2></div>
          <div class="field"><label class="label" for="skill-in">Adicionar skill</label><ul class="chips" id="chips" aria-label="Skills adicionadas"></ul>
            <input class="input" id="skill-in" list="cat" placeholder="Digite e pressione Enter — ex.: PostgreSQL"><datalist id="cat">${m.catalogo.map((c) => `<option value="${esc(c)}">`).join("")}</datalist>
            <div id="e-skills"></div><p class="help">Enter adiciona · Backspace com o campo vazio remove a última · clique na skill para marcar como desejável.</p></div>
          <div class="chips" id="sugg" style="align-items:center;gap:8px"></div>
        </section>
        <section class="fsec" aria-labelledby="s3"><div class="fsec-h"><span class="n">03</span><h2 id="s3" class="t-h2">Tempo e disponibilidade</h2></div>
          <div class="grid2 grid-sm-1" style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
            <div class="field"><label class="label" for="f-dur">Duração estimada</label><input class="input" id="f-dur" value="${esc(F.duracao)}" placeholder="Ex.: 4 meses, 10 semanas ou 30/06/2027" autocomplete="off">
              <div class="quick" id="q-dur" aria-label="Atalhos de duração">${m.duracoes.map((d) => `<button type="button" class="sugg" data-dur="${esc(d)}" aria-pressed="${d === F.duracao}">${esc(d)}</button>`).join("")}</div><div id="e-dur"></div></div>
            <div class="field"><label class="label" for="f-ini">Início desejado</label><input type="date" class="input" id="f-ini" value="${esc(dataInicio(F.inicio))}">
              <div class="quick" id="q-ini" aria-label="Atalhos de início">${Object.keys(INI_ATALHOS).map((d) => `<button type="button" class="sugg" data-ini="${esc(d)}" aria-pressed="${dataInicio(d) === dataInicio(F.inicio)}">${esc(d)}</button>`).join("")}</div></div></div>
          <div class="field"><div class="between"><label class="label" for="f-disp">Disponibilidade mínima por pessoa</label><span class="t-strong t-num" id="disp-v">${F.disponibilidade_min}%</span></div>
            <input type="range" class="range" id="f-disp" min="20" max="100" step="10" value="${F.disponibilidade_min}"><div class="between t-small t-2"><span>20%</span><span>100%</span></div>
            <p class="help">Quem não tem esse percentual livre em algum mês entra com o selo de remanejamento — você decide se vale liberar.</p></div>
        </section>
        <section class="fsec" aria-labelledby="s4"><details class="adv" ${F.senioridades.length || F.tipo_servico || F.metodologia ? "open" : ""}><summary id="s4"><span class="n" style="font-size:13px;color:var(--primary);font-weight:500">04</span> Ajustes finos (opcional) ${ic("chevron", "i-sm")}</summary>
          <div style="display:flex;flex-direction:column;gap:20px;margin-top:12px">
            <div class="field"><span class="label">Senioridade</span><div class="chips" id="sens">${m.senioridades.map((s) => `<label class="check" style="min-height:36px;margin-right:12px"><input type="checkbox" value="${esc(s)}" ${F.senioridades.includes(s) ? "checked" : ""}> ${esc(s)}</label>`).join("")}</div></div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px" class="grid-sm-1">
              <div class="field"><label class="label" for="f-tipo">Tipo de serviço</label><input class="input" id="f-tipo" list="dl-tipo" value="${esc(F.tipo_servico || "")}" placeholder="Qualquer" autocomplete="off"><datalist id="dl-tipo">${m.tipos_servico.map((v) => `<option value="${esc(v)}">`).join("")}</datalist></div>
              <div class="field"><label class="label" for="f-met">Metodologia</label><input class="input" id="f-met" list="dl-met" value="${esc(F.metodologia || "")}" placeholder="Qualquer" autocomplete="off"><datalist id="dl-met">${m.metodologias.map((v) => `<option value="${esc(v)}">`).join("")}</datalist></div>
              <div class="field"><label class="label" for="f-niv">Nível mínimo das skills</label><input class="input" id="f-niv" list="dl-niv" value="${esc(F.nivel || "")}" placeholder="Básico" autocomplete="off"><datalist id="dl-niv"><option value="Básico"><option value="Intermediário"><option value="Avançado"></datalist></div></div>
            <p class="help" style="margin-top:-8px">Nos três campos acima, escolha da lista ou digite outro valor.</p>
            ${m.ia_ativa ? `<button type="button" class="toggle" role="switch" aria-checked="${F.usar_ia}" id="f-ia"><span class="track" aria-hidden="true"></span>Refinar ranking com IA</button>` : ""}
          </div></details></section>
        <div class="row stack-sm" style="gap:12px;padding-top:32px;border-top:1px solid var(--line)"><button class="btn btn-primary" id="go" style="min-height:48px;padding:0 24px">${F.busca_id ? "Salvar e gerar de novo" : "Gerar matchmaking"}</button><button type="button" class="btn btn-ghost" id="draft">Salvar rascunho</button><button type="button" class="btn btn-ghost" id="clear">Limpar</button>
          ${F.busca_id && (F.autor_id === S.me.id || S.me.perfil === "admin") ? `<button type="button" class="btn btn-ghost-danger" id="del-proj" style="margin-left:auto">${ic("trash", "i-sm")}Excluir projeto</button>` : ""}</div>
      </form>
      <aside style="display:flex;flex-direction:column;gap:32px">
        <div class="field"><span class="label">Briefing <span class="opt">(opcional)</span></span><div id="brief"></div><div id="brief-err"></div>
          <p class="help">O texto do arquivo complementa a descrição e preenche os campos; você revisa antes de gerar.</p></div>
        <div><p class="t-cap">Prévia da busca</p><div id="prev" aria-live="polite"><dl class="sum-list is-loading" id="sum" style="margin-top:8px"><div><dt>Calculando…</dt><dd></dd></div></dl></div></div>
      </aside>
    </div></main>`);
  const cnt = () => ($("#cnt").textContent = `${$("#f-desc").value.length} caracteres`);
  cnt(); renderChips(); renderBrief();
  $("#f-nome").oninput = (e) => { F.nome = e.target.value; setErr("nome", ""); };
  $("#f-desc").oninput = (e) => { F.descricao = e.target.value; cnt(); setErr("descricao", ""); clearTimeout(F._t); F._t = setTimeout(renderChips, 250); };
  const si = $("#skill-in");
  si.onkeydown = (e) => {
    if (e.key === "Enter") { e.preventDefault(); addSkill(si.value); si.value = ""; }
    else if (e.key === "Backspace" && !si.value && F.skills.length) { F.skills.pop(); renderChips(); }
  };
  si.oninput = () => { if (si.value.endsWith(",")) { addSkill(si.value); si.value = ""; } else if (S.meta.catalogo.includes(si.value)) { addSkill(si.value); si.value = ""; } };
  $("#chips").onclick = (e) => {
    const rm = e.target.closest("[data-rm]"), tg = e.target.closest("[data-tg]");
    if (rm) { const [x] = F.skills.splice(+rm.dataset.rm, 1); if (x && F._removidas) F._removidas.add(fold(x.nome)); renderChips(); si.focus(); }
    if (tg) { const s = F.skills[+tg.dataset.tg]; s.obrigatoria = !s.obrigatoria; renderChips(); }
  };
  $("#sugg").onclick = (e) => { const b = e.target.closest("[data-add]"); if (b) addSkill(b.dataset.add); };
  const marcaAtalhos = () => {
    $$("#q-dur [data-dur]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.dur === F.duracao)));
    $$("#q-ini [data-ini]").forEach((b) => b.setAttribute("aria-pressed", String(dataInicio(b.dataset.ini) === F.inicio)));
  };
  marcaAtalhosAtual = marcaAtalhos;
  $("#f-dur").oninput = (e) => { F.duracao = e.target.value.trim(); marcaAtalhos(); renderResumo(); };
  $("#q-dur").onclick = (e) => { const b = e.target.closest("[data-dur]"); if (!b) return; F.duracao = b.dataset.dur; $("#f-dur").value = F.duracao; marcaAtalhos(); renderResumo(); };
  $("#f-ini").onchange = (e) => { F.inicio = e.target.value || dataInicio("Em 15 dias"); marcaAtalhos(); renderResumo(); };
  $("#q-ini").onclick = (e) => { const b = e.target.closest("[data-ini]"); if (!b) return; F.inicio = dataInicio(b.dataset.ini); $("#f-ini").value = F.inicio; marcaAtalhos(); renderResumo(); };
  $("#f-disp").oninput = (e) => { F.disponibilidade_min = +e.target.value; $("#disp-v").textContent = `${F.disponibilidade_min}%`; renderResumo(); };
  $("#sens").onchange = () => { F.senioridades = $$("#sens input:checked").map((c) => c.value); renderResumo(); };
  $("#f-tipo").oninput = (e) => { F.tipo_servico = e.target.value.trim() || null; renderResumo(); };
  $("#f-met").oninput = (e) => { F.metodologia = e.target.value.trim() || null; renderResumo(); };
  $("#f-niv").oninput = (e) => { F.nivel = e.target.value.trim(); F.skills.forEach((s) => (s.nivel = F.nivel || "basico")); renderResumo(); };
  if ($("#f-ia")) $("#f-ia").onclick = (e) => { F.usar_ia = !F.usar_ia; e.currentTarget.setAttribute("aria-checked", String(F.usar_ia)); renderResumo(); };
  $("#clear").onclick = () => { const keep = F.busca_id; F = FORM0(); F.busca_id = keep; pageNovaBuscaRefill(); };
  $("#draft").onclick = () => enviar(true);
  if ($("#del-proj")) $("#del-proj").onclick = () => confirmarExclusao(F.busca_id, F.nome || "este projeto", F.n_alocados || 0);
  $("#f").onsubmit = (e) => { e.preventDefault(); enviar(false); };
}
function confirmarExclusao(id, nome, nAloc) {
  modal(`<div class="row" style="gap:12px;align-items:flex-start"><span class="t-err" style="margin-top:4px">${ic("warn", "i-lg")}</span><div>
      <h2 id="m-title" class="t-h1">Tem certeza disso?</h2>
      <p class="t-2" style="margin-top:8px">O projeto <b style="color:var(--ink)">${esc(nome)}</b>${nAloc ? ` e as <b style="color:var(--ink)">${nAloc} alocaç${nAloc === 1 ? "ão" : "ões"}</b> registrada${nAloc === 1 ? "" : "s"} nele` : ""} ser${nAloc ? "ão" : "á"} excluído${nAloc ? "s" : ""}. Essa ação não pode ser desfeita.</p>
      <p class="t-small t-2" style="margin-top:8px">Os dados do SGD não são alterados.</p></div></div>
    <div class="row" style="justify-content:flex-end;gap:8px;margin-top:28px"><button type="button" class="btn btn-ghost" data-close>Cancelar</button><button type="button" class="btn btn-danger" id="del-ok">Sim, excluir</button></div>`,
  (root, close) => {
    $("#del-ok", root).onclick = async () => {
      const b = $("#del-ok", root); b.disabled = true; b.textContent = "Excluindo…";
      try { await api(`/api/buscas/${id}`, { method: "DELETE" }); close(); CUR = null; toast(`Projeto “${nome}” excluído.`); go("#/buscas"); }
      catch (e) { close(); toast(e.message); }
    };
  });
}
function pageNovaBuscaRefill() {
  $("#f-nome").value = ""; $("#f-desc").value = ""; $("#cnt").textContent = "0 caracteres";
  $("#f-dur").value = F.duracao; $("#f-ini").value = F.inicio; $("#f-disp").value = 50; $("#disp-v").textContent = "50%";
  $$("#sens input").forEach((c) => (c.checked = false)); $("#f-tipo").value = ""; $("#f-met").value = ""; $("#f-niv").value = ""; if (marcaAtalhosAtual) marcaAtalhosAtual(); $("#e-dur").innerHTML = "";
  ["nome", "descricao", "skills"].forEach((c) => setErr(c, "")); $("#err-sum").innerHTML = ""; renderChips(); renderBrief();
}
function renderBrief() {
  const el = $("#brief");
  if (F.briefing_nome) {
    el.innerHTML = `<div class="card file-card">${ic("file")}<div style="flex:1;min-width:0"><p class="t-strong" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(F.briefing_nome)}</p><p class="t-small t-2">${esc(F.file_info || "enviado")}</p></div><button type="button" class="icon-btn" id="rm-brief" aria-label="Remover briefing">${ic("trash")}</button></div>`;
    $("#rm-brief").onclick = () => { F.briefing_nome = null; F.briefing_texto = null; F.file_info = null; F.briefing_hash = null; renderBrief(); };
    return;
  }
  el.innerHTML = `<label class="dropzone" id="dz">${ic("upload", "i-lg")}<span style="font-size:14px"><b>Arraste o PDF ou DOCX</b> ou clique para escolher</span><span class="help">Até 10 MB · preenche o formulário na hora</span><input type="file" id="file" accept=".pdf,.docx,.txt,.md"></label>`;
  const dz = $("#dz");
  ["dragover", "dragenter"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("is-over"); }));
  ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, () => dz.classList.remove("is-over")));
  dz.addEventListener("drop", (e) => { e.preventDefault(); lerBriefing(e.dataTransfer.files[0]); });
  $("#file").onchange = (e) => lerBriefing(e.target.files[0]);
}
const durPorMeses = (n) => `${n} ${n === 1 ? "mês" : "meses"}`;
function iniPorMes(aaaamm) {
  const hoje = new Date(), [y, mm] = aaaamm.split("-").map(Number);
  if (y < hoje.getFullYear() || (y === hoje.getFullYear() && mm <= hoje.getMonth() + 1)) return isoLocal(hoje);
  return `${y}-${String(mm).padStart(2, "0")}-01`;
}
// aplica o que veio do briefing; com "so_se_auto", só mexe em campos que o usuário ainda não alterou
function aplicarBriefing(x, soSeAuto) {
  const A = F._auto || (F._auto = {});
  const pode = (campo, atual) => !soSeAuto || atual === A[campo] || atual == null || atual === "";
  let novas = 0;
  if (x.texto && (soSeAuto ? F.descricao === A.descricao : !F.descricao.trim())) { F.descricao = x.texto; A.descricao = x.texto; $("#f-desc").value = F.descricao; $("#cnt").textContent = `${F.descricao.length} caracteres`; }
  (x.skills || []).forEach((sk) => {
    if ((F._removidas || new Set()).has(fold(sk.nome))) return;
    if (!F.skills.some((k) => fold(k.nome) === fold(sk.nome))) { F.skills.push({ nome: sk.nome, obrigatoria: sk.obrigatoria, nivel: sk.nivel }); novas++; }
  });
  if (x.duracao_meses && pode("duracao", F.duracao)) { F.duracao = durPorMeses(x.duracao_meses); A.duracao = F.duracao; $("#f-dur").value = F.duracao; }
  if (x.inicio && pode("inicio", F.inicio)) { F.inicio = iniPorMes(x.inicio); A.inicio = F.inicio; $("#f-ini").value = F.inicio; }
  if (x.disponibilidade_min && pode("disp", F.disponibilidade_min)) { F.disponibilidade_min = Math.max(20, Math.min(100, Math.round(x.disponibilidade_min / 10) * 10)); A.disp = F.disponibilidade_min; $("#f-disp").value = F.disponibilidade_min; $("#disp-v").textContent = `${F.disponibilidade_min}%`; }
  if (x.senioridades?.length && (!soSeAuto || !F.senioridades.length || F.senioridades === A.sens)) { F.senioridades = x.senioridades; A.sens = F.senioridades; $$("#sens input").forEach((c) => (c.checked = F.senioridades.includes(c.value))); }
  if (x.tipo_servico && pode("tipo", F.tipo_servico)) { F.tipo_servico = x.tipo_servico; A.tipo = x.tipo_servico; $("#f-tipo").value = x.tipo_servico; }
  if (x.metodologia && pode("met", F.metodologia)) { F.metodologia = x.metodologia; A.met = x.metodologia; $("#f-met").value = x.metodologia; }
  if (x.senioridades?.length || x.tipo_servico || x.metodologia) $("details.adv").open = true;
  if (marcaAtalhosAtual) marcaAtalhosAtual();
  renderChips(); setErr("skills", ""); setErr("descricao", "");
  return novas;
}
async function lerBriefing(file) {
  if (!file) return;
  $("#brief-err").innerHTML = "";
  if (!/\.(pdf|docx|txt|md)$/i.test(file.name)) { $("#brief-err").innerHTML = `<p class="err-msg">${ic("alert")}“${esc(file.name)}” não é PDF nem DOCX. Exporte o briefing nesses formatos e envie de novo.</p>`; return; }
  if (file.size > 10 * 1024 * 1024) { $("#brief-err").innerHTML = `<p class="err-msg">${ic("alert")}O arquivo passa de 10 MB. Reduza imagens ou divida o documento.</p>`; return; }
  $("#brief").innerHTML = `<div class="card file-card"><span class="spin"></span><div><p class="t-strong">${esc(file.name)}</p><p class="t-small t-2">Lendo o arquivo…</p></div></div>`;
  // 1ª leitura: regras (instantânea). A IA complementa em segundo plano, sem travar o formulário.
  const fd = new FormData(); fd.append("arquivo", file); fd.append("usar_ia", "false");
  if (F.busca_id) fd.append("ignorar_id", String(F.busca_id));
  let x;
  try { x = await api("/api/extract", { method: "POST", body: fd }); }
  catch (e) {
    renderBrief();
    const id = e.detail && e.detail.busca_id;
    $("#brief-err").innerHTML = `<p class="err-msg">${ic("alert")}<span>${esc(e.message)}${id ? ` <a href="#/buscas/${id}">Abrir a busca existente</a>` : ""}</span></p>`;
    return;
  }
  const mb = file.size / 1048576, tam = mb >= 1 ? mb.toFixed(1).replace(".", ",") + " MB" : Math.max(1, Math.round(file.size / 1024)) + " KB";
  F.briefing_nome = file.name; F.briefing_texto = x.texto_completo || null; F.briefing_hash = x.briefing_hash || null;
  F._auto = {}; F._removidas = new Set();
  const refinar = F.usar_ia && S.meta.ia_ativa && x.texto_completo;
  F.file_info = refinar ? `${tam} · campos preenchidos · refinando…` : `${tam} · campos preenchidos`;
  if (!F.nome) { F.nome = file.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").replace(/\bexemplo\b/i, "").trim(); $("#f-nome").value = F.nome; }
  aplicarBriefing(x, false); renderBrief();
  toast(`Briefing lido: ${x.skills.length} skill${x.skills.length === 1 ? "" : "s"} encontrada${x.skills.length === 1 ? "" : "s"}${x.skills_fora_catalogo?.length ? `; fora do catálogo: ${x.skills_fora_catalogo.join(", ")}` : ""}. Revise antes de gerar.`, 6000);
  if (!refinar) return;
  const hash = F.briefing_hash, fd2 = new FormData(); fd2.append("texto", x.texto_completo); fd2.append("usar_ia", "true");
  try {
    const y = await api("/api/extract", { method: "POST", body: fd2 });
    if (F.briefing_hash !== hash || !$("#f-desc")) return; // trocou de arquivo ou saiu da tela
    if (y.origem === "ia") { const n = aplicarBriefing(y, true); if (n) toast(`Briefing refinado: +${n} skill${n === 1 ? "" : "s"}.`); }
  } catch (_) { /* fica o que as regras encontraram */ }
  if (F.briefing_hash === hash && $("#brief")) { F.file_info = `${tam} · campos preenchidos`; renderBrief(); }
}
async function enviar(rascunho) {
  const body = { nome: F.nome.trim(), descricao: F.descricao, skills: F.skills, duracao: F.duracao, inicio: F.inicio, disponibilidade_min: F.disponibilidade_min, senioridades: F.senioridades, tipo_servico: F.tipo_servico, metodologia: F.metodologia, briefing_nome: F.briefing_nome, briefing_texto: F.briefing_texto, briefing_hash: F.briefing_hash || null, rascunho, usar_ia: F.usar_ia && !!S.meta.ia_ativa, busca_id: F.busca_id || null };
  // validação local (mesmas regras do servidor)
  const er = {};
  if (!body.nome) er.nome = "Dê um nome ao projeto para encontrá-lo depois no histórico.";
  if (!rascunho) { const falta = 40 - body.descricao.trim().length; if (falta > 0) er.descricao = `Descreva a demanda com pelo menos 40 caracteres — faltam ${falta}.`; if (!body.skills.length) er.skills = "Adicione ao menos uma skill: digite o nome e pressione Enter."; }
  ["nome", "descricao", "skills"].forEach((c) => setErr(c, er[c] || ""));
  const n = Object.keys(er).length;
  $("#err-sum").innerHTML = n ? `<div class="alert alert-error" role="alert" style="margin-bottom:24px">${ic("alert")}<p>${n === 1 ? "1 campo precisa de ajuste." : `${n} campos precisam de ajuste.`}</p></div>` : "";
  if (n) { window.scrollTo({ top: 0, behavior: "smooth" }); return; }
  if (rascunho) {
    try { const r = await api("/api/buscas", { method: "POST", json: body }); F.busca_id = r.id; toast("Rascunho salvo. Ele aparece em Buscas e no início."); } catch (e) { mostraErrosServidor(e); }
    return;
  }
  const titulo = body.nome;
  $("#nb-main").innerHTML = `${band(`${crumbs([["Buscas", "#/buscas"], ["Gerando"]])}<h1 class="t-display" style="margin-top:24px">${esc(titulo)}</h1>`)}
    <section aria-busy="true" style="max-width:960px;margin-top:40px"><p role="status" class="t-2" style="display:flex;align-items:center;gap:8px"><span class="spin"></span>Cruzando skills, histórico e disponibilidade…</p>
    <div style="margin-top:32px;display:flex;flex-direction:column;gap:12px" aria-hidden="true"><div class="sk" style="width:260px;height:18px"></div>
    ${[1, 2, 3].map(() => `<div class="card" style="padding:24px;display:grid;grid-template-columns:40px minmax(0,1fr) 80px;gap:16px;align-items:start"><div class="sk" style="width:40px;height:40px;border-radius:50%"></div><div style="display:flex;flex-direction:column;gap:10px"><div class="sk" style="width:40%;height:16px"></div><div class="sk" style="width:24%;height:12px"></div><div style="display:flex;gap:6px;margin-top:6px"><div class="sk" style="width:64px;height:24px"></div><div class="sk" style="width:52px;height:24px"></div><div class="sk" style="width:88px;height:24px"></div></div><div class="sk" style="width:60%;height:12px;margin-top:4px"></div></div><div class="sk" style="width:64px;height:28px;justify-self:end"></div></div>`).join("")}</div></section>`;
  try {
    const r = await api("/api/buscas", { method: "POST", json: body });
    S.sel = new Map(); S.remOn = true; S.q = "";
    go(`#/buscas/${r.id}`);
  } catch (e) {
    await pageNovaBusca(new URLSearchParams(), true); // volta ao formulário sem perder o que foi preenchido
    mostraErrosServidor(e);
  }
}
function mostraErrosServidor(e) {
  const er = (e.detail && e.detail.erros) || null;
  if (!er) { toast(e.message); return; }
  const id = e.detail.busca_id, link = id ? ` <a href="#/buscas/${id}">Abrir a busca existente</a>` : "";
  ["nome", "descricao", "skills"].forEach((c) => setErr(c, er[c] || ""));
  if (er.nome && id) $("#e-nome").innerHTML = `<p class="err-msg">${ic("alert")}<span>${esc(er.nome)}${link}</span></p>`;
  if (er.briefing) $("#brief-err").innerHTML = `<p class="err-msg">${ic("alert")}<span>${esc(er.briefing)}${link}</span></p>`;
  const n = Object.keys(er).length;
  $("#err-sum").innerHTML = `<div class="alert alert-error" role="alert" style="margin-bottom:24px">${ic("alert")}<p>${n === 1 ? "1 campo precisa de ajuste." : `${n} campos precisam de ajuste.`} ${esc(Object.values(er)[0])}</p></div>`;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ============================================================ 05 · resultados */
function statusInterno(c, need) {
  if (c.disponivel) return `<span class="status s-ok">${ic("check")}Disponível · ${c.disp_min >= 100 ? "100% livre" : `≥ ${need}% livre`} no período</span>`;
  const maxLoad = 100 - c.disp_min;
  const viab = c.remanejamento?.viabilidade;
  return `<span class="status s-warn">${ic("warn")}${maxLoad}% alocado · remanejamento ${viab === "Difícil" ? "difícil" : "viável"}</span>`;
}
function porque(c) {
  if (c.justificativa_regra) return c.justificativa; // texto da IA
  const h = c.historico_similar?.[0];
  if (h) return `Atuou em ${h.demanda} (${h.tipo_servico} · ${h.metodologia}, ${h.similaridade}% similar).`;
  const ok = c.skills_match.filter((s) => s.ok).length;
  return `Atende ${ok} de ${c.skills_match.length} skills no nível pedido.`;
}
function acaoCandidato(b, origem, id, nome) {
  const key = `${origem}:${id}`;
  const aloc = (b.decisoes || []).find((d) => d.origem === origem && d.candidato_id === id);
  if (aloc) {
    const opts = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map((v) => `<option value="${v}" ${v === aloc.percentual ? "selected" : ""}>${v}%</option>`).join("");
    return `<label class="sr-only" for="pct-${key}">Dedicação de ${esc(nome)}</label><select class="select" id="pct-${key}" data-pct="${key}" style="width:96px;min-height:36px;padding:6px 32px 6px 10px" title="Dedicação no projeto">${opts}</select>
      <button type="button" class="btn btn-sm btn-ghost" data-rem="${key}" aria-label="Remover ${esc(nome)} do projeto">Remover</button>`;
  }
  const sel = S.sel.has(key);
  return `<button type="button" class="btn btn-sm ${sel ? "btn-selected" : "btn-secondary"}" aria-pressed="${sel}" data-sel="${key}">${sel ? ic("check", "i-sm") + "Selecionado" : "Selecionar"}</button>`;
}
function cardInterno(c, b, need, near = false) {
  const hit = c.skills_match.filter((s) => s.nivel_atual !== "—"), miss = c.skills_match.filter((s) => s.nivel_atual === "—");
  const role = [c.cargo, c.senioridade, c.modalidade].filter(Boolean).join(" · ");
  return `<li><article class="card res-card ${near ? "near" : ""}" aria-labelledby="n-${c.id}">
    <div style="display:flex;flex-direction:column;gap:16px;min-width:0">
      <div class="row" style="gap:14px"><span class="avatar" aria-hidden="true">${esc(ini(c.nome))}</span><div style="min-width:0"><div class="row" style="gap:8px;flex-wrap:wrap"><span class="chip chip-origin">Interno</span><h3 id="n-${c.id}" style="font-size:17px;line-height:24px;font-weight:600">${nm(c.nome)}</h3>${c.perfil_amplo ? '<span class="chip chip-origin" title="Declara skills demais no SGD — confirme com o líder">perfil amplo</span>' : ""}</div><p class="t-small t-2" style="margin-top:2px">${esc(role)}</p></div></div>
      <ul class="chips" aria-label="Skills de ${esc(c.nome)}">${hit.map((s) => `<li class="chip chip-skill" title="${esc(s.nivel_atual)}${s.ok ? "" : ` · pedido ${s.nivel_pedido}`}">${esc(s.nome)}${s.ok ? "" : " ↓"}<span class="sr-only"> — ${s.ok ? "atende" : "abaixo do nível"}</span></li>`).join("")}${miss.map((s) => `<li class="chip chip-miss">${ic("x")}${esc(s.nome)}<span class="sr-only"> — não atende</span></li>`).join("")}</ul>
      <div class="meta-line">${near ? `<span class="status s-warn">${ic("warn")}Falta: ${esc(c.faltando_obrigatorias.join(", "))} · candidato a PDI</span>` : statusInterno(c, need)}<span class="t-small t-2">${esc(porque(c))}</span></div>
    </div>
    <div class="res-side"><div><p class="score">${Math.round(c.score)}%</p><p class="t-cap" style="text-align:right">match</p></div>
      <div class="row" style="gap:16px"><a href="#/buscas/${b.id}/interno/${c.id}" class="t-small" style="font-weight:600;display:inline-flex;align-items:center;min-height:44px" aria-label="Ver detalhes de ${esc(c.nome)}">Ver detalhes</a>
      ${acaoCandidato(b, "interno", c.id, c.nome)}</div></div>
  </article></li>`;
}
function rowExterno(t, b) {
  const pedidas = (b.resultado.requisitos || []).map((r) => r.nome), miss = pedidas.filter((p) => !t.skills_atendidas.includes(p));
  return `<li class="ext-row"><div style="display:flex;flex-direction:column;gap:10px;min-width:0">
      <div class="row" style="gap:12px"><span class="avatar avatar-sm" aria-hidden="true">${esc(ini(t.nome))}</span><div style="min-width:0"><div class="row" style="gap:8px;flex-wrap:wrap"><span class="chip chip-origin">iHiring</span><h3 style="font-size:15px;line-height:22px;font-weight:600">${nm(t.nome)}</h3><span class="chip chip-syn">dado de teste</span></div><p class="t-small t-2">${esc([t.cargo, t.senioridade, t.modalidade].filter(Boolean).join(" · "))}</p></div></div>
      <ul class="chips">${t.skills_atendidas.map((s) => `<li class="chip chip-skill">${esc(s)}</li>`).join("")}${miss.map((s) => `<li class="chip chip-miss">${ic("x")}${esc(s)}</li>`).join("")}</ul>
      <div class="meta-line"><span class="status ${t.disponibilidade > 0 ? "s-ok" : "s-muted"}">${ic(t.disponibilidade > 0 ? "check" : "clock")}Disponibilidade informada: ${t.disponibilidade}%</span></div></div>
    <div class="res-side"><div><p class="ext-score">${Math.round(t.score)}%</p><p class="t-cap" style="text-align:right">match</p></div>
      <div class="row" style="gap:16px"><a href="#/buscas/${b.id}/ihiring/${t.id}" class="t-small" style="font-weight:600;display:inline-flex;align-items:center;min-height:44px">Ver detalhes</a>
      ${acaoCandidato(b, "ihiring", t.id, t.nome)}</div></div></li>`;
}
let CUR = null; // busca carregada
async function pageResultado(id) {
  loadingView("buscas");
  let b; try { b = await api(`/api/buscas/${id}`); } catch (e) { return errorView("buscas", e); }
  if (b.status === "rascunho" || !b.resultado) return go(`#/buscas/nova?de=${id}`);
  if (!S.keepSel && (!CUR || CUR.id !== b.id)) { S.sel = new Map(); S.remOn = true; S.q = ""; }
  S.keepSel = false;
  CUR = b;
  const r = b.resultado, p = b.params;
  shell("buscas", `<main class="wrap-narrow" style="padding-bottom:48px;flex:1">
    ${band(`<div class="between">${crumbs([["Buscas", "#/buscas"], ["Resultado"]])}<div class="row" style="gap:8px">${(b.decisoes || []).length ? `<a class="btn btn-secondary btn-sm" href="#/buscas/${b.id}/relatorio">${ic("report", "i-sm")}Relatório</a>` : ""}<a class="btn btn-ghost btn-sm" href="#/buscas/nova?de=${b.id}">${ic("pencil", "i-sm")}Editar projeto</a><a class="btn btn-secondary btn-sm" href="#/buscas/nova">${ic("plus", "i-sm")}Nova busca</a></div></div>
      <section style="margin-top:24px;display:flex;flex-direction:column;gap:10px"><div class="row" style="gap:12px;flex-wrap:wrap"><h1 class="t-display">${esc(b.nome)}</h1>${statusBusca(b.status, (b.decisoes || []).length)}</div>
        <p class="t-small t-2 t-num">Gerado em ${fmtDate(b.atualizado_em || b.criado_em, true)} · ${esc(r.duracao_meses ? `${r.duracao_meses} ${r.duracao_meses === 1 ? "mês" : "meses"}` : p.duracao)} · início ${r.inicio_data ? fmtDia(r.inicio_data) : esc(p.inicio).toLowerCase()} (${esc(r.periodo.rotulo)}) · dedicação mínima ${r.disponibilidade_min}% · por ${esc(b.autor || "—")}</p>
        <p class="t-small" style="color:var(--ink-2)"><span class="t-strong" style="color:var(--ink)">Skills pedidas</span> ${r.requisitos.map((q) => esc(q.nome) + (q.obrigatoria ? "" : " (desejável)")).join(" · ")}</p>
        <p class="ia-pill" id="ia-pill">${iaPill(r)}</p></section>`)}
    <div id="res-body"></div></main><div id="selbar"></div>`);
  renderRes();
  if (r.ia?.pendente) aguardarIA(b.id);
}
function iaPill(r) {
  const fonte = ` · fonte SGD: ${r.fonte_dados === "postgres" ? "Postgres" : "snapshot"}`;
  if (r.ia?.pendente) return `<span class="ia-dot wait"></span>Refinando o ranking com IA…${fonte}`;
  return `<span class="ia-dot ${r.ia?.usada ? "on" : ""}"></span>${r.ia?.usada ? "Ranking refinado por IA" : "Ranking por skills, histórico e disponibilidade"}${fonte}`;
}
// o ranking aparece na hora; quando a IA termina, a tela se atualiza sozinha
async function aguardarIA(id, tentativa = 0) {
  await new Promise((ok) => setTimeout(ok, tentativa < 5 ? 2000 : 4000));
  if (!CUR || CUR.id !== id || !location.hash.startsWith(`#/buscas/${id}`) || location.hash.split("/").length > 3) return;
  let b; try { b = await api(`/api/buscas/${id}`); } catch (_) { return; }
  if (!CUR || CUR.id !== id) return;
  if (b.resultado?.ia?.pendente && tentativa < 30) return aguardarIA(id, tentativa + 1);
  const ia = b.resultado?.ia?.pendente ? { usada: false } : b.resultado?.ia;
  CUR.resultado = { ...b.resultado, ia }; CUR.decisoes = b.decisoes; CUR.status = b.status;
  const pill = $("#ia-pill"); if (pill) pill.innerHTML = iaPill(CUR.resultado);
  const y = window.scrollY, foco = document.activeElement?.id;
  if ($("#res-body")) { renderRes(); window.scrollTo(0, y); if (foco && $("#" + CSS.escape(foco))) $("#" + CSS.escape(foco)).focus(); }
  if (ia?.usada) toast("Ranking refinado pela IA.");
}
function renderRes() {
  const b = CUR, r = b.resultado, need = r.disponibilidade_min, q = fold(S.q);
  const confirmada = b.status === "confirmada";
  const decs = b.decisoes || [];
  const selInt = new Set(decs.filter((d) => d.origem === "interno").map((d) => d.candidato_id));
  const selExt = new Set(decs.filter((d) => d.origem === "ihiring").map((d) => d.candidato_id));
  const match = (c) => !q || fold(`${c.nome} ${c.cargo} ${c.senioridade} ${(c.skills_match || []).map((s) => s.nome).join(" ")} ${(c.skills_atendidas || []).join(" ")}`).includes(q);
  const naoSel = (c) => !confirmada || !selInt.has(c.id);
  const internos = r.ranking.filter((c) => naoSel(c) && (S.remOn || c.disponivel) && match(c));
  const quase = r.quase_la.filter((c) => naoSel(c) && match(c));
  const externos = r.externos.filter((t) => (!confirmada || !selExt.has(t.id)) && match(t));
  const nRem = r.ranking.filter((c) => naoSel(c) && c.remanejamento).length;
  const total = internos.length + externos.length;
  const hot = confirmada ? [] : r.ranking.filter((c) => c.mais_viavel_alocado);
  // seleção confirmada fica no topo
  const escolhidosInt = [...r.ranking, ...r.quase_la, ...(r.fixados || [])].filter((c) => selInt.has(c.id));
  const escolhidosExt = [...r.externos, ...(r.externos_fixados || [])].filter((t) => selExt.has(t.id));
  const topo = confirmada ? `
    <section aria-labelledby="secSel" style="margin-top:40px;display:flex;flex-direction:column;gap:16px">
      <div><div class="row" style="gap:12px;align-items:baseline;flex-wrap:wrap"><h2 id="secSel" class="t-h1">Alocados no projeto</h2><span class="status s-ok">${ic("check")}${escolhidosInt.length + escolhidosExt.length} pessoa${escolhidosInt.length + escolhidosExt.length === 1 ? "" : "s"} · ${esc(r.periodo.rotulo)}</span></div>
        <p class="t-2">Ajuste a dedicação de cada pessoa ou remova. Para incluir mais gente, selecione em <b>Também sugeridos</b> e clique em “Adicionar ao projeto”.</p></div>
      ${escolhidosInt.length ? `<ol style="display:flex;flex-direction:column;gap:12px">${escolhidosInt.map((c) => cardInterno(c, b, need)).join("")}</ol>` : ""}
      ${escolhidosExt.length ? `<ul class="card" style="padding:0">${escolhidosExt.map((t) => rowExterno(t, b)).join("")}</ul>` : ""}
    </section>
    <div style="margin-top:72px"><h2 class="t-display" style="font-size:28px;line-height:36px">Também sugeridos</h2><p class="t-2" style="margin-top:4px">Os demais talentos que o matchmaking encontrou para esta busca.</p></div>` : "";
  $("#res-body").innerHTML = `${topo}
    <div class="between" style="margin-top:${confirmada ? 24 : 32}px;padding:12px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);row-gap:8px">
      <p aria-live="polite" style="font-size:15px"><span class="t-strong">${total} talento${total === 1 ? "" : "s"} ${confirmada ? "também sugerido" + (total === 1 ? "" : "s") : "encontrado" + (total === 1 ? "" : "s")}</span>${S.remOn && nRem ? `<span class="t-strong" style="color:var(--warn-ink)"> · ${nRem} com remanejamento ${nRem === 1 ? "viável" : "viáveis"}</span>` : ""}${!S.remOn ? '<span class="t-2"> · remanejamento desconsiderado</span>' : ""}</p>
      <div class="row toolbar-r" style="gap:20px;flex-wrap:wrap"><button type="button" class="toggle" role="switch" aria-checked="${S.remOn}" id="tg-rem"><span class="track" aria-hidden="true"></span>Considerar remanejamento</button>
        <div class="row" style="gap:8px"><label for="q" class="t-small t-2" style="font-weight:500">Filtrar</label><div style="position:relative"><svg class="i i-sm" viewBox="0 0 24 24" aria-hidden="true" style="position:absolute;left:12px;top:14px;color:var(--ink-2)">${ICON.search}</svg><input id="q" class="input" type="search" value="${esc(S.q)}" placeholder="Nome, cargo ou skill" style="padding-left:36px;width:240px"></div></div></div></div>
    ${S.remOn && hot.length ? `<div class="alert alert-warn" style="margin-top:24px">${ic("warn")}<p><b>${hot.map((c) => nm(c.nome)).join(", ")}</b> ${hot.length > 1 ? "têm" : "tem"} aderência técnica igual ou maior que a melhor pessoa disponível, mas ${hot.length > 1 ? "estão alocados" : "está alocado(a)"} no período. Abra os detalhes para ver o que liberar e com quem falar.</p></div>` : ""}
    ${confirmada ? "" : r.avisos.map((a) => `<div class="alert alert-info" style="margin-top:12px">${ic("info")}<p>${esc(a)}</p></div>`).join("")}
    <section aria-labelledby="secA" style="margin-top:${confirmada ? 32 : 48}px;display:flex;flex-direction:column;gap:16px">
      <div><div class="row" style="gap:12px;align-items:baseline"><h2 id="secA" class="t-h1">Colaboradores Vint_Global</h2><span class="t-2 t-num">${internos.length} encontrado${internos.length === 1 ? "" : "s"}</span></div><p class="t-2">Já estão na empresa — realocação imediata. Fonte: SGD.</p></div>
      ${internos.length ? `<ol style="display:flex;flex-direction:column;gap:12px" aria-label="Colaboradores Vint_Global, por match">${internos.map((c) => cardInterno(c, b, need)).join("")}</ol>`
        : `<div class="empty-box">${ic("info")}<div><p class="t-strong">Nenhum colaborador interno ${confirmada ? "além dos selecionados " : ""}atende aos critérios.</p><p class="t-2">Veja os talentos do banco iHiring abaixo.${!S.remOn ? " Ligar “Considerar remanejamento” pode trazer colaboradores hoje alocados." : ""}</p></div></div>`}
      ${quase.length ? `<div style="margin-top:24px"><h3 class="t-h2">Próximos do ideal</h3><p class="t-2" style="margin-top:4px">Faltam 1–2 skills obrigatórias — bons candidatos a PDI.</p></div><ol style="display:flex;flex-direction:column;gap:12px">${quase.map((c) => cardInterno(c, b, need, true)).join("")}</ol>` : ""}
    </section>
    <div role="separator" aria-hidden="true" style="margin:64px 0 0;display:flex;align-items:center;gap:16px"><span style="flex:1;height:1px;background:var(--line)"></span><span class="t-cap">Fora da Vint_Global</span><span style="flex:1;height:1px;background:var(--line)"></span></div>
    <section aria-labelledby="secB" style="margin-top:40px;display:flex;flex-direction:column;gap:16px">
      <div><div class="row" style="gap:12px;align-items:baseline"><h2 id="secB" class="t-h1">Banco de talentos iHiring</h2><span class="t-2 t-num">${externos.length} encontrado${externos.length === 1 ? "" : "s"}</span></div><p class="t-2">Talentos mapeados, disponíveis para contato. <span class="chip chip-syn">base de teste sintética</span></p></div>
      ${externos.length ? `<ul class="card" style="padding:0">${externos.map((t) => rowExterno(t, b)).join("")}</ul>` : `<div class="empty-box">${ic("info")}<div><p class="t-strong">Nenhum talento do banco iHiring ${confirmada ? "além dos selecionados " : ""}atende aos critérios.</p><p class="t-2">Revise as skills ou reduza a dedicação mínima.</p></div></div>`}
    </section>`;
  $("#tg-rem").onclick = () => { S.remOn = !S.remOn; renderRes(); };
  $("#q").oninput = (e) => { S.q = e.target.value; const pos = e.target.selectionStart; renderRes(); const i = $("#q"); i.focus(); i.setSelectionRange(pos, pos); };
  $$("[data-sel]").forEach((btn) => (btn.onclick = () => {
    const k = btn.dataset.sel;
    if (S.sel.has(k)) S.sel.delete(k); else S.sel.set(k, true);
    renderRes();
  }));
  $$("[data-pct]").forEach((el) => (el.onchange = async () => {
    const [origem, id] = el.dataset.pct.split(":");
    try { await api(`/api/buscas/${CUR.id}/decisao/${origem}/${id}`, { method: "PATCH", json: { percentual: +el.value } }); toast(`Dedicação ajustada para ${el.value}%.`); const d = CUR.decisoes.find((x) => x.origem === origem && x.candidato_id === +id); if (d) d.percentual = +el.value; }
    catch (e) { toast(e.message); }
  }));
  $$("[data-rem]").forEach((btn) => (btn.onclick = async () => {
    const [origem, id] = btn.dataset.rem.split(":");
    try { const r2 = await api(`/api/buscas/${CUR.id}/decisao/${origem}/${id}`, { method: "DELETE" }); toast(r2.restantes ? "Pessoa removida do projeto." : "Pessoa removida. O projeto voltou para “Aguardando decisão”."); CUR = null; S.keepSel = true; pageResultado(+location.hash.split("/")[2]); }
    catch (e) { toast(e.message); }
  }));
  renderSelbar();
}
function renderSelbar() {
  const el = $("#selbar"); if (!el) return;
  if (!S.sel.size) { el.innerHTML = ""; return; }
  const add = CUR.status === "confirmada";
  const r = CUR.resultado, nomes = [...S.sel.keys()].map((k) => { const [o, id] = k.split(":"); const c = o === "interno" ? [...r.ranking, ...r.quase_la, ...(r.fixados || [])].find((x) => x.id === +id) : [...r.externos, ...(r.externos_fixados || [])].find((x) => x.id === +id); return c ? nm(c.nome) : k; });
  el.innerHTML = `<div class="selbar" role="region" aria-label="Seleção"><div class="wrap-narrow"><div><p class="t-strong">${S.sel.size} talento${S.sel.size > 1 ? "s" : ""} selecionado${S.sel.size > 1 ? "s" : ""} para ${esc(CUR.nome)}</p><p class="t-small t-2">${nomes.join(", ")}</p></div>
    <div class="row" style="gap:8px"><button class="btn btn-ghost" id="sel-clear">Limpar</button><button class="btn btn-primary" id="sel-ok">${add ? "Adicionar ao projeto" : "Confirmar seleção"}</button></div></div></div>`;
  $("#sel-clear").onclick = () => { S.sel.clear(); renderRes(); };
  $("#sel-ok").onclick = confirmar;
}
async function confirmar() {
  const selecionados = [...S.sel.keys()].map((k) => { const [origem, id] = k.split(":"); return { origem, id: +id }; });
  try {
    await api(`/api/buscas/${CUR.id}/decisao`, { method: "POST", json: { selecionados } });
    toast(CUR.status === "confirmada" ? `${selecionados.length} pessoa(s) adicionada(s) ao projeto.` : "Alocação confirmada e registrada. Avise os gestores das alocações afetadas.");
    S.sel.clear(); CUR = null; render();
  } catch (e) { toast(e.message); }
}

/* ============================================================ 06 · detalhes do candidato */
function barras(cel, cls, row) {
  const out = []; let i = 0;
  while (i < cel.length) {
    if (!cel[i]) { i++; continue; }
    let j = i; while (j + 1 < cel.length && cel[j + 1] === cel[i]) j++;
    out.push({ start: i, span: j - i + 1, pct: cel[i] }); i = j + 1;
  }
  return out.map((b) => `<div class="tl-bar ${cls}" style="grid-row:${row};grid-column:${b.start + 2} / span ${b.span}">${b.pct}%</div>`).join("");
}
async function pageDetalhe(id, origem, cid) {
  loadingView("buscas");
  let d; try { d = await api(`/api/buscas/${id}/candidatos/${origem}/${cid}`); } catch (e) { return errorView("buscas", e); }
  if (origem === "ihiring") return detalheExterno(d, id);
  const c = d.candidato, f = d.ficha, tl = d.timeline, b = d.busca;
  const selBtn = d.selecionado ? `<span class="btn btn-selected">${ic("check", "i-sm")}No projeto</span><button class="btn btn-ghost" id="rem-one">Remover</button>` : `<button class="btn btn-primary" id="sel-one">${b.status === "confirmada" ? "Adicionar ao projeto" : "Selecionar para o projeto"}</button>`;
  const role = [c.cargo, c.senioridade].filter(Boolean).join(" · ") + (f.desde ? ` · na Vint_Global desde ${f.desde}` : "");
  const rows = tl.linhas.map((l, i) => `<div class="tl-lbl" style="grid-row:${i + 2};grid-column:1">${esc(l.projeto)}<div class="t-small t-2" style="font-weight:400">${esc(l.andamento)}</div></div>${barras(l.celulas, "tl-cur", i + 2)}`).join("");
  const rProp = Math.max(tl.linhas.length, 1) + 2, rTot = rProp + 1; // sem alocações, a linha "Sem alocação ativa" ocupa a linha 2
  const propCells = tl.proposta;
  const propStart = propCells.findIndex((x) => x > 0);
  const remTxt = d.rem ? `Liberar ${d.rem.liberar_por_mes.map((x) => `${x.liberar_pct}% em ${x.mes}`).join(", ")}. A alocação mais fácil de mexer é <b>${esc(d.rem.principal.demanda)}</b> (${esc(d.rem.principal.andamento)}, contrato ${esc(d.rem.principal.situacao_contrato || "—")}) — fale com ${nm(d.rem.principal.gerente)}. ${esc(d.rem.principal.sugestao)}${d.rem.cobre ? ` <b>${nm(d.rem.cobre.nome)}</b> (${d.rem.cobre.origem === "interno" ? "interno" : "iHiring"}, ${Math.round(d.rem.cobre.score)}% de aderência às skills dessa demanda) pode cobrir a saída.` : ""}` : "";
  const pdi = [...(c.pdi || []).map((p) => ({ t: `Desenvolver ${p.skill} (${p.de} → ${p.para})`, d: [p.base_existente.length ? `Base que já tem: ${p.base_existente.join(", ")}` : `Área ${p.area}`, p.pratica_em.length ? `praticar em ${p.pratica_em.join(", ")}` : ""].filter(Boolean).join(" · "), m: `Trilha interna · ${p.prazo_estimado}` })),
    ...(c.pdi || []).filter((p) => p.mentor_sugerido).slice(0, 1).map((p) => ({ t: `Pareamento com ${esc(p.mentor_sugerido)}`, d: `Colega com ${p.skill} avançado e mais disponibilidade no período.`, m: "Mentoria · 4 semanas", raw: true }))];
  shell("buscas", `<main class="wrap" style="flex:1;padding-bottom:96px">
    ${band(`${crumbs([["Buscas", "#/buscas"], [b.nome, `#/buscas/${b.id}`], [c.nome]])}
      <div class="between" style="margin-top:32px;align-items:flex-end;row-gap:24px"><div class="row" style="gap:20px"><span class="avatar avatar-lg" aria-hidden="true">${esc(ini(c.nome))}</span><div><span class="chip chip-origin">Interno</span><h1 class="t-display" style="font-size:40px;line-height:48px;margin-top:4px">${nm(c.nome)}</h1><p class="t-2" style="margin-top:4px">${esc(role)}</p></div></div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:16px"><div><p class="big-score">${Math.round(c.score)}%</p><p class="t-cap" style="text-align:right">match · ${esc(b.nome)}</p></div><div class="row" style="gap:16px"><a class="link-btn" href="#/buscas/${b.id}" style="text-decoration:none">${ic("back")}Voltar</a>${selBtn}</div></div></div>`, "padding-bottom:48px")}
    <div class="det-grid" style="margin-top:56px">
      <div style="display:flex;flex-direction:column;gap:56px;min-width:0">
        <section class="dsec" aria-labelledby="pq"><h2 id="pq" class="t-h1">Por que este match</h2><ul class="why">${d.motivos.map((m) => `<li>${m.ok ? `<span class="t-ok">${ic("check")}</span>` : `<span class="t-2">${ic("x")}</span>`}<p><span class="t-strong">${esc(m.forte)}</span> ${esc(m.texto)}</p></li>`).join("")}</ul></section>
        <section class="dsec" aria-labelledby="al"><div class="between"><h2 id="al" class="t-h1">Alocações atuais</h2>${c.disponivel ? `<span class="status s-ok">${ic("check")}Disponível no período</span>` : `<span class="status s-warn">${ic("warn")}${100 - c.disp_min}% alocado · remanejamento ${d.rem?.viabilidade === "Difícil" ? "difícil" : "viável"}</span>`}</div>
          <div class="tl-box"><div class="tl"><div class="tl-m" style="grid-row:1;grid-column:1">Projeto</div>${tl.meses.map((m, i) => `<div class="tl-m" style="grid-row:1;grid-column:${i + 2}">${esc(m.split("/")[0])}</div>`).join("")}
            ${rows || `<div class="tl-lbl t-2" style="font-weight:400;grid-row:2;grid-column:1 / span 7">Sem alocação ativa no SGD nesta janela.</div>`}
            ${propStart >= 0 ? `<div class="tl-lbl" style="font-weight:400;grid-row:${rProp};grid-column:1">${esc(b.nome)}<div class="t-small t-2">(proposta)</div></div><div class="tl-bar tl-prop" style="grid-row:${rProp};grid-column:${propStart + 2} / span ${propCells.filter((x) => x > 0).length}">${propCells[propStart]}% · a partir de ${esc(tl.meses[propStart].split("/")[0].toLowerCase())}</div>` : ""}
            <div class="tl-tot" style="grid-row:${rTot};grid-column:1;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);font-weight:500">Total atual</div>${tl.total.map((t, i) => `<div class="tl-tot ${t > 100 ? "over" : ""}" style="grid-row:${rTot};grid-column:${i + 2}">${t}%</div>`).join("")}</div></div>
          <p class="t-small t-2">Barras cheias: alocação registrada no SGD. Tracejado: o que esta busca propõe.</p>
          ${d.rem ? `<div class="panel-soft" style="background:var(--warn-bg);padding:24px 28px;display:flex;gap:12px"><span style="color:var(--warn)">${ic("warn")}</span><div style="display:flex;flex-direction:column;gap:12px"><h3 class="t-h2" style="color:var(--warn-ink)">Remanejamento sugerido</h3><p>${remTxt}</p>
            <details><summary class="btn btn-secondary btn-sm" style="display:inline-flex;width:max-content">Ver impacto</summary><div class="table-box" style="margin-top:12px"><table class="table"><thead><tr><th>Demanda atual</th><th>Status</th><th>Contrato</th><th>Ocupação</th><th>Gerente</th><th>Facilidade</th></tr></thead><tbody>${d.rem.alocacoes.map((a) => `<tr><td>${esc(a.demanda)}<div class="t-small t-2">${esc(a.tipo_servico)}</div></td><td>${esc(a.andamento)}</td><td>${esc(a.contrato)}<div class="t-small t-2">${esc(a.situacao_contrato)}</div></td><td class="t-num">${a.meses.map((m) => `${esc(m.mes)}: ${m.pct}%`).join("<br>")}</td><td>${nm(a.gerente)}</td><td>${esc(a.facilidade)}</td></tr>`).join("")}</tbody></table></div></details></div></div>` : ""}
        </section>
        ${pdi.length || c.pdi_resumo ? `<section class="dsec" aria-labelledby="pd"><div><h2 id="pd" class="t-h1">PDI sugerido</h2><p class="t-2" style="margin-top:4px">Ações que fecham a lacuna deste match e preparam a próxima alocação.</p></div>
          <div class="card pad">${c.pdi_resumo ? `<p style="margin-bottom:20px">${esc(c.pdi_resumo)}</p>` : ""}${pdi.map((x, i) => `<div class="pdi"><span class="t-2 t-num">${String(i + 1).padStart(2, "0")}</span><div><p class="t-strong">${x.raw ? x.t : esc(x.t)}</p><p class="t-small t-2" style="margin-top:4px">${esc(x.d)}</p></div><p class="t-small t-2 pdi-meta">${esc(x.m)}</p></div>`).join("")}
          <p class="help" style="margin-top:16px">O SGD não tem catálogo de cursos: a trilha é sugerida a partir das lacunas, de colegas avançados e de demandas ativas.</p></div></section>` : ""}
      </div>
      <aside style="display:flex;flex-direction:column;gap:40px">
        <div><p class="t-cap">Ficha</p><dl class="ficha" style="margin-top:8px">
          <div><dt>E-mail</dt><dd class="t-2">Não consta no SGD</dd></div>
          <div><dt>Gestor da demanda atual</dt><dd>${f.gestor ? nm(f.gestor) : "—"}</dd></div>
          <div><dt>Modalidade · vínculo</dt><dd>${esc(f.local)}</dd></div>
          <div><dt>Alocação hoje</dt><dd class="t-num">${f.alocacao_hoje}% (${f.n_projetos_hoje} projeto${f.n_projetos_hoje === 1 ? "" : "s"})</dd></div>
          <div><dt>Pode começar</dt><dd>${esc(f.pode_comecar)}</dd></div></dl></div>
        <div><p class="t-cap">Skills × demanda</p><ul class="chips" style="margin-top:12px">${c.skills_match.map((s) => s.nivel_atual !== "—" ? `<li class="chip chip-skill" title="${esc(s.nivel_atual)}">${esc(s.nome)} · ${esc(s.nivel_atual.slice(0, 5))}.</li>` : `<li class="chip chip-miss">${ic("x")}${esc(s.nome)}</li>`).join("")}</ul>
          <p class="t-small t-2" style="margin-top:12px">${c.n_skills_declaradas} skills declaradas no SGD${c.perfil_amplo ? " — perfil amplo: confirme o nível real com o líder." : "."}${c.skills_match.some((s) => s.evidencia_projeto) ? " ★ = usada em projeto registrado." : ""}</p></div>
      </aside>
    </div></main>`);
  bindSelUm(b, "interno", c.id);
}
function detalheExterno(d, id) {
  const t = d.candidato, b = d.busca;
  const selBtn = d.selecionado ? `<span class="btn btn-selected">${ic("check", "i-sm")}No projeto</span><button class="btn btn-ghost" id="rem-one">Remover</button>` : `<button class="btn btn-primary" id="sel-one">${b.status === "confirmada" ? "Adicionar ao projeto" : "Selecionar para o projeto"}</button>`;
  shell("buscas", `<main class="wrap" style="flex:1;padding-bottom:96px">
    ${band(`${crumbs([["Buscas", "#/buscas"], [b.nome, `#/buscas/${b.id}`], [t.nome]])}
      <div class="between" style="margin-top:32px;align-items:flex-end;row-gap:24px"><div class="row" style="gap:20px"><span class="avatar avatar-lg" aria-hidden="true">${esc(ini(t.nome))}</span><div><span class="chip chip-origin">iHiring</span> <span class="chip chip-syn">dado sintético de teste</span><h1 class="t-display" style="font-size:40px;line-height:48px;margin-top:4px">${nm(t.nome)}</h1><p class="t-2" style="margin-top:4px">${esc([t.cargo, t.senioridade, t.modalidade].filter(Boolean).join(" · "))}</p></div></div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:16px"><div><p class="big-score">${Math.round(t.score)}%</p><p class="t-cap" style="text-align:right">match · ${esc(b.nome)}</p></div><div class="row" style="gap:16px"><a class="link-btn" href="#/buscas/${b.id}" style="text-decoration:none">${ic("back")}Voltar</a>${selBtn}</div></div></div>`, "padding-bottom:48px")}
    <div class="det-grid" style="margin-top:56px"><section class="dsec"><h2 class="t-h1">Por que este match</h2><ul class="why">
      <li><span class="t-ok">${ic("check")}</span><p><span class="t-strong">Atende ${t.skills_atendidas.length} skill(s) pedida(s)</span> — ${esc(t.skills_atendidas.join(", ") || "nenhuma")}.</p></li>
      <li><span class="${t.disponibilidade > 0 ? "t-ok" : "t-2"}">${ic(t.disponibilidade > 0 ? "check" : "x")}</span><p><span class="t-strong">Disponibilidade informada: ${t.disponibilidade}%</span> — valor declarado no cadastro, sem calendário mensal.</p></li>
      ${d.faltando.length ? `<li><span class="t-2">${ic("x")}</span><p><span class="t-strong">Lacuna:</span> ${esc(d.faltando.join(", "))}.</p></li>` : ""}</ul>
      <div class="alert alert-warn">${ic("warn")}<p>Esta base InHire recebida no hackathon é sintética. Antes de contatar, confirme dados e consentimento no InHire real.</p></div></section>
      <aside><p class="t-cap">Skills no cadastro</p><ul class="chips" style="margin-top:12px">${d.skills.map((s) => `<li class="chip ${s.pedida ? "chip-skill" : "chip-origin"}">${esc(s.nome)} · ${esc(s.nivel)}</li>`).join("")}</ul></aside></div></main>`);
  bindSelUm(b, "ihiring", t.id);
}

function bindSelUm(b, origem, id) {
  if ($("#sel-one")) $("#sel-one").onclick = async () => { try { await api(`/api/buscas/${b.id}/decisao`, { method: "POST", json: { selecionados: [{ origem, id }] } }); toast(b.status === "confirmada" ? "Adicionado(a) ao projeto." : "Alocação confirmada com esta pessoa. Você pode adicionar mais gente no resultado."); CUR = null; render(); } catch (e) { toast(e.message); } };
  if ($("#rem-one")) $("#rem-one").onclick = async () => { try { await api(`/api/buscas/${b.id}/decisao/${origem}/${id}`, { method: "DELETE" }); toast("Removido(a) do projeto."); CUR = null; render(); } catch (e) { toast(e.message); } };
}

/* ============================================================ 07 · admin — usuários */
async function pageUsuarios() {
  if (S.me.perfil !== "admin") return errorView("inicio", new Error("Acesso restrito ao perfil Admin."));
  loadingView("usuarios");
  let users; try { users = await api("/api/usuarios"); } catch (e) { return errorView("usuarios", e); }
  const st = { q: "", fp: "todos", fs: "todos" };
  const nAdm = users.filter((u) => u.perfil === "admin").length, nPend = users.filter((u) => u.status === "pendente").length;
  shell("usuarios", `<main class="wrap" style="flex:1;padding-bottom:96px">
    ${band(`<div class="between"><div><h1 class="t-display">Usuários com acesso</h1><p class="t-2" style="margin-top:8px">${users.length} pessoa${users.length === 1 ? "" : "s"} · ${nAdm} Admin · ${nPend} convite${nPend === 1 ? "" : "s"} pendente${nPend === 1 ? "" : "s"}</p></div><button class="btn btn-primary" id="btn-invite">${ic("plus")}Convidar usuário</button></div>`)}
    <div style="display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr) minmax(0,1fr);gap:16px;margin:32px 0 24px" class="grid-sm-1">
      <div class="field"><label class="label" for="u-q">Buscar</label><div style="position:relative"><svg class="i i-sm" viewBox="0 0 24 24" aria-hidden="true" style="position:absolute;left:12px;top:14px;color:var(--ink-2)">${ICON.search}</svg><input id="u-q" class="input" type="search" placeholder="Nome ou e-mail" style="padding-left:36px"></div></div>
      <div class="field"><label class="label" for="u-p">Perfil</label><select class="select" id="u-p"><option value="todos">Todos</option><option value="admin">Admin</option><option value="usuario">Usuário</option></select></div>
      <div class="field"><label class="label" for="u-s">Status</label><select class="select" id="u-s"><option value="todos">Todos</option><option value="ativo">Ativo</option><option value="pendente">Convite pendente</option><option value="bloqueado">Bloqueado</option></select></div></div>
    <div id="ut"></div></main>`);
  const stat = (s) => s === "ativo" ? `<span class="status s-ok">${ic("check")}Ativo</span>` : s === "pendente" ? `<span class="status s-muted">${ic("mail")}Convite pendente</span>` : `<span class="status s-err">${ic("lock")}Bloqueado</span>`;
  const draw = () => {
    const q = fold(st.q);
    const rows = users.filter((u) => (!q || fold(u.nome + " " + u.email).includes(q)) && (st.fp === "todos" || u.perfil === st.fp) && (st.fs === "todos" || u.status === st.fs));
    $("#ut").innerHTML = rows.length ? `<div class="table-box"><table class="table"><thead><tr><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Status</th><th>Último acesso</th><th style="text-align:right">Ações</th></tr></thead><tbody>
      ${rows.map((u) => `<tr><td><div class="row" style="gap:12px"><span class="avatar avatar-sm" aria-hidden="true">${esc(ini(u.nome))}</span><span class="t-strong">${esc(u.nome)}</span>${u.voce ? '<span class="t-small t-2">(você)</span>' : ""}</div></td><td>${esc(u.email)}</td><td><span class="chip chip-role">${perfilLabel(u.perfil)}</span></td><td>${stat(u.status)}</td><td class="t-num">${fmtRel(u.ultimo_acesso)}</td>
        <td style="text-align:right">${u.voce ? "" : u.status === "ativo" ? `<button class="act" data-a="redefinir" data-u="${u.id}">Redefinir senha</button><button class="act danger" data-a="bloquear" data-u="${u.id}">Bloquear</button>` : u.status === "pendente" ? `<button class="act" data-a="reenviar" data-u="${u.id}">Reenviar convite</button>` : `<button class="act" data-a="desbloquear" data-u="${u.id}">Desbloquear</button>`}</td></tr>`).join("")}</tbody></table></div>`
      : `<div class="empty-box">${ic("info")}<p>Ninguém corresponde aos filtros.</p></div>`;
    $$("[data-a]").forEach((b) => (b.onclick = () => acao(b.dataset.a, +b.dataset.u)));
  };
  const acao = async (a, uid, confirmado = false) => {
    const u = users.find((x) => x.id === uid);
    if (a === "bloquear" && !confirmado) {
      modal(`<h2 id="m-title" class="t-h1">Bloquear ${esc(u.nome.split(" ")[0])}?</h2><p class="t-2" style="margin-top:8px">${esc(u.email)} perde o acesso agora e todas as sessões são encerradas. Você pode desbloquear depois.</p>
        <div class="row" style="justify-content:flex-end;gap:8px;margin-top:24px"><button class="btn btn-ghost" data-close>Cancelar</button><button class="btn btn-primary" id="cf">Bloquear acesso</button></div>`,
      (root, close) => { $("#cf", root).onclick = () => { close(); acao(a, uid, true); }; });
      return;
    }
    try {
      const r = await api(`/api/usuarios/${uid}/acao/${a}`, { method: "POST" });
      if (r.link) linkModal(a === "reenviar" ? "Convite renovado" : "Link de redefinição gerado", `Envie este link para ${u.email}. Ele expira em 48 horas e só pode ser usado uma vez.`, r.link);
      else toast(a === "desbloquear" ? `Acesso de ${u.nome.split(" ")[0]} desbloqueado.` : `Acesso de ${u.nome.split(" ")[0]} bloqueado e sessões encerradas.`);
      users = await api("/api/usuarios"); draw();
    } catch (e) { toast(e.message); }
  };
  $("#u-q").oninput = (e) => { st.q = e.target.value; draw(); };
  $("#u-p").onchange = (e) => { st.fp = e.target.value; draw(); };
  $("#u-s").onchange = (e) => { st.fs = e.target.value; draw(); };
  $("#btn-invite").onclick = () => modal(`<h2 id="m-title" class="t-h1">Convidar usuário</h2><p class="t-2" style="margin-top:8px">Um link para definir a senha é gerado e vale por 48 horas.</p>
    <form id="inv" style="display:flex;flex-direction:column;gap:20px;margin-top:24px" novalidate>
      <div class="field"><label class="label" for="inv-name">Nome completo</label><input class="input" id="inv-name" autocomplete="off"><div id="e-iname"></div></div>
      <div class="field"><label class="label" for="inv-email">E-mail corporativo</label><input class="input" id="inv-email" type="email" autocomplete="off"><div id="e-iemail"></div></div>
      <div class="field"><label class="label" for="inv-area">Área <span class="opt">(opcional)</span></label><input class="input" id="inv-area"></div>
      <fieldset style="border:0;padding:0;margin:0;display:flex;flex-direction:column;gap:8px"><legend class="label" style="margin-bottom:6px">Perfil</legend>
        <label class="radio-card"><input type="radio" name="pf" value="usuario" checked><span><b>Usuário</b><br><span class="t-small t-2">Cria buscas, vê resultados e seleciona talentos.</span></span></label>
        <label class="radio-card"><input type="radio" name="pf" value="admin"><span><b>Admin</b><br><span class="t-small t-2">Tudo do Usuário + convida, redefine senha e bloqueia acessos.</span></span></label></fieldset>
      <div class="row" style="justify-content:flex-end;gap:8px"><button type="button" class="btn btn-ghost" data-close>Cancelar</button><button class="btn btn-primary">Enviar convite</button></div></form>`,
  (root, close) => {
    $("#inv", root).onsubmit = async (e) => {
      e.preventDefault();
      const body = { nome: $("#inv-name").value, email: $("#inv-email").value, area: $("#inv-area").value, perfil: $("input[name=pf]:checked").value };
      $("#e-iname").innerHTML = ""; $("#e-iemail").innerHTML = "";
      try {
        const r = await api("/api/usuarios", { method: "POST", json: body }); close();
        linkModal("Convite criado", `Envie este link para ${body.email}. Ele expira em 48 horas.`, r.link);
        users = await api("/api/usuarios"); draw();
      } catch (err) {
        const d = err.detail || {}; const box = d.campo === "nome" ? "#e-iname" : "#e-iemail";
        $(box).innerHTML = `<p class="err-msg">${ic("alert")}${esc(d.mensagem || err.message)}</p>`;
      }
    };
  });
  draw();
}

/* ============================================================ 08 · meu perfil */
function device(ua) {
  ua = ua || "";
  const br = /Edg\//.test(ua) ? "Edge" : /OPR\//.test(ua) ? "Opera" : /Chrome\//.test(ua) ? "Chrome" : /Firefox\//.test(ua) ? "Firefox" : /Safari\//.test(ua) ? "Safari" : "Navegador";
  const os = /iPhone|iPad/.test(ua) ? "iPhone" : /Android/.test(ua) ? "Android" : /Windows/.test(ua) ? "Windows" : /Mac OS X/.test(ua) ? "macOS" : /Linux/.test(ua) ? "Linux" : "—";
  return `${br} · ${os}`;
}
async function pagePerfil() {
  loadingView("");
  let me, ss; try { [me, ss] = await Promise.all([api("/api/me"), api("/api/me/sessoes")]); } catch (e) { return errorView("", e); }
  shell("", `<main class="wrap-narrow" style="flex:1;padding-bottom:96px">
    ${band(`<h1 class="t-display">Meu perfil</h1><p class="t-2" style="margin-top:8px">${esc(me.nome)} · ${perfilLabel(me.perfil)}${me.area ? ` · ${esc(me.area)}` : ""}</p>`)}
    <section class="psec" style="margin-top:8px"><div><h2 class="t-h2">Dados</h2><p class="t-small t-2" style="margin-top:6px">Nome e e-mail são definidos pelo Admin no convite.</p></div>
      <dl class="card pad-m kv"><div><dt>Nome</dt><dd class="t-strong">${esc(me.nome)}</dd></div><div><dt>E-mail</dt><dd>${esc(me.email)}</dd></div><div><dt>Perfil</dt><dd><span class="chip chip-role">${perfilLabel(me.perfil)}</span></dd></div><div><dt>Área</dt><dd>${esc(me.area || "—")}</dd></div></dl></section>
    <section class="psec"><div><h2 class="t-h2">Senha</h2><p class="t-small t-2" style="margin-top:6px">${me.senha_trocada_em ? `Trocada pela última vez em ${fmtDate(me.senha_trocada_em)}.` : "Ainda não trocada."}</p></div>
      <form id="pw" class="card pad-m" style="display:flex;flex-direction:column;gap:20px" novalidate>${pwField("pa", "Senha atual", "current-password")}
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px" class="grid-sm-1">${pwField("p1", "Nova senha")}${pwField("p2", "Confirmar nova senha")}</div>
        <p class="help" id="pw-help">12+ caracteres, com maiúscula, número e símbolo.</p><div id="pw-msg"></div>
        <div><button class="btn btn-primary">Atualizar senha</button></div></form></section>
    <section class="psec"><div><h2 class="t-h2">Sessões ativas</h2><p class="t-small t-2" style="margin-top:6px">Encerre qualquer acesso que você não reconheça.</p></div>
      <div><div class="table-box"><table class="table"><thead><tr><th>Dispositivo</th><th>IP</th><th>Último uso</th><th></th></tr></thead><tbody>
        ${ss.map((s) => `<tr><td><span class="t-strong">${esc(device(s.user_agent))}</span>${s.atual ? '<span class="t-small t-2"> · esta sessão</span>' : ""}</td><td class="t-num">${esc(s.ip || "—")}</td><td>${s.atual ? "Agora" : fmtRel(s.ultimo_uso)}</td><td style="text-align:right">${s.atual ? "" : `<button class="act" data-end="${s.id}">Encerrar</button>`}</td></tr>`).join("")}</tbody></table></div>
        ${ss.length > 1 ? `<button class="btn btn-secondary" id="end-all" style="margin-top:16px">Encerrar todas as outras sessões</button>` : ""}</div></section></main>`);
  bindEyes();
  const msg = (ok, t) => ($("#pw-msg").innerHTML = `<div class="alert ${ok ? "alert-info" : "alert-error"}">${ic(ok ? "check" : "alert")}<p>${esc(t)}</p></div>`);
  $("#pw").onsubmit = async (e) => {
    e.preventDefault();
    const p1 = $("#p1").value, p2 = $("#p2").value, falta = REGRAS.filter(([, f]) => !f(p1)).map(([l]) => l);
    if (falta.length) return msg(false, "A nova senha precisa de: " + falta.join(", ") + ".");
    if (p1 !== p2) return msg(false, "As senhas não coincidem.");
    try { await api("/api/me/senha", { method: "POST", json: { atual: $("#pa").value, nova: p1 } }); msg(true, "Senha atualizada. As outras sessões foram encerradas."); $("#pa").value = $("#p1").value = $("#p2").value = ""; }
    catch (err) { msg(false, err.message); }
  };
  $$("[data-end]").forEach((b) => (b.onclick = async () => { await api(`/api/me/sessoes/${b.dataset.end}`, { method: "DELETE" }); toast("Sessão encerrada."); render(); }));
  if ($("#end-all")) $("#end-all").onclick = async () => { await api("/api/me/sessoes/encerrar-outras", { method: "POST" }); toast("Outras sessões encerradas."); render(); };
}

/* ============================================================ base de conhecimento (RAG) */
async function pageBase() {
  const m = S.meta;
  let f = null;
  try { f = await api("/api/base/fontes"); } catch (_) { /* segue sem o painel */ }
  const sug = ["Quem tem PostgreSQL avançado e está livre em dezembro?", "Qual a capacidade livre da equipe nos próximos 3 meses?",
    "Quais contratos estão vencidos ou vencendo e quantas pessoas estão neles?", "Quais projetos estão aguardando decisão e quem já foi alocado?",
    "Quantos colaboradores temos por senioridade e modalidade?", "Quais problemas de qualidade de dados afetam o matching?"];
  shell("base", `<main class="wrap-narrow" style="flex:1;padding-bottom:96px">
    ${band(`<h1 class="t-display">Base de conhecimento</h1><p class="t-2" style="margin-top:8px;max-width:680px">Pergunte em português. A resposta cruza, na hora, o <b>banco SGD</b> (colaboradores, skills, disponibilidade, demandas, contratos), os <b>projetos e alocações</b> registrados aqui, o banco <b>iHiring</b> e os <b>documentos</b> da base — sempre citando a fonte.</p>
      <p class="ia-pill" style="margin-top:12px"><span class="ia-dot ${m.ia_ativa ? "on" : ""}"></span>${m.ia_ativa ? "Respostas escritas por IA a partir do banco e dos documentos" : "Respostas montadas a partir do banco e dos documentos"}</p>`)}
    ${f ? `<div class="chips" style="margin-top:24px;gap:8px" aria-label="Fontes consultadas">
      <span class="chip chip-skill">SGD ao vivo · ${f.sgd.colaboradores} colaboradores · ${f.sgd.demandas} demandas · ${f.sgd.contratos} contratos</span>
      <span class="chip chip-skill">Projetos do app · ${f.projetos} · ${f.alocacoes} alocações</span>
      <span class="chip chip-skill">iHiring · ${f.inhire} talentos</span>
      <span class="chip chip-skill">Documentos · ${f.documentos.length}</span></div>` : ""}
    <form id="rf" class="row stack-sm" style="gap:8px;margin-top:24px"><label for="rq" class="sr-only">Pergunta</label><input id="rq" class="input" placeholder="Ex.: Quem tem React avançado e está livre em janeiro?"><button class="btn btn-primary">Perguntar</button></form>
    <div class="chips" style="margin-top:12px">${sug.map((q) => `<button type="button" class="sugg" data-q="${esc(q)}">${esc(q)}</button>`).join("")}</div>
    <div id="ro" style="margin-top:32px"></div>
    <section style="margin-top:64px" aria-labelledby="docs-h"><div class="between"><div><h2 id="docs-h" class="t-h2">Documentos da base</h2><p class="t-small t-2" style="margin-top:4px">Atas, briefings, políticas, catálogos de cursos… Tudo que for enviado aqui passa a ser consultado nas respostas.</p></div>
      <label class="btn btn-secondary btn-sm" style="cursor:pointer">${ic("upload", "i-sm")}Adicionar documento<input type="file" id="doc-up" accept=".pdf,.docx,.txt,.md" hidden></label></div>
      <div id="docs" style="margin-top:16px"></div></section></main>`);
  const tipo = (fonte) => (fonte.includes("ao vivo") ? "SGD ao vivo" : fonte.startsWith("SGD") ? "SGD" : fonte.startsWith("VINT Match") ? "Projeto" : fonte.startsWith("InHire") ? "iHiring" : "Documento");
  const desenhaDocs = (docs) => {
    $("#docs").innerHTML = docs?.length ? `<div class="table-box"><table class="table"><thead><tr><th>Documento</th><th>Trechos</th><th>Origem</th><th></th></tr></thead><tbody>${docs.map((d) => `<tr><td>${ic("file", "i-sm")} ${esc(d.nome)}</td><td class="t-num">${d.trechos}</td><td>${d.enviado ? "Enviado pela tela" : "Base do projeto"}</td><td style="text-align:right">${d.enviado && S.me.perfil === "admin" ? `<button class="act danger" data-del="${esc(d.nome)}">Remover</button>` : ""}</td></tr>`).join("")}</tbody></table></div>` : `<p class="t-2">Nenhum documento.</p>`;
    $$("[data-del]").forEach((b) => (b.onclick = async () => { try { await api(`/api/base/documentos/${encodeURIComponent(b.dataset.del)}`, { method: "DELETE" }); toast("Documento removido da base."); pageBase(); } catch (e) { toast(e.message); } }));
  };
  desenhaDocs(f?.documentos);
  $("#doc-up").onchange = async (e) => {
    const file = e.target.files[0]; if (!file) return;
    const fd = new FormData(); fd.append("arquivo", file);
    toast(`Lendo “${file.name}”…`);
    try { await api("/api/base/documentos", { method: "POST", body: fd }); toast(`“${file.name}” adicionado à base.`); pageBase(); } catch (err) { toast(err.message); }
  };
  const ask = async (q) => {
    $("#rq").value = q; $("#ro").innerHTML = `<p class="t-2"><span class="spin"></span> Consultando o banco e os documentos…</p>`;
    try {
      const r = await api("/api/rag", { method: "POST", json: { pergunta: q } });
      $("#ro").innerHTML = `<div class="answer">${esc(r.resposta)}</div>
        <p class="t-cap" style="margin-top:32px">Fontes</p>${r.fontes.map((x, i) => `<div class="src"><div class="row" style="gap:8px;flex-wrap:wrap"><b>[${i + 1}] ${esc(x.secao)}</b><span class="chip chip-origin">${esc(tipo(x.fonte))}</span><span class="t-small t-2">${esc(x.fonte)}</span></div><p class="t-2" style="margin-top:6px;white-space:pre-wrap">${esc(x.texto)}</p></div>`).join("")}`;
    } catch (e) { $("#ro").innerHTML = `<div class="alert alert-error">${ic("alert")}<p>${esc(e.message)}</p></div>`; }
  };
  $("#rf").onsubmit = (e) => { e.preventDefault(); const q = $("#rq").value.trim(); if (q) ask(q); };
  $$("[data-q]").forEach((b) => (b.onclick = () => ask(b.dataset.q)));
}

/* ============================================================ 06 · relatório */
// seções do relatório; "pessoa: true" = só existe no formato detalhado (ficha por pessoa)
const REL_OPCOES = [["descricao", "Descrição do projeto", true], ["kpis", "Resumo em números", true], ["atencao", "Pontos de atenção", true],
  ["cobertura", "Cobertura das skills", true], ["outros", "Outros sugeridos", false],
  ["motivos", "Motivos da escolha", true, true], ["skills", "Skills pedidas", true, true], ["disp", "Disponibilidade mês a mês", false, true],
  ["pdi", "Remanejamento e PDI", true, true]];
const REL_CHAVE = "vm_rel_opts2";
function relOpcoes() {
  let o = {}; try { o = JSON.parse(localStorage.getItem(REL_CHAVE) || "{}"); } catch (_) { /* sem storage */ }
  return { formato: o.formato === "detalhado" ? "detalhado" : "resumido", ...Object.fromEntries(REL_OPCOES.map(([k, , d]) => [k, o[k] ?? d])) };
}
function relSalvar(o) { try { localStorage.setItem(REL_CHAVE, JSON.stringify(o)); } catch (_) { /* sem storage */ } }
function relTabela(pessoas) {
  return `<div class="table-box"><table class="table rel-tabela"><thead><tr><th>Pessoa</th><th style="text-align:right">Dedicação</th><th style="text-align:right">Match</th><th>Situação</th><th>Por que foi escolhido(a)</th></tr></thead><tbody>${pessoas.map((x) => {
    const int = x.origem === "interno";
    const sit = int ? (x.disponivel ? "Disponível" : "Remanejamento") : `iHiring · ${x.disponibilidade_informada}% disp.`;
    return `<tr><td><span class="t-strong">${nm(x.nome)}</span><div class="t-small t-2">${esc([x.cargo, x.senioridade].filter(Boolean).join(" · "))}${int ? "" : " · iHiring"}</div></td>
      <td class="t-num" style="text-align:right">${x.percentual}%</td><td class="t-num" style="text-align:right">${Math.round(x.score)}%</td><td>${esc(sit)}</td><td class="t-small">${esc(x.justificativa || "—")}</td></tr>`;
  }).join("")}</tbody></table></div>`;
}
const pctTxt = (n) => `${n}%`;
const plural = (n, um, varios) => `${n} ${n === 1 ? um : varios}`;
function relPessoa(x, o) {
  const int = x.origem === "interno";
  const papel = [x.cargo, x.senioridade, x.modalidade].filter(Boolean).join(" · ");
  const status = int ? (x.disponivel ? `<span class="status s-ok">${ic("check")}Disponível no período</span>` : `<span class="status s-warn">${ic("warn")}Depende de remanejamento</span>`)
    : `<span class="status s-muted">${ic("info")}Disponibilidade informada: ${x.disponibilidade_informada}%</span>`;
  const motivos = int ? `<ul class="why">${x.motivos.map((m) => `<li>${m.ok ? `<span class="t-ok">${ic("check")}</span>` : `<span class="t-2">${ic("x")}</span>`}<p><span class="t-strong">${esc(m.forte)}</span> ${esc(m.texto)}</p></li>`).join("")}</ul>`
    : `<p>${esc(x.justificativa)}</p>`;
  const skills = `<ul class="chips">${x.skills.map((k) => k.ok ? `<li class="chip chip-skill">${esc(k.nome)}${k.atual ? ` · ${esc(k.atual.toLowerCase())}` : ""}</li>` : `<li class="chip chip-miss">${ic("x")}${esc(k.nome)}${k.atual && k.atual !== "—" ? ` · ${esc(k.atual.toLowerCase())} (pedido ${esc(k.pedido.toLowerCase())})` : ""}</li>`).join("")}</ul>`;
  const disp = int && x.disp_meses?.length ? `<div class="rel-meses">${x.disp_meses.map((m) => `<div><span class="t-cap">${esc(m.mes.split("/")[0])}</span><b class="t-num ${m.disp < (REL.projeto.dedicacao_min || 0) ? "t-warn" : ""}">${m.disp}%</b></div>`).join("")}</div><p class="t-small t-2">Percentual livre em cada mês, segundo o planejamento do SGD.</p>` : "";
  const rem = x.remanejamento ? `<p><span class="t-strong">Remanejamento:</span> liberar ${esc(x.remanejamento.liberar_por_mes.map((r) => `${r.liberar_pct}% em ${r.mes}`).join(", "))} (viabilidade ${esc(x.remanejamento.viabilidade.toLowerCase())})${x.remanejamento.alocacoes.length ? ` — hoje em ${esc(x.remanejamento.alocacoes.join(", "))}` : ""}.</p>` : "";
  const pdi = (x.pdi || []).length || x.pdi_resumo ? `<p><span class="t-strong">PDI sugerido:</span> ${x.pdi_resumo ? esc(x.pdi_resumo) : esc(x.pdi.map((d) => `${d.skill} (${d.de.toLowerCase()} → ${d.para.toLowerCase()})${d.mentor ? `, mentoria com ${d.mentor}` : ""}`).join("; "))}.</p>` : "";
  return `<article class="rel-pessoa">
    <div class="between" style="align-items:flex-start;gap:16px"><div class="row" style="gap:12px;align-items:flex-start"><span class="avatar" aria-hidden="true">${esc(ini(x.nome))}</span><div>
      <div class="row" style="gap:8px;flex-wrap:wrap"><h3 class="t-h2" style="font-size:18px">${nm(x.nome)}</h3><span class="chip chip-origin">${int ? "Interno" : "iHiring"}</span>${int ? "" : '<span class="chip chip-syn">dado de teste</span>'}</div>
      <p class="t-small t-2">${esc(papel)}</p></div></div>
      <div class="rel-nums"><div><b class="t-num">${Math.round(x.score)}%</b><span class="t-cap">match</span></div><div><b class="t-num">${pctTxt(x.percentual)}</b><span class="t-cap">dedicação</span></div></div></div>
    <div class="meta-line" style="margin-top:12px">${status}<span class="t-small t-2">Alocado(a) por ${esc(x.alocado_por || "—")} em ${fmtDate(x.alocado_em)}</span></div>
    ${o.motivos ? `<div class="rel-bloco"><p class="t-cap">Por que foi escolhido(a)</p>${motivos}</div>` : ""}
    ${o.skills ? `<div class="rel-bloco"><p class="t-cap">Skills pedidas</p>${skills}</div>` : ""}
    ${o.disp && disp ? `<div class="rel-bloco"><p class="t-cap">Disponibilidade no período</p>${disp}</div>` : ""}
    ${o.pdi && (rem || pdi) ? `<div class="rel-bloco">${rem}${pdi}</div>` : ""}
  </article>`;
}
let REL = null;
function relCorpo() {
  const r = REL, o = relOpcoes(), pj = r.projeto, rs = r.resumo;
  const periodo = pj.inicio ? `${fmtDia(pj.inicio)} → ${fmtDia(pj.fim)} (${plural(pj.duracao_meses, "mês", "meses")})` : esc(pj.periodo || "—");
  const filtros = [pj.tipo_servico && `Tipo de serviço: ${pj.tipo_servico}`, pj.metodologia && `Metodologia: ${pj.metodologia}`, pj.senioridades.length && `Senioridade: ${pj.senioridades.join(", ")}`, pj.briefing && `Briefing: ${pj.briefing}`].filter(Boolean);
  const cobertura = `<div class="table-box"><table class="table"><thead><tr><th>Skill</th><th>Nível pedido</th><th>Quem atende no time</th></tr></thead><tbody>${r.cobertura.map((c) => `<tr><td><span class="t-strong">${esc(c.skill)}</span>${c.obrigatoria ? "" : ' <span class="t-2">(desejável)</span>'}</td><td>${esc(c.nivel)}</td><td>${c.atendida_por.length ? esc(c.atendida_por.map((q) => q.nivel ? `${q.nome} (${q.nivel.toLowerCase()})` : q.nome).join(", ")) : `<span class="t-err">${ic("alert", "i-sm")} ninguém no nível pedido</span>`}${c.abaixo_do_nivel.length ? `<div class="t-small t-2">Abaixo do nível: ${esc(c.abaixo_do_nivel.join(", "))}</div>` : ""}</td></tr>`).join("")}</tbody></table></div>`;
  const outros = r.outros_sugeridos.length ? `<div class="table-box"><table class="table"><thead><tr><th>Nome</th><th>Cargo</th><th style="text-align:right">Match</th><th>Situação</th></tr></thead><tbody>${r.outros_sugeridos.map((c) => `<tr><td>${nm(c.nome)}</td><td>${esc(c.cargo || "—")}</td><td class="t-num" style="text-align:right">${Math.round(c.score)}%</td><td>${c.disponivel ? "Disponível" : "Remanejamento"}</td></tr>`).join("")}</tbody></table></div>` : `<p class="t-2">Não há outros sugeridos.</p>`;
  return `<header class="rel-cab"><div class="between" style="align-items:flex-start"><div><p class="t-cap">VINT Match · Relatório de alocação</p><h1 class="t-display" style="margin-top:8px">${esc(pj.nome)}</h1></div>
      <p class="t-small t-2" style="text-align:right">Gerado em ${fmtDate(r.gerado_em, true)}<br>por ${esc(S.me.nome)}</p></div>
    <dl class="rel-ficha"><div><dt>Período</dt><dd>${periodo}</dd></div><div><dt>Dedicação mínima</dt><dd>${pj.dedicacao_min}% por pessoa</dd></div><div><dt>Responsável pela busca</dt><dd>${esc(pj.autor || "—")}</dd></div><div><dt>Ranking</dt><dd>${pj.ia_usada ? "Regras + refinamento por IA" : "Regras (skills, histórico, disponibilidade)"}</dd></div></dl>
    ${o.descricao && pj.descricao ? `<p style="margin-top:16px;max-width:760px">${esc(pj.descricao)}</p>` : ""}
    ${o.descricao && filtros.length ? `<p class="t-small t-2" style="margin-top:8px">${esc(filtros.join(" · "))}</p>` : ""}</header>
  ${!o.kpis ? "" : `<section class="rel-kpis" aria-label="Resumo"><div><b class="t-num">${rs.total}</b><span>${rs.total === 1 ? "pessoa alocada" : "pessoas alocadas"}</span><small>${plural(rs.internos, "interno", "internos")} · ${rs.externos} iHiring</small></div>
    <div><b class="t-num">${rs.skills_cobertas}/${rs.skills_total}</b><span>skills cobertas</span><small>no nível pedido</small></div>
    <div><b class="t-num">${rs.dedicacao_media ?? Math.round(rs.dedicacao_total / Math.max(rs.total, 1))}%</b><span>dedicação média</span><small>${(() => { const fte = Math.round(rs.dedicacao_total / 10) / 10; return `equivale a ${fte.toLocaleString("pt-BR")} ${fte === 1 ? "pessoa" : "pessoas"} em tempo integral`; })()}</small></div>
    <div><b class="t-num">${rs.remanejamento}</b><span>${rs.remanejamento === 1 ? "remanejamento" : "remanejamentos"}</span><small>a combinar com gestores</small></div></section>`}
  ${o.atencao && r.atencao.length ? `<section class="rel-sec"><h2 class="t-h1">Pontos de atenção</h2><ul class="rel-atencao">${r.atencao.map((a) => `<li>${ic("warn", "i-sm")}<span>${esc(a)}</span></li>`).join("")}</ul></section>` : ""}
  <section class="rel-sec"><h2 class="t-h1">Time alocado</h2>${o.formato === "detalhado" ? r.pessoas.map((x) => relPessoa(x, o)).join("") : relTabela(r.pessoas)}</section>
  ${o.cobertura ? `<section class="rel-sec"><h2 class="t-h1">Cobertura das skills</h2>${cobertura}</section>` : ""}
  ${o.outros ? `<section class="rel-sec"><h2 class="t-h1">Outros sugeridos</h2><p class="t-2" style="margin-bottom:12px">Alternativas do ranking que não foram alocadas.</p>${outros}</section>` : ""}
  <footer class="rel-rodape">Documento interno · contém dados pessoais de colaboradores — compartilhe só com quem precisa (LGPD). Fonte: SGD${r.pessoas.some((x) => x.origem === "ihiring") ? " e iHiring (base de teste sintética)" : ""}.</footer>`;
}
function relTexto() {
  const r = REL, pj = r.projeto;
  const linhas = [`Relatório de alocação — ${pj.nome}`, `Período: ${pj.inicio ? `${fmtDia(pj.inicio)} a ${fmtDia(pj.fim)}` : pj.periodo} · dedicação mínima ${pj.dedicacao_min}%`, "",
    `Time (${r.resumo.total}):`, ...r.pessoas.map((x) => `• ${x.nome} — ${[x.cargo, x.senioridade].filter(Boolean).join(", ")} · ${x.percentual}% · match ${Math.round(x.score)}%${x.remanejamento ? " · depende de remanejamento" : ""}\n  Motivo: ${x.justificativa || "—"}`),
    "", `Skills cobertas: ${r.resumo.skills_cobertas}/${r.resumo.skills_total}`];
  if (r.atencao.length) linhas.push("", "Pontos de atenção:", ...r.atencao.map((a) => `• ${a}`));
  return linhas.join("\n");
}
function relCsv() {
  const q = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const cab = ["Nome", "Origem", "Cargo", "Senioridade", "Dedicação (%)", "Match (%)", "Situação", "Skills atendidas", "Lacunas", "Motivo", "Alocado por", "Alocado em"];
  const linhas = REL.pessoas.map((x) => [x.nome, x.origem === "interno" ? "Interno (SGD)" : "iHiring", x.cargo, x.senioridade, x.percentual, Math.round(x.score),
    x.origem === "interno" ? (x.disponivel ? "Disponível" : "Remanejamento") : `Disponibilidade informada ${x.disponibilidade_informada}%`,
    x.skills.filter((k) => k.ok).map((k) => k.nome).join(", "), x.skills.filter((k) => !k.ok).map((k) => k.nome).join(", "), x.justificativa, x.alocado_por, fmtDate(x.alocado_em)]);
  return "﻿" + [cab, ...linhas].map((l) => l.map(q).join(";")).join("\r\n");
}
async function pageRelatorio(id) {
  loadingView("buscas");
  try { REL = await api(`/api/buscas/${id}/relatorio`); } catch (e) { return errorView("buscas", e); }
  const pj = REL.projeto, o = relOpcoes();
  shell("buscas", `<main class="wrap" style="flex:1;padding-bottom:96px">
    <div class="no-print">${band(`${crumbs([["Buscas", "#/buscas"], [pj.nome, `#/buscas/${id}`], ["Relatório"]])}
      <div class="between" style="margin-top:24px;row-gap:16px;align-items:flex-end"><div><h1 class="t-display">Relatório do projeto</h1><p class="t-2" style="margin-top:8px;max-width:560px">Pessoas alocadas, motivos da escolha e pontos de atenção. Na hora de imprimir você escolhe o formato e o que entra.</p></div>
      <div class="row" style="gap:8px;flex-wrap:wrap"><button type="button" class="btn btn-ghost btn-sm" id="rel-copy">${ic("copy", "i-sm")}Copiar resumo</button><button type="button" class="btn btn-secondary btn-sm" id="rel-csv">${ic("download", "i-sm")}Baixar planilha (CSV)</button><button type="button" class="btn btn-primary btn-sm" id="rel-print">${ic("printer", "i-sm")}Imprimir / salvar PDF</button></div></div>
      <div class="rel-opcoes"><span class="t-cap">Formato</span><div class="quick" id="rel-fmt" style="margin:0">${[["resumido", "Resumido"], ["detalhado", "Detalhado"]].map(([v, l]) => `<button type="button" class="sugg" data-fmt="${v}" aria-pressed="${o.formato === v}">${l}</button>`).join("")}</div>
        <button type="button" class="btn btn-ghost btn-sm" id="rel-secoes">${ic("pencil", "i-sm")}Escolher o que entra</button><span class="t-small t-2" id="rel-conta"></span></div>`)}</div>
    ${REL.pessoas.length ? `<article class="rel" id="rel-doc"></article>` : `<div class="empty-box" style="margin-top:40px">${ic("info")}<div><p class="t-strong">Ainda não há pessoas alocadas neste projeto.</p><p class="t-2">Abra o <a href="#/buscas/${id}">resultado</a>, selecione as pessoas e confirme. Depois volte aqui para gerar o relatório.</p></div></div>`}
  </main>`);
  const desenha = () => {
    const at = relOpcoes();
    if ($("#rel-doc")) $("#rel-doc").innerHTML = relCorpo();
    $$("#rel-fmt [data-fmt]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.fmt === at.formato)));
    const n = REL_OPCOES.filter(([k, , , porPessoa]) => at[k] && (!porPessoa || at.formato === "detalhado")).length;
    if ($("#rel-conta")) $("#rel-conta").textContent = `${n} ${n === 1 ? "seção" : "seções"} incluída${n === 1 ? "" : "s"}`;
  };
  desenha();
  $("#rel-fmt").onclick = (e) => { const b = e.target.closest("[data-fmt]"); if (!b) return; relSalvar({ ...relOpcoes(), formato: b.dataset.fmt }); desenha(); };
  const imprimir = () => {
    const tema = document.documentElement.dataset.theme;
    document.documentElement.dataset.theme = "light"; // papel sempre no tema claro
    const volta = () => { document.documentElement.dataset.theme = tema; window.removeEventListener("afterprint", volta); };
    window.addEventListener("afterprint", volta);
    document.title = `Vint_Match — Relatório — ${pj.nome}`;
    window.print();
  };
  // janela de opções: escolhe formato e seções; com "imprimir", imprime em seguida
  const escolher = (paraImprimir) => {
    const o0 = relOpcoes();
    const caixa = (k, l, porPessoa) => `<label class="check" style="min-height:36px"><input type="checkbox" data-op="${k}" ${o0[k] ? "checked" : ""} ${porPessoa && o0.formato !== "detalhado" ? "disabled" : ""}> ${esc(l)}</label>`;
    modal(`<h2 id="m-title" class="t-h1">${paraImprimir ? "O que vai na impressão?" : "O que entra no relatório?"}</h2>
      <p class="t-2" style="margin-top:4px">A escolha fica salva para os próximos relatórios.</p>
      <fieldset class="rel-modal-grupo"><legend class="t-cap">Formato</legend>
        <label class="radio-card"><input type="radio" name="rel-f" value="resumido" ${o0.formato === "resumido" ? "checked" : ""}><span><b>Resumido</b><br><span class="t-small t-2">O time numa tabela, uma linha por pessoa. Cabe em 1–2 páginas.</span></span></label>
        <label class="radio-card"><input type="radio" name="rel-f" value="detalhado" ${o0.formato === "detalhado" ? "checked" : ""}><span><b>Detalhado</b><br><span class="t-small t-2">Uma ficha por pessoa, com os detalhes marcados abaixo.</span></span></label></fieldset>
      <fieldset class="rel-modal-grupo"><legend class="t-cap">Seções</legend><div class="rel-modal-cols">${REL_OPCOES.filter((x) => !x[3]).map(([k, l]) => caixa(k, l)).join("")}</div></fieldset>
      <fieldset class="rel-modal-grupo" id="rel-pp"><legend class="t-cap">Em cada pessoa <span style="text-transform:none;letter-spacing:0">(só no detalhado)</span></legend><div class="rel-modal-cols">${REL_OPCOES.filter((x) => x[3]).map(([k, l]) => caixa(k, l, true)).join("")}</div></fieldset>
      <div class="row" style="justify-content:space-between;gap:8px;margin-top:24px;flex-wrap:wrap"><div class="row" style="gap:6px"><button type="button" class="btn btn-ghost btn-sm" data-preset="enxuto">Só o essencial</button><button type="button" class="btn btn-ghost btn-sm" data-preset="tudo">Tudo</button></div>
        <div class="row" style="gap:8px"><button type="button" class="btn btn-ghost" data-close>Cancelar</button><button type="button" class="btn btn-primary" id="rel-ok">${paraImprimir ? `${ic("printer", "i-sm")}Imprimir / salvar PDF` : "Aplicar"}</button></div></div>`,
    (root, close) => {
      const ler = () => {
        const o = { formato: $("input[name=rel-f]:checked", root).value };
        $$("[data-op]", root).forEach((c) => (o[c.dataset.op] = c.checked));
        $$("#rel-pp input", root).forEach((c) => (c.disabled = o.formato !== "detalhado"));
        return o;
      };
      const aplica = () => { relSalvar(ler()); desenha(); }; // a página atrás já mostra o resultado
      root.addEventListener("change", aplica);
      $$("[data-preset]", root).forEach((b) => (b.onclick = () => {
        const tudo = b.dataset.preset === "tudo";
        $(`input[name=rel-f][value=${tudo ? "detalhado" : "resumido"}]`, root).checked = true;
        $$("[data-op]", root).forEach((c) => (c.checked = tudo || ["kpis", "atencao"].includes(c.dataset.op)));
        aplica();
      }));
      $("#rel-ok", root).onclick = () => { aplica(); close(); if (paraImprimir) setTimeout(imprimir, 150); };
    });
  };
  const vazio = !REL.pessoas.length;
  ["#rel-copy", "#rel-csv", "#rel-print", "#rel-secoes"].forEach((sel) => ($(sel).disabled = vazio));
  $("#rel-print").onclick = () => escolher(true);
  $("#rel-secoes").onclick = () => escolher(false);
  $("#rel-csv").onclick = () => {
    const url = URL.createObjectURL(new Blob([relCsv()], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = `relatorio_${chaveArquivo(pj.nome)}.csv`; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };
  $("#rel-copy").onclick = async () => {
    try { await navigator.clipboard.writeText(relTexto()); toast("Resumo copiado. Cole no e-mail ou no Teams."); }
    catch (_) { toast("Não consegui copiar automaticamente. Use Imprimir / salvar PDF."); }
  };
}
const chaveArquivo = (n) => fold(n).replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "projeto";

/* ============================================================ roteador */
async function ensureSession() {
  if (S.me && S.meta) return true;
  try { S.me = await api("/api/me"); S.meta = await api("/api/meta"); return true; }
  catch (_) { return false; }
}
async function render() {
  $("#modal-root").innerHTML = "";
  const raw = location.hash.replace(/^#/, "") || "/";
  const [path, qs] = raw.split("?");
  const params = new URLSearchParams(qs || "");
  const parts = path.split("/").filter(Boolean);
  document.title = "Vint_Match";
  if (parts[0] === "login") return pageLogin();
  if (parts[0] === "primeiro-acesso") return pagePrimeiroAcesso(params);
  if (!(await ensureSession())) return go("#/login");
  try {
    if (!parts.length) return pageDashboard();
    if (parts[0] === "buscas") {
      if (!parts[1]) return pageBuscas();
      if (parts[1] === "nova") return pageNovaBusca(params);
      if (parts[2] === "relatorio") return pageRelatorio(+parts[1]);
      if (parts.length >= 4) return pageDetalhe(+parts[1], parts[2], +parts[3]);
      return pageResultado(+parts[1]);
    }
    if (parts[0] === "usuarios") return pageUsuarios();
    if (parts[0] === "perfil") return pagePerfil();
    if (parts[0] === "base") return pageBase();
    errorView("inicio", new Error("Página não encontrada."));
  } catch (e) { errorView("inicio", e); }
}
window.addEventListener("hashchange", render);
render();
