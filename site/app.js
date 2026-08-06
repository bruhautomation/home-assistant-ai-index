/* Home Assistant AI Index — filter/compare UI. Vanilla JS, no dependencies.
   Filter state is mirrored into location.hash so filtered views are shareable. */
"use strict";

const DATA = JSON.parse(document.getElementById("data").textContent);
const CAPS = DATA.capabilities;
const ICONS = DATA.capability_icons;
const LABELS = DATA.capability_labels;
const CATS = DATA.categories;

const INSTALL_LABELS = {
  "core-integration": "core",
  "hacs-integration": "HACS",
  "addon": "add-on",
  "container": "container",
  "external": "external",
};

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
    .map((c) => `<span title="${esc(LABELS[c])}">${ICONS[c]}${disputed.has(c) ? "⚠️" : ""}</span>`)
    .join("") || "—";
}

function inferenceLabel(entry) {
  const inf = new Set(entry.inference || []);
  if (inf.has("local") && inf.has("cloud")) return "🏠/☁️";
  if (inf.has("local")) return "🏠 local";
  return "☁️ cloud";
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
    <th title="select to compare"></th>
    <th data-sort="name">Name${arrow("name")}</th>
    <th data-sort="category">Category${arrow("category")}</th>
    <th>Capabilities</th>
    <th>Inference</th>
    <th>Install</th>
    <th data-sort="stars">★${arrow("stars")}</th>
    <th data-sort="updated">Updated${arrow("updated")}</th>
    <th data-sort="rating" title="Supervisor add-on security rating">🛡️${arrow("rating")}</th>
  </tr>`;

  document.querySelector("#index tbody").innerHTML = rows.map((entry) => {
    const meta = (entry.generated && entry.generated.repo_meta) || {};
    const addon = entry.generated && entry.generated.addon;
    const archived = meta.archived ? " ⚠️<small>archived</small>" : "";
    return `<tr>
      <td><input type="checkbox" data-compare="${esc(entry.id)}" ${state.compare.has(entry.id) ? "checked" : ""}></td>
      <td><a href="./entries/${esc(entry.id)}/">${esc(entry.name)}</a>${archived}
          <span class="sub">${esc(entry.summary)}</span></td>
      <td><span class="chip">${esc(CATS[entry.category])}</span></td>
      <td class="capcell">${capIcons(entry)}</td>
      <td class="nowrap">${inferenceLabel(entry)}</td>
      <td>${entry.install.map((i) => INSTALL_LABELS[i]).join(", ")}</td>
      <td class="nowrap">${starsLabel(entry)}</td>
      <td class="nowrap">${meta.pushed_at ? meta.pushed_at.slice(0, 10) : "—"}</td>
      <td class="nowrap">${addon ? addon.supervisor_rating.value + "/8" : "—"}</td>
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
    return `<button data-cap="${cap}" class="${mode}"
      title="click: must have · click again: must NOT have · again: any">${ICONS[cap]} ${esc(LABELS[cap])}</button>`;
  };
  document.getElementById("filters").innerHTML = `
  <div class="group"><span class="label">Search</span>
    <input type="search" id="q" placeholder="name, summary, provider…" value="${esc(state.q)}"></div>
  <div class="group"><span class="label">Category</span>
    ${Object.entries(CATS).map(([id, title]) =>
      `<button data-cat="${id}" class="${state.cats.has(id) ? "on" : ""}">${esc(title)}</button>`).join("")}</div>
  <div class="group"><span class="label">Capability</span>${CAPS.map(capBtn).join("")}</div>
  <div class="group"><span class="label">Inference</span>
    <select id="inference">
      <option value="any" ${state.inference === "any" ? "selected" : ""}>any</option>
      <option value="local-only" ${state.inference === "local-only" ? "selected" : ""}>🏠 local only — cloud not even possible</option>
      <option value="local-possible" ${state.inference === "local-possible" ? "selected" : ""}>🏠 can run local</option>
      <option value="cloud-possible" ${state.inference === "cloud-possible" ? "selected" : ""}>☁️ can use cloud</option>
    </select></div>
  <div class="group"><span class="label">Install</span>
    ${Object.entries(INSTALL_LABELS).map(([id, label]) =>
      `<button data-install="${id}" class="${state.installs.has(id) ? "on" : ""}">${esc(label)}</button>`).join("")}</div>`;
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
    html += row(`${ICONS[cap]} ${esc(LABELS[cap])}`, chosen.map((e) =>
      e.capabilities[cap] ? '<span class="yes">yes</span>' : '<span class="no">—</span>'));
  html += row("inference", chosen.map(inferenceLabel));
  html += row("install", chosen.map((e) => e.install.map((i) => INSTALL_LABELS[i]).join(", ")));
  html += row("providers", chosen.map((e) => (e.providers || []).join(", ") || "—"));
  html += row("🛡️ add-on rating", chosen.map((e) =>
    e.generated && e.generated.addon ? e.generated.addon.supervisor_rating.value + "/8" : "—"));
  html += row("★ stars", chosen.map(starsLabel));
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
  if (event.target.id === "inference") { state.inference = event.target.value; renderTable(); }
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
