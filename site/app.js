/* Home Assistant AI Index — filter/compare UI. Vanilla JS, no dependencies.
   Filter state is mirrored into location.hash so filtered views are shareable. */
"use strict";

const DATA = JSON.parse(document.getElementById("data").textContent);
const CAPS = DATA.capabilities;
const LABELS = DATA.capability_labels;
const TIPS = DATA.capability_tips || {};
const SVGS = DATA.capability_svgs || {};
const CATS = DATA.categories;

const INSTALL_LABELS = {
  "core-integration": "core",
  "hacs-integration": "HACS",
  "addon": "add-on",
  "container": "container",
  "external": "external",
};

const svg = (name, cls = "ic") => SVGS[name]
  ? `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${SVGS[name]}</svg>`
  : "";

const state = {
  q: "",
  cats: new Set(),
  caps: {},            // cap -> "require" | "exclude"
  inference: "any",    // any | local-only | local-possible | cloud-possible
  installs: new Set(),
  sort: { key: "name", dir: 1 },
  compare: new Set(),
};

/* ---------- filter state <-> URL hash ---------- */

function stateToHash() {
  const parts = [];
  if (state.q) parts.push("q=" + encodeURIComponent(state.q));
  if (state.cats.size) parts.push("cat=" + [...state.cats].join(","));
  const caps = Object.entries(state.caps).map(([c, m]) => `${c}:${m}`);
  if (caps.length) parts.push("cap=" + caps.join(","));
  if (state.inference !== "any") parts.push("inf=" + state.inference);
  if (state.installs.size) parts.push("in=" + [...state.installs].join(","));
  history.replaceState(null, "", parts.length ? "#" + parts.join("&") : location.pathname);
}

function hashToState() {
  const hash = location.hash.replace(/^#/, "");
  if (!hash) return;
  for (const part of hash.split("&")) {
    const [key, raw] = part.split("=");
    const value = decodeURIComponent(raw || "");
    if (key === "q") state.q = value;
    if (key === "cat") value.split(",").forEach((c) => CATS[c] && state.cats.add(c));
    if (key === "inf") state.inference = value;
    if (key === "in") value.split(",").forEach((i) => INSTALL_LABELS[i] && state.installs.add(i));
    if (key === "cap")
      value.split(",").forEach((pair) => {
        const [cap, mode] = pair.split(":");
        if (CAPS.includes(cap) && (mode === "require" || mode === "exclude")) state.caps[cap] = mode;
      });
  }
}

/* ---------- filtering ---------- */

function matches(entry) {
  if (state.q) {
    const hay = (entry.name + " " + entry.summary + " " + (entry.providers || []).join(" ")).toLowerCase();
    if (!hay.includes(state.q.toLowerCase())) return false;
  }
  if (state.cats.size && !state.cats.has(entry.category)) return false;
  for (const [cap, mode] of Object.entries(state.caps)) {
    const has = !!entry.capabilities[cap];
    if (mode === "require" && !has) return false;
    if (mode === "exclude" && has) return false;
  }
  const inf = entry.inference || [];
  if (state.inference === "local-only" && (inf.includes("cloud") || !inf.includes("local"))) return false;
  if (state.inference === "local-possible" && !inf.includes("local")) return false;
  if (state.inference === "cloud-possible" && !inf.includes("cloud")) return false;
  if (state.installs.size && ![...state.installs].some((i) => entry.install.includes(i))) return false;
  return true;
}

function sortKey(entry) {
  const meta = (entry.generated && entry.generated.repo_meta) || {};
  const addon = entry.generated && entry.generated.addon;
  switch (state.sort.key) {
    case "stars": return meta.stars == null ? -1 : meta.stars;
    case "updated": return meta.pushed_at || "";
    case "rating": return addon ? addon.supervisor_rating.value : -1;
    case "category": return entry.category;
    default: return entry.name.toLowerCase();
  }
}

/* ---------- rendering ---------- */

const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function capIcons(entry) {
  const disputed = new Set(entry.disputed || []);
  return CAPS.filter((c) => entry.capabilities[c])
    .map((c) => `<span class="capic${disputed.has(c) ? " disputed" : ""}" data-tip="${esc(LABELS[c])}${disputed.has(c) ? " (disputed)" : ""}" tabindex="0">${svg(c)}</span>`)
    .join("") || '<span class="none">—</span>';
}

function inferenceLabel(entry) {
  const inf = new Set(entry.inference || []);
  if (inf.has("local") && inf.has("cloud"))
    return `<span class="inf" data-tip="local or cloud — your choice of backend decides">${svg("local")}/${svg("cloud")}</span>`;
  if (inf.has("local")) return `<span class="inf" data-tip="model runs on your hardware">${svg("local")} local</span>`;
  return `<span class="inf" data-tip="model runs on someone else's servers">${svg("cloud")} cloud</span>`;
}

function starsLabel(entry) {
  if (entry.repo === "home-assistant/core") return "core";
  const meta = (entry.generated && entry.generated.repo_meta) || {};
  if (meta.stars == null) return "—";
  return meta.stars >= 1000 ? (meta.stars / 1000).toFixed(1).replace(/\.0$/, "") + "k" : String(meta.stars);
}

function renderTable() {
  const rows = DATA.entries.filter(matches);
  rows.sort((a, b) => {
    const ka = sortKey(a), kb = sortKey(b);
    return (ka < kb ? -1 : ka > kb ? 1 : 0) * state.sort.dir;
  });

  const arrow = (key) => (state.sort.key === key ? (state.sort.dir > 0 ? " ↑" : " ↓") : "");
  document.querySelector("#index thead").innerHTML = `<tr>
    <th class="cmpcol" data-tip="tick to compare"></th>
    <th data-sort="name">Name${arrow("name")}</th>
    <th data-sort="category">Category${arrow("category")}</th>
    <th>Capabilities</th>
    <th>Inference</th>
    <th>Install</th>
    <th data-sort="stars" data-tip="GitHub stars">${svg("star")}${arrow("stars")}</th>
    <th data-sort="updated">Updated${arrow("updated")}</th>
    <th data-sort="rating" data-tip="Supervisor add-on security rating">${svg("shield")}${arrow("rating")}</th>
  </tr>`;

  document.querySelector("#index tbody").innerHTML = rows.map((entry) => {
    const meta = (entry.generated && entry.generated.repo_meta) || {};
    const addon = entry.generated && entry.generated.addon;
    const archived = meta.archived ? ' <span class="archived" data-tip="repository is archived — no longer maintained">archived</span>' : "";
    return `<tr>
      <td class="cmpcol"><input type="checkbox" data-compare="${esc(entry.id)}" aria-label="compare ${esc(entry.name)}" ${state.compare.has(entry.id) ? "checked" : ""}></td>
      <td data-label="Project"><a href="./entries/${esc(entry.id)}/">${esc(entry.name)}</a>${archived}
          <span class="sub">${esc(entry.summary)}</span></td>
      <td data-label="Category"><span class="chip">${esc(CATS[entry.category])}</span></td>
      <td data-label="Capabilities" class="capcell">${capIcons(entry)}</td>
      <td data-label="Inference" class="nowrap">${inferenceLabel(entry)}</td>
      <td data-label="Install">${entry.install.map((i) => INSTALL_LABELS[i]).join(", ")}</td>
      <td data-label="Stars" class="nowrap">${starsLabel(entry)}</td>
      <td data-label="Updated" class="nowrap">${meta.pushed_at ? meta.pushed_at.slice(0, 10) : "—"}</td>
      <td data-label="Add-on rating" class="nowrap">${addon ? addon.supervisor_rating.value + "/8" : "—"}</td>
    </tr>`;
  }).join("");

  document.getElementById("count").textContent =
    `${rows.length} of ${DATA.entries.length} projects` +
    (rows.length < DATA.entries.length ? " match the filters" : "");
  stateToHash();
}

function renderFilters() {
  const capBtn = (cap) => {
    const mode = state.caps[cap] || "";
    const modeTip = mode === "require" ? "required — click for exclude"
      : mode === "exclude" ? "excluded — click to reset"
      : "click to require";
    return `<button data-cap="${cap}" class="fchip ${mode}" aria-pressed="${mode ? "true" : "false"}"
      data-tip="${esc(TIPS[cap] || LABELS[cap])} (${modeTip})">${svg(cap)}<span>${esc(LABELS[cap])}</span><b class="st"></b></button>`;
  };
  const infBtn = (value, label, tip) =>
    `<button data-inf="${value}" class="seg ${state.inference === value ? "on" : ""}" data-tip="${esc(tip)}">${label}</button>`;
  document.getElementById("filters").innerHTML = `
  <div class="frow search"><label class="searchbox">${svg("search")}
    <input type="search" id="q" placeholder="Search name, summary, provider…" value="${esc(state.q)}" aria-label="Search"></label>
    <span class="hint">Capability filters cycle: <b class="eg req">require</b> → <b class="eg exc">exclude</b> → off</span></div>
  <div class="frow"><span class="flabel">Capabilities</span><div class="fset">${CAPS.map(capBtn).join("")}</div></div>
  <div class="frow"><span class="flabel">Category</span><div class="fset">
    ${Object.entries(CATS).map(([id, title]) =>
      `<button data-cat="${id}" class="fchip cat ${state.cats.has(id) ? "on" : ""}">${esc(title)}</button>`).join("")}</div></div>
  <div class="frow"><span class="flabel">Inference</span><div class="fset seggroup" role="group">
    ${infBtn("any", "any", "no inference filter")}
    ${infBtn("local-only", `${svg("local")} local only`, "cloud not even possible — inference stays on your hardware")}
    ${infBtn("local-possible", `${svg("local")} can run local`, "a local backend is one of the options")}
    ${infBtn("cloud-possible", `${svg("cloud")} can use cloud`, "a cloud backend is one of the options")}</div></div>
  <div class="frow"><span class="flabel">Install</span><div class="fset">
    ${Object.entries(INSTALL_LABELS).map(([id, label]) =>
      `<button data-install="${id}" class="fchip ${state.installs.has(id) ? "on" : ""}">${esc(label)}</button>`).join("")}</div></div>`;
}

/* ---------- compare ---------- */

function renderCompareBar() {
  const bar = document.getElementById("comparebar");
  bar.hidden = state.compare.size < 2;
  document.getElementById("comparelabel").textContent = `${state.compare.size} selected`;
}

function openCompare() {
  const chosen = DATA.entries.filter((e) => state.compare.has(e.id));
  const row = (label, cells) =>
    `<tr><td>${label}</td>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`;
  let html = `<table><thead><tr><th></th>${chosen.map((e) =>
    `<th><a href="./entries/${esc(e.id)}/">${esc(e.name)}</a></th>`).join("")}</tr></thead><tbody>`;
  for (const cap of CAPS)
    html += row(`${svg(cap)} ${esc(LABELS[cap])}`, chosen.map((e) =>
      e.capabilities[cap] ? '<span class="yes">yes</span>' : '<span class="no">—</span>'));
  html += row("inference", chosen.map(inferenceLabel));
  html += row("install", chosen.map((e) => e.install.map((i) => INSTALL_LABELS[i]).join(", ")));
  html += row("providers", chosen.map((e) => (e.providers || []).join(", ") || "—"));
  html += row(`${svg("shield")} add-on rating`, chosen.map((e) =>
    e.generated && e.generated.addon ? e.generated.addon.supervisor_rating.value + "/8" : "—"));
  html += row(`${svg("star")} stars`, chosen.map(starsLabel));
  html += "</tbody></table>";
  document.getElementById("comparebody").innerHTML = html;
  document.getElementById("comparedlg").showModal();
}

/* ---------- presets ---------- */

const PRESETS = {
  cameras:     () => { state.caps = { reads_camera: "require" }; },
  localonly:   () => { state.inference = "local-only"; },
  autonomous:  () => { state.caps = { runs_unattended: "require" }; },
  cloudcamera: () => { state.caps = { reads_camera: "require" }; state.inference = "cloud-possible"; },
  clear:       () => {},
};

function resetFilters() {
  state.q = "";
  state.cats.clear();
  state.caps = {};
  state.inference = "any";
  state.installs.clear();
}

/* ---------- events ---------- */

document.addEventListener("click", (event) => {
  const target = event.target.closest("button, th");
  if (!target) return;
  if (target.dataset.preset) {
    resetFilters();
    PRESETS[target.dataset.preset]();
    renderFilters(); renderTable();
  } else if (target.dataset.cat !== undefined) {
    state.cats.has(target.dataset.cat) ? state.cats.delete(target.dataset.cat) : state.cats.add(target.dataset.cat);
    renderFilters(); renderTable();
  } else if (target.dataset.cap !== undefined) {
    const cap = target.dataset.cap;
    const mode = state.caps[cap];
    if (!mode) state.caps[cap] = "require";
    else if (mode === "require") state.caps[cap] = "exclude";
    else delete state.caps[cap];
    renderFilters(); renderTable();
  } else if (target.dataset.inf !== undefined) {
    state.inference = target.dataset.inf;
    renderFilters(); renderTable();
  } else if (target.dataset.install !== undefined) {
    state.installs.has(target.dataset.install)
      ? state.installs.delete(target.dataset.install)
      : state.installs.add(target.dataset.install);
    renderFilters(); renderTable();
  } else if (target.dataset.sort) {
    const key = target.dataset.sort;
    if (state.sort.key === key) state.sort.dir *= -1;
    else state.sort = { key, dir: key === "stars" || key === "rating" ? -1 : 1 };
    renderTable();
  } else if (target.id === "comparebtn") {
    openCompare();
  } else if (target.id === "compareclear") {
    state.compare.clear();
    renderCompareBar(); renderTable();
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "q") { state.q = event.target.value; renderTable(); }
});

document.addEventListener("change", (event) => {
  const id = event.target.dataset && event.target.dataset.compare;
  if (!id) return;
  if (event.target.checked) {
    if (state.compare.size >= 4) { event.target.checked = false; return; }
    state.compare.add(id);
  } else state.compare.delete(id);
  renderCompareBar();
});

hashToState();
renderFilters();
renderTable();
renderCompareBar();
