// Review page. Plain JS, no framework. Every action is saved at once through a queue that
// keeps the order of clicks; the server keeps the last verdict per (document, value).
"use strict";

const STANCES = ["endorse", "reject", "mention"];
const STANCE_LABEL = { endorse: "+ endorse", reject: "− reject", mention: "~ mention", contested: "± contested" };
const VERDICT = { CORRECT: "correct", NOT_PRESENT: "not_present", WRONG_CALL: "wrong_call", ADDED: "added" };
// Mirrors of the server's StrEnums (Verdict, RowKind, ReviewMode).
const KIND = { MODEL: "model", OWNER: "owner" };
const MODE = { REVIEW: "review", BLIND: "blind" };
const NOTE_DELAY_MS = 600;
const RETRY_MS = 3000;

const state = {
  mode: MODE.REVIEW,
  documents: [],
  index: 0,
  multiRun: false,
  doc: null,           // the /api/doc payload on screen
  selected: null,      // row_id
  cursor: {},          // row_id -> index of the quote last scrolled to
  picker: null,        // row_id whose stance picker is open
  addValue: null,      // value_id chosen in the add panel
  queue: [],
  saving: false,
  failed: false,
  refused: null,       // why the server refused the last change, until the next one
  retryTimer: null,
  noteTimer: null,
};

const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k === "color") node.style.setProperty("--c", `var(--hl-${v})`);
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children) if (c !== null && c !== undefined) node.append(c);
  return node;
}

async function getJSON(url) {
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}

// ---------- saving ----------

function setStatus(kind, message) {
  const s = $("save-status");
  s.dataset.state = kind;
  const short = message && message.length > 60 ? `${message.slice(0, 57)}…` : message;
  s.textContent = { saved: "Saved ✓", saving: "Saving…", failed: "Not saved – retrying",
    refused: `Not saved: ${short || "refused"}` }[kind];
  s.title = message || (kind === "failed" ? "Click to retry now" : "Every action saves at once");
}

function enqueue(url, body, onDone) {
  // A note waiting for its turn is replaced by the newer text of the same article.
  if (url === "/api/note") {
    const waiting = state.queue.findIndex((j, i) => (i > 0 || !state.saving) && j.url === url && j.body.document_id === body.document_id);
    if (waiting >= 0) state.queue.splice(waiting, 1);
  }
  state.queue.push({ url, body, onDone });
  state.refused = null;
  pump();
}

async function pump() {
  if (state.saving || state.failed) return;
  const job = state.queue[0];
  if (!job) {
    if (state.refused) setStatus("refused", state.refused);
    else setStatus("saved");
    return;
  }
  state.saving = true;
  setStatus("saving");
  let retry = false;
  try {
    const r = await fetch(job.url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(job.body),
    });
    const data = await r.json().catch(() => ({}));
    if (r.ok) {
      state.queue.shift();
      if (job.onDone) job.onDone(data);
    } else if (r.status >= 400 && r.status < 500) {
      state.queue.shift();          // a 4xx is final: saving it again will not help
      state.refused = data.error || `HTTP ${r.status}`;
      reloadDoc();                  // show what is really stored
    } else {
      retry = true;                 // 5xx: the server may recover
    }
  } catch (_) {
    retry = true;                   // server stopped or network error: keep the job
  }
  state.saving = false;
  if (retry) {
    state.failed = true;
    setStatus("failed");
    clearTimeout(state.retryTimer);
    state.retryTimer = setTimeout(retryNow, RETRY_MS);
    return;
  }
  pump();
}

function retryNow() {
  clearTimeout(state.retryTimer);
  state.failed = false;
  pump();
}

function pendingWork() {
  return state.queue.length > 0 || state.noteTimer !== null;
}

// ---------- verdicts ----------

// The owner's answer implied by a verdict: the stance present, or null for absent.
function presentStance(verdict, modelStance, corrected) {
  if (verdict === VERDICT.CORRECT) return modelStance;
  if (verdict === VERDICT.NOT_PRESENT) return null;
  return corrected;
}

// Show a new answer for a value on every model row of it (blind mode can have several).
function applyAnswer(valueId, present) {
  for (const row of state.doc.rows) {
    if (row.value_id !== valueId || row.kind !== KIND.MODEL) continue;
    row.verdict_stance = present;
    if (present === null) row.verdict = VERDICT.NOT_PRESENT;
    else row.verdict = present === row.stance ? VERDICT.CORRECT : VERDICT.WRONG_CALL;
  }
}

function sendVerdict(row, verdict, corrected = null) {
  const docId = state.doc.document_id;
  const body = {
    document_id: docId,
    value_id: row.value_id,
    verdict,
    model_stance: row.kind === KIND.MODEL ? row.stance : null,
    corrected_stance: corrected,
  };
  if (row.kind === KIND.MODEL) {
    applyAnswer(row.value_id, presentStance(verdict, row.stance, corrected));
    renderRows();
  }
  enqueue("/api/verdict", body, (data) => tableSaved(docId, data));
}

function tableSaved(docId, data) {
  // Intermediate answers of quick clicks are skipped: only the last one is drawn.
  if (!state.doc || state.doc.document_id !== docId) return;
  if (state.queue.some((j) => j.url === "/api/verdict")) return;
  const spans = Object.fromEntries(state.doc.rows.map((r) => [r.row_id, r.spans]));
  state.doc.rows = data.rows.map((r) => ({ ...r, spans: spans[r.row_id] ?? r.spans }));
  state.doc.addable = data.addable;
  renderRows();
  renderAdd();
  updateProgress();
}

function addValue(valueId, stance) {
  const docId = state.doc.document_id;
  closeAdd();
  enqueue("/api/verdict", {
    document_id: docId, value_id: valueId, verdict: VERDICT.ADDED,
    model_stance: null, corrected_stance: stance,
  }, (data) => { tableSaved(docId, data); select(`o|${valueId}`, { scroll: false }); });
}

// ---------- notes ----------

function noteChanged() {
  clearTimeout(state.noteTimer);
  state.noteTimer = setTimeout(flushNote, NOTE_DELAY_MS);
  setStatus("saving");
}

function flushNote() {
  if (state.noteTimer === null || !state.doc) return;
  clearTimeout(state.noteTimer);
  state.noteTimer = null;
  const docId = state.doc.document_id;
  const note = $("note").value;
  state.doc.note = note;
  enqueue("/api/note", { document_id: docId, note });
}

// ---------- rendering ----------

function renderHeader(items) {
  const settings = $("run-settings");
  settings.replaceChildren();
  if (items.mode === MODE.BLIND) {
    settings.append(el("span", { class: "blind-badge", title: "Tags from every run, without saying which run proposed them", text: "Blind pass" }));
    return;
  }
  const s = items.settings;
  settings.append(el("span", { class: "setting", title: "framework / level", text: `${s.framework_id} / ${s.level_id}` }));
  for (const run of s.runs) {
    const parts = [run.model || run.kind, run.effort && `${run.effort} effort`, run.unit, run.few_shot ? "few-shot" : null, run.batch ? "batch" : null];
    settings.append(el("span", { class: "setting", title: `run ${run.run_id} (${run.status})`, text: parts.filter(Boolean).join(" · ") }));
  }
}

function renderMeta(doc) {
  const m = doc.meta;
  const facts = [["Country", m.country], ["Source", m.source_id], ["Genre", m.genre], ["Date", m.date]];
  $("doc-meta").replaceChildren(...facts.filter(([, v]) => v).map(([k, v]) =>
    el("li", { class: "fact" }, el("span", { class: "fact-label", text: k }), v)));
  $("title").textContent = m.title || doc.document_id;
  const byline = [doc.document_id];
  if (m.language) byline.push(`language: ${m.language}`);
  $("byline").replaceChildren(byline.join(" · "));
  if (m.url) $("byline").append(" · ", el("a", { href: m.url, target: "_blank", rel: "noopener noreferrer", text: "original ↗" }));
  $("position").textContent = `Article ${doc.index} / ${doc.total}`;
  $("prev").disabled = state.index <= 0;
  $("next").disabled = state.index >= state.documents.length - 1;
  document.title = `${doc.index}/${doc.total} · Value review`;
}

function renderArticle(doc) {
  const box = $("article");
  box.classList.remove("focusing");
  box.lang = doc.meta.language || "";
  $("text-error").hidden = !doc.text_error;
  $("text-error").textContent = doc.text_error ? `Text not available: ${doc.text_error}` : "";
  const rowsById = doc.rows;
  const frag = document.createDocumentFragment();
  for (const piece of doc.pieces) {
    let node = document.createTextNode(piece.t);
    // innermost = highest lane, so every mark keeps its own underline offset
    for (const [rowIdx, span, lane] of [...piece.m].reverse()) {
      const row = rowsById[rowIdx];
      const wrap = el("span", { class: "hl", color: row.color, "data-row": row.row_id, "data-span": span });
      wrap.style.setProperty("--lane", lane);
      wrap.append(node);
      node = wrap;
    }
    frag.append(node);
  }
  box.replaceChildren(frag);
}

function evidenceText(row) {
  if (row.kind === KIND.OWNER) return el("div", { class: "evidence", text: "your tag (not proposed here)" });
  if (!row.spans) return el("div", { class: "evidence none", text: "no quote found" });
  const n = row.spans;
  let text = n === 1 ? "1 quote" : `${n} quotes`;
  if (state.selected === row.row_id && n > 1) text = `quote ${(state.cursor[row.row_id] ?? 0) + 1} of ${n} · click again for the next`;
  if (row.evidence_unresolved) text += " · some not found";
  return el("div", { class: "evidence", text });
}

function outcome(row) {
  if (row.kind === KIND.OWNER) return el("span", { class: "outcome added", text: `added: ${row.verdict_stance}` });
  switch (row.verdict) {
    case VERDICT.CORRECT: return el("span", { class: "outcome correct", text: "correct" });
    case VERDICT.NOT_PRESENT: return el("span", { class: "outcome absent", text: "not present" });
    case VERDICT.WRONG_CALL: return el("span", { class: "outcome wrong", text: `actually ${row.verdict_stance}` });
    default: return el("span", { class: "outcome", text: "not judged" });
  }
}

function verdictButtons(row) {
  const stop = (fn) => (ev) => { ev.stopPropagation(); select(row.row_id, { scroll: false, cycle: false }); fn(); };
  if (row.kind === KIND.OWNER) {
    return [
      el("button", { type: "button", class: "v v-text wrong", title: "Change the stance", "aria-expanded": state.picker === row.row_id ? "true" : "false",
        onclick: stop(() => togglePicker(row.row_id)) }, "⟲ stance"),
      el("button", { type: "button", class: "v v-text absent", title: "Remove this value",
        onclick: stop(() => sendVerdict(row, VERDICT.NOT_PRESENT)) }, "✗ remove"),
    ];
  }
  const pressed = (v) => (row.verdict === v ? "true" : "false");
  return [
    el("button", { type: "button", class: "v correct", title: "Correct (1)", "aria-label": "Correct", "aria-pressed": pressed(VERDICT.CORRECT),
      onclick: stop(() => { closePicker(); sendVerdict(row, VERDICT.CORRECT); }) }, "✓"),
    el("button", { type: "button", class: "v absent", title: "Not present (2)", "aria-label": "Not present", "aria-pressed": pressed(VERDICT.NOT_PRESENT),
      onclick: stop(() => { closePicker(); sendVerdict(row, VERDICT.NOT_PRESENT); }) }, "✗"),
    el("button", { type: "button", class: "v wrong", title: "Wrong call: pick the right stance (3)", "aria-label": "Wrong call",
      "aria-pressed": pressed(VERDICT.WRONG_CALL), "aria-expanded": state.picker === row.row_id ? "true" : "false",
      onclick: stop(() => togglePicker(row.row_id)) }, "⟲"),
  ];
}

function picker(row) {
  const current = row.kind === KIND.OWNER ? row.verdict_stance : row.stance;
  const question = row.kind === KIND.OWNER ? "Change the stance to:" : `The model said ${row.stance}. The text actually:`;
  const choices = STANCES.map((s) => el("button", {
    type: "button", class: "stance-pick", "data-stance": s,
    disabled: s === current, "aria-pressed": row.verdict_stance === s && row.verdict !== VERDICT.CORRECT ? "true" : "false",
    onclick: (ev) => { ev.stopPropagation(); pickStance(row, s); },
  }, STANCE_LABEL[s]));
  return el("div", { class: "picker", onclick: (ev) => ev.stopPropagation() },
    el("p", { text: question }), el("div", { class: "stance-choices", role: "group", "aria-label": "Stance" }, ...choices));
}

function pickStance(row, stance) {
  closePicker();
  if (row.kind === KIND.OWNER) sendVerdict(row, VERDICT.ADDED, stance);
  else sendVerdict(row, VERDICT.WRONG_CALL, stance);
}

function renderRows() {
  const doc = state.doc;
  const list = $("rows");
  list.replaceChildren(...doc.rows.map((row) => {
    const stanceBadge = row.kind === KIND.MODEL
      ? el("span", { class: `stance ${row.stance}`, title: "the model's stance", text: STANCE_LABEL[row.stance] || row.stance })
      : el("span", { class: `stance ${row.verdict_stance}`, title: "your stance", text: STANCE_LABEL[row.verdict_stance] });
    const runs = row.source_runs && state.multiRun ? el("div", { class: "runs", text: `from ${row.source_runs.join(", ")}` }) : null;
    const li = el("li", {
      class: ["row", row.verdict ? "judged" : "", state.selected === row.row_id ? "selected" : ""].join(" ").trim(),
      color: row.color, "data-row": row.row_id, tabindex: "0",
      onclick: () => select(row.row_id, { cycle: true }),
      onkeydown: (ev) => { if (ev.key === "Enter" && ev.target === li) select(row.row_id, { cycle: true }); },
    },
      el("div", { class: "row-main" },
        el("span", { class: "chip", "aria-hidden": "true" }),
        el("div", { class: "row-text" },
          el("div", { class: "row-title" }, el("span", { class: "vname", text: row.name }), stanceBadge),
          el("div", { class: "vdef", text: row.definition }),
          evidenceText(row), runs)),
      el("div", { class: "verdicts" }, ...verdictButtons(row), outcome(row)),
      state.picker === row.row_id ? picker(row) : null);
    return li;
  }));
  $("no-rows").hidden = doc.rows.length > 0;
  updateProgress();
}

function updateProgress() {
  const model = state.doc.rows.filter((r) => r.kind === KIND.MODEL);
  const judged = model.filter((r) => r.verdict).length;
  $("progress").textContent = model.length ? `${judged} / ${model.length} judged` : "";
}

function renderAdd() {
  const filter = $("add-filter").value.trim().toLowerCase();
  const items = state.doc.addable.filter((v) => !filter || v.name.toLowerCase().includes(filter) || v.value_id.includes(filter));
  $("add-list").replaceChildren(...items.map((v) => el("li", {},
    el("button", {
      type: "button", class: "add-item", color: v.color, "aria-pressed": state.addValue === v.value_id ? "true" : "false",
      onclick: () => chooseAdd(v),
    },
      el("span", { class: "chip", "aria-hidden": "true" }),
      el("span", { class: "row-text" }, el("span", { class: "vname", text: v.name }), el("span", { class: "vdef", text: v.definition }))))));
  const hint = state.doc.addable.length === 0 ? "Every value is already tagged here."
    : items.length === 0 ? "No value matches." : state.mode === MODE.BLIND ? "Values judged earlier are not listed." : "";
  $("add-hint").textContent = hint;
}

// ---------- interaction ----------

function select(rowId, { scroll = true, cycle = false } = {}) {
  const box = $("article");
  const wasSelected = state.selected === rowId;
  state.selected = rowId;
  for (const n of box.querySelectorAll(".hl.focus")) n.classList.remove("focus", "current");
  const marks = box.querySelectorAll(`.hl[data-row="${CSS.escape(rowId)}"]`);
  box.classList.toggle("focusing", marks.length > 0);
  for (const n of marks) n.classList.add("focus");
  const row = state.doc.rows.find((r) => r.row_id === rowId);
  if (row && row.spans && scroll !== false) {
    let k = state.cursor[rowId] ?? 0;
    if (cycle && wasSelected) k = (k + 1) % row.spans;
    state.cursor[rowId] = k;
    const target = box.querySelector(`.hl[data-row="${CSS.escape(rowId)}"][data-span="${k}"]`);
    if (target) {
      for (const n of box.querySelectorAll(`.hl[data-row="${CSS.escape(rowId)}"][data-span="${k}"]`)) n.classList.add("current");
      const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      target.scrollIntoView({ block: "center", behavior: smooth ? "smooth" : "auto" });
    }
  }
  renderRows();
  const li = $("rows").querySelector(`[data-row="${CSS.escape(rowId)}"]`);
  if (li) li.scrollIntoView({ block: "nearest" });
}

function clearSelection() {
  state.selected = null;
  closePicker(false);
  const box = $("article");
  box.classList.remove("focusing");
  for (const n of box.querySelectorAll(".hl.focus")) n.classList.remove("focus", "current");
  renderRows();
}

function togglePicker(rowId) {
  state.picker = state.picker === rowId ? null : rowId;
  renderRows();
}

function closePicker(render = true) {
  if (state.picker === null) return;
  state.picker = null;
  if (render) renderRows();
}

function openAdd() {
  $("add-panel").hidden = false;
  $("add-btn").setAttribute("aria-expanded", "true");
  state.addValue = null;
  $("add-stance").hidden = true;
  renderAdd();
  $("add-filter").focus();
}

function closeAdd() {
  $("add-panel").hidden = true;
  $("add-btn").setAttribute("aria-expanded", "false");
  $("add-filter").value = "";
  state.addValue = null;
}

function chooseAdd(v) {
  state.addValue = v.value_id;
  $("add-name").textContent = v.name;
  $("add-stance").hidden = false;
  renderAdd();
  $("add-stance").querySelector(".stance-pick").focus();
}

async function loadDoc(index) {
  flushNote();
  index = Math.max(0, Math.min(index, state.documents.length - 1));
  state.index = index;
  const docId = state.documents[index].document_id;
  let doc;
  try {
    doc = await getJSON(`/api/doc/${encodeURIComponent(docId)}`);
  } catch (e) {
    $("title").textContent = "Could not load the article";
    $("text-error").hidden = false;
    $("text-error").textContent = String(e.message || e);
    return;
  }
  if (state.documents[state.index].document_id !== docId) return; // a newer navigation won
  state.doc = doc;
  state.selected = null;
  state.picker = null;
  state.cursor = {};
  history.replaceState(null, "", `#${index + 1}`);
  renderMeta(doc);
  renderArticle(doc);
  renderRows();
  closeAdd();
  renderAdd();
  $("note").value = doc.note;
  window.scrollTo({ top: 0 });
}

function reloadDoc() {
  if (state.doc) loadDoc(state.index);
}

function go(delta) {
  const next = state.index + delta;
  if (next >= 0 && next < state.documents.length) loadDoc(next);
}

function rowAt(offset) {
  const rows = state.doc.rows;
  if (!rows.length) return null;
  const i = rows.findIndex((r) => r.row_id === state.selected);
  if (i < 0) return rows[offset > 0 ? 0 : rows.length - 1];
  return rows[(i + offset + rows.length) % rows.length];
}

function onKey(ev) {
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  const typing = ev.target.closest("input, textarea, select");
  if (ev.key === "Escape") {
    if (typing) ev.target.blur();
    if (!$("add-panel").hidden) closeAdd();
    else if (state.picker) closePicker();
    else clearSelection();
    return;
  }
  if (typing || !state.doc) return;
  const row = state.doc.rows.find((r) => r.row_id === state.selected);
  const key = ev.key.toLowerCase();
  if (key === "arrowleft") go(-1);
  else if (key === "arrowright") go(1);
  else if (key === "j" || key === "k") {
    const next = rowAt(key === "j" ? 1 : -1);
    if (next) select(next.row_id);
  } else if (key === "a") { ev.preventDefault(); openAdd(); }
  else if (row && state.picker === row.row_id && "erm".includes(key) && key.length === 1) {
    const stance = { e: "endorse", r: "reject", m: "mention" }[key];
    const current = row.kind === KIND.OWNER ? row.verdict_stance : row.stance;
    if (stance !== current) pickStance(row, stance);
  } else if (row && row.kind === KIND.MODEL && key === "1") { closePicker(); sendVerdict(row, VERDICT.CORRECT); }
  else if (row && row.kind === KIND.MODEL && key === "2") { closePicker(); sendVerdict(row, VERDICT.NOT_PRESENT); }
  else if (row && key === "3") togglePicker(row.row_id);
  else if (row && row.kind === KIND.OWNER && key === "2") sendVerdict(row, VERDICT.NOT_PRESENT);
  else return;
  ev.preventDefault();
}

// ---------- theme ----------

const THEMES = ["auto", "light", "dark"];

function applyTheme(theme) {
  if (theme === "auto") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = theme;
  $("theme").title = theme === "auto" ? "Theme: follows the system" : `Theme: ${theme}`;
  $("theme").textContent = { auto: "◐", light: "☀", dark: "☾" }[theme];
}

function initTheme() {
  let theme = new URLSearchParams(location.search).get("theme");
  if (!THEMES.includes(theme)) {
    try { theme = localStorage.getItem("review-theme"); } catch (_) { theme = null; }
  }
  applyTheme(THEMES.includes(theme) ? theme : "auto");
  $("theme").addEventListener("click", () => {
    const now = document.documentElement.dataset.theme || "auto";
    const next = THEMES[(THEMES.indexOf(now) + 1) % THEMES.length];
    applyTheme(next);
    try { localStorage.setItem("review-theme", next); } catch (_) { /* private mode */ }
  });
}

// ---------- start ----------

async function init() {
  initTheme();
  $("prev").addEventListener("click", () => go(-1));
  $("next").addEventListener("click", () => go(1));
  $("save-status").addEventListener("click", () => { if (state.failed) retryNow(); });
  $("add-btn").addEventListener("click", () => ($("add-panel").hidden ? openAdd() : closeAdd()));
  $("add-filter").addEventListener("input", renderAdd);
  $("add-filter").addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      const first = $("add-list").querySelector(".add-item");
      if (first) first.click();
    }
  });
  for (const b of $("add-stance").querySelectorAll(".stance-pick")) {
    b.addEventListener("click", () => { if (state.addValue) addValue(state.addValue, b.dataset.stance); });
  }
  $("note").addEventListener("input", noteChanged);
  $("note").addEventListener("blur", flushNote);
  $("article").addEventListener("click", (ev) => {
    const mark = ev.target.closest(".hl");
    if (mark) select(mark.dataset.row, { scroll: false });
    else if (window.getSelection().isCollapsed) clearSelection();
  });
  document.addEventListener("keydown", onKey);
  window.addEventListener("beforeunload", (ev) => {
    flushNote();
    if (pendingWork()) { ev.preventDefault(); ev.returnValue = ""; }
  });

  let items;
  try {
    items = await getJSON("/api/items");
  } catch (e) {
    $("title").textContent = "Could not reach the review server";
    $("text-error").hidden = false;
    $("text-error").textContent = String(e.message || e);
    return;
  }
  state.mode = items.mode;
  state.documents = items.documents;
  state.multiRun = items.mode !== MODE.BLIND && items.settings.runs.length > 1;
  renderHeader(items);
  if (!state.documents.length) {
    $("title").textContent = items.mode === MODE.BLIND ? "Nothing left to judge" : "No articles in these runs";
    $("position").textContent = "Article 0 / 0";
    $("prev").disabled = $("next").disabled = true;
    return;
  }
  const fromHash = parseInt(location.hash.slice(1), 10);
  loadDoc(Number.isFinite(fromHash) ? fromHash - 1 : 0);
}

document.addEventListener("DOMContentLoaded", init);
