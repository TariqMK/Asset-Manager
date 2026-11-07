// Product page behaviour: live app previews with made-up sample data, and download links from the latest GitHub release.
"use strict";

const REPO = "TariqMK/Asset-Manager";
const ASSET = { windows: /windows-x64\.zip$/i, macos: /macos-arm64\.zip$/i, linux: /linux-x64\.tar\.gz$/i };
const OS_NAME = { windows: "Windows", macos: "macOS", linux: "Linux" };
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ------------------------------------------------------------ sample library (all made up)
const ROOT = "C:\\Users\\Alex\\Pictures\\";
const FILES = [
  ["vestrahorn-sunrise.jpg", "1600×1067", "674.8 KB", "Photography\\Iceland 2025", ["hero", "iceland", "landscape", "mountains", "sunrise"]],
  ["logo-primary.png", "1600×900", "48.2 KB", "Design Library\\Brand\\Northwind Coffee", ["brand", "logo", "northwind"]],
  ["buttermere-morning.jpg", "1600×1067", "702.1 KB", "Photography\\Lake District", ["lake-district", "landscape", "sunrise", "water"]],
  ["spring-campaign-01.png", "1400×1400", "96.4 KB", "Design Library\\Illustrations", ["hero", "illustration"]],
  ["kirkjufell-golden-hour.jpg", "1600×1067", "651.3 KB", "Photography\\Iceland 2025", ["iceland", "landscape", "mountains", "sunset"]],
  ["onboarding-welcome.png", "1200×1600", "61.7 KB", "Design Library\\UI", ["mobile", "northwind", "ui"]],
  ["wastwater-sunset.jpg", "1600×1067", "688.0 KB", "Photography\\Lake District", ["lake-district", "landscape", "sunset", "water"]],
  ["paper-warm.jpg", "1200×1200", "412.5 KB", "Design Library\\Textures", ["paper", "texture"]],
  ["jokulsarlon-blue-hour.jpg", "1600×1067", "597.9 KB", "Photography\\Iceland 2025", ["iceland", "landscape", "water"]],
  ["colour-palette.png", "1600×900", "22.6 KB", "Design Library\\Brand\\Northwind Coffee", ["brand", "northwind"]],
  ["catbells-fog.jpg", "1600×1067", "664.6 KB", "Photography\\Lake District", ["fog", "lake-district", "landscape", "mountains"], true],
  ["spring-campaign-02.png", "1400×1400", "88.1 KB", "Design Library\\Illustrations", ["illustration"]],
  ["reynisfjara-overcast.jpg", "1600×1067", "533.2 KB", "Photography\\Iceland 2025", ["fog", "iceland", "landscape"]],
  ["logo-reversed.png", "1600×900", "47.9 KB", "Design Library\\Brand\\Northwind Coffee", ["brand", "logo", "northwind"]],
  ["concrete-grey.jpg", "1200×1200", "455.0 KB", "Design Library\\Textures", ["texture"]],
  ["onboarding-subscribe.png", "1200×1600", "60.3 KB", "Design Library\\UI", ["mobile", "northwind", "ui"]],
  ["derwentwater-dawn.jpg", "1600×1067", "690.4 KB", "Photography\\Lake District", ["lake-district", "landscape", "sunrise", "water"]],
].map(([name, dims, size, folder, tags, missing]) => ({
  name, dims, size, folder, tags, missing: !!missing,
  ext: name.split(".").pop().toUpperCase(),
  img: `img/${name.replace(/\.\w+$/, "")}.jpg`,
}));
const PRESENT = FILES.filter((f) => !f.missing);
const byName = (n) => FILES.find((f) => f.name === n);

const svg = (id) => `<svg class="ico"><use href="#i-${id}"/></svg>`;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const tile = (f, cls = "") => `<div class="tile ${cls}" data-name="${f.name}"><img src="${f.img}" alt="" loading="lazy"></div>`;

function tagCounts(files) {
  const counts = {};
  files.forEach((f) => f.tags.forEach((t) => { counts[t] = (counts[t] || 0) + 1; }));
  return Object.keys(counts).sort().map((t) => [t, counts[t]]);
}

// Runs fn every `ms` while the tab is visible. With reduced motion, fn runs once.
function loop(fn, ms) {
  fn();
  if (REDUCED) return;
  setInterval(() => { if (!document.hidden) fn(); }, ms);
}

// ------------------------------------------------------------ hero: the library window
function renderHero() {
  const sidebar = document.getElementById("hero-sidebar");
  const row = (icon, label, n, cls = "") =>
    `<div class="side-row ${cls}">${svg(icon)}<span>${esc(label)}</span>${n !== undefined ? `<span class="n">${n}</span>` : ""}</div>`;
  sidebar.innerHTML =
    `<div class="app-brand">Asset Manager <span class="cat">v1.2.2</span></div>` +
    row("images", "All files", undefined, "active") +
    row("image-off", "Missing", 1) +
    `<div class="side-label">Tags</div>` +
    tagCounts(FILES).slice(0, 6).map(([t, n]) => row("tag", t, n)).join("") +
    `<div class="side-label">Watched folders</div>` +
    row("folder", "Photography") + row("folder", "Design Library") +
    `<div class="side-label">Collections</div>` +
    row("layers", "Website refresh", 2) + row("layers", "Homepage heroes", 3, "sub") +
    row("layers", "Northwind rebrand", 3) + row("filter", "Golden hour", 5);

  const grid = document.getElementById("hero-grid");
  grid.innerHTML = FILES.slice(0, 12).map((f) => `
    <div class="thumb${f.missing ? " missing" : ""}" data-name="${f.name}">
      <div class="thumb-img"><img src="${f.img}" alt="">${f.missing ? `<span class="badge-missing">${svg("alert")}Missing</span>` : ""}</div>
      <div class="thumb-name">${esc(f.name)}</div>
      <div class="cat">${f.ext} · ${f.dims}</div>
      <div class="thumb-tags">${esc(f.tags.join(", "))}</div>
    </div>`).join("");
}

const HERO_STORY = [
  ["vestrahorn-sunrise.jpg", ["Homepage heroes", "Golden hour"], "Shot at 05:40 from the black-sand spit. Use for the spring homepage hero, cropped to 16:9."],
  ["logo-primary.png", ["Northwind rebrand"], "Final mark, approved 12 May. Use logo-reversed on dark backgrounds."],
  ["buttermere-morning.jpg", ["Homepage heroes", "Golden hour"], "Calm water, good for headline text on the left."],
  ["kirkjufell-golden-hour.jpg", ["Golden hour"], "Print version requested by the client, A2."],
];
const COLLECTIONS = ["Website refresh", "Homepage heroes", "Northwind rebrand", "Golden hour"];
let heroStep = 0;

function heroTick() {
  const [name, inCollections, note] = HERO_STORY[heroStep++ % HERO_STORY.length];
  const f = byName(name);
  document.querySelectorAll("#hero-grid .thumb").forEach((t) => t.classList.toggle("selected", t.dataset.name === name));
  const insp = document.getElementById("hero-inspector");
  insp.innerHTML = `<div class="fade">
    <div class="insp-name">${esc(f.name)}</div>
    <div class="insp-preview"><img src="${f.img}" alt=""></div>
    <div class="cat" style="margin-top:12px">${f.ext} · ${f.dims} · ${f.size} · ${esc(f.folder.split("\\")[0])}</div>
    <div class="insp-path">${esc(ROOT + f.folder + "\\" + f.name)}</div>
    <div class="insp-label">Tags</div>
    <div class="chips">${f.tags.map((t) => `<span class="chip">${esc(t)}</span>`).join("")}</div>
    <div class="insp-label">Collections</div>
    ${COLLECTIONS.map((c) => `<div class="check${inCollections.includes(c) ? " on" : ""}"><i></i>${esc(c)}</div>`).join("")}
    <div class="insp-label">Notes</div>
    <div class="insp-note">${esc(note)}</div>
  </div>`;
}

// ------------------------------------------------------------ smart collections
// Each step is the rule set of the "Golden hour" collection; rules are ANDed.
const SMART_STEPS = [
  [{ match: "any", tags: ["sunrise", "sunset"] }, { match: "all", tags: ["landscape"] }],
  [{ match: "any", tags: ["sunrise"] }, { match: "all", tags: ["landscape"] }],
  [{ match: "any", tags: ["sunrise", "sunset"] }, { match: "all", tags: ["landscape"] }, { match: "all", tags: ["iceland"] }],
  [{ match: "any", tags: ["sunrise", "sunset"] }, { match: "all", tags: ["landscape"] }, { match: "all", tags: ["lake-district"] }],
];
const RULE_CHOICES = [["sunrise", "sunset", "fog"], ["landscape"], ["iceland", "lake-district"]];
let smartStep = 0;

function matches(f, rules) {
  return rules.every((r) => (r.match === "any" ? r.tags.some((t) => f.tags.includes(t)) : r.tags.every((t) => f.tags.includes(t))));
}

function smartTick() {
  const rules = SMART_STEPS[smartStep++ % SMART_STEPS.length];
  const prev = document.querySelectorAll("#smart-rules .rule").length;
  document.getElementById("smart-rules").innerHTML = rules.map((r, i) => `
    ${i ? `<span class="combine">and</span>` : ""}
    <div class="rule${i >= prev && prev ? " entering" : ""}">
      <div class="rule-head">Rule ${i + 1} · <b>${r.match === "any" ? "Any of" : "All of"}</b></div>
      <div class="chips">${RULE_CHOICES[i].map((t) => `<span class="chip${r.tags.includes(t) ? " on" : ""}">${t}</span>`).join("")}</div>
    </div>`).join("");

  const grid = document.getElementById("smart-grid");
  if (!grid.children.length) grid.innerHTML = PRESENT.map((f) => tile(f)).join("");
  let n = 0;
  [...grid.children].forEach((el) => {
    const hit = matches(byName(el.dataset.name), rules);
    if (hit) n++;
    el.classList.toggle("in", hit);
    el.classList.toggle("out", !hit);
  });
  document.getElementById("smart-meta").textContent = `Golden hour · ${rules.length} rules · ${n} files`;
}

// ------------------------------------------------------------ tag filter and search
const FILTER_STORY = [
  { tag: null, query: "" },
  { tag: "iceland", query: "" },
  { tag: null, query: "fog" },
  { tag: "northwind", query: "" },
];
let filterStep = 0;
let typing = null;

function renderFilter(tag, query) {
  const q = query.toLowerCase();
  const shown = PRESENT.filter((f) => (!tag || f.tags.includes(tag)) &&
    (!q || (f.name + " " + f.tags.join(" ")).toLowerCase().includes(q)));
  document.getElementById("filter-tags").innerHTML = tagCounts(PRESENT)
    .filter(([t]) => ["brand", "fog", "iceland", "landscape", "northwind", "texture", "water"].includes(t))
    .map(([t, n]) => `<li class="${t === tag ? "active" : ""}">${svg("tag")}${t}<span class="n">${n}</span></li>`).join("");
  const chip = document.getElementById("filter-chip");
  chip.hidden = !tag;
  chip.textContent = tag ? `${tag} ×` : "";
  document.getElementById("filter-count").textContent = `${shown.length} file${shown.length === 1 ? "" : "s"}`;
  document.getElementById("filter-grid").innerHTML = shown.slice(0, 12).map((f) => tile(f)).join("");
}

function filterTick() {
  const { tag, query } = FILTER_STORY[filterStep++ % FILTER_STORY.length];
  const queryEl = document.getElementById("filter-query");
  clearInterval(typing);
  if (!query || REDUCED) {
    queryEl.textContent = query;
    renderFilter(tag, query);
    return;
  }
  // Type the search one letter at a time, filtering as it goes, like the app.
  let i = 0;
  typing = setInterval(() => {
    i++;
    queryEl.textContent = query.slice(0, i);
    renderFilter(tag, query.slice(0, i));
    if (i >= query.length) clearInterval(typing);
  }, 240);
}

// ------------------------------------------------------------ background scan
const SCAN_FILES = PRESENT.filter((f) => f.folder.startsWith("Design Library"));
let scanTimer = null;

function scanRun() {
  const title = document.getElementById("scan-title");
  const fill = document.getElementById("scan-fill");
  const progress = document.getElementById("scan-progress");
  const lines = document.getElementById("scan-lines");
  const grid = document.getElementById("scan-grid");
  const total = SCAN_FILES.length;
  const log = [`Scanning ${ROOT}Design Library`, `Found ${total} images`];
  const show = (done) => {
    fill.style.transform = `scaleX(${done / total})`;
    progress.textContent = done < total
      ? `${done + 1} of ${total}  ${SCAN_FILES[done].folder.replace("Design Library\\", "")}\\${SCAN_FILES[done].name}`
      : `${total} of ${total}`;
    lines.textContent = log.join("\n");
  };

  if (REDUCED) {
    title.textContent = "Scanned Design Library";
    log.push(`Done in 2.4s -- ${total} new, 0 newly missing`);
    show(total);
    grid.innerHTML = SCAN_FILES.map((f) => tile(f)).join("");
    return;
  }
  title.textContent = "Scanning Design Library…";
  grid.innerHTML = "";
  let done = 0;
  show(0);
  clearInterval(scanTimer);
  scanTimer = setInterval(() => {
    if (document.hidden) return;
    if (done < total) {
      grid.insertAdjacentHTML("beforeend", tile(SCAN_FILES[done]));
      done++;
      if (done === total) {
        title.textContent = "Scanned Design Library";
        log.push(`Done in 2.4s -- ${total} new, 0 newly missing`);
      }
      show(done);
    } else if (done++ > total + 8) {
      clearInterval(scanTimer);
      scanRun();
    }
  }, 300);
}

// ------------------------------------------------------------ downloads
function detectOS() {
  const ua = navigator.userAgent;
  if (/Android|iPhone|iPad|iPod/i.test(ua)) return null;
  if (/Windows/i.test(ua)) return "windows";
  if (/Mac/i.test(ua)) return "macos";
  if (/Linux|X11/i.test(ua)) return "linux";
  return null;
}

async function wireDownloads() {
  const os = detectOS();
  const hero = document.getElementById("hero-download");
  if (os) {
    hero.textContent = `Download for ${OS_NAME[os]}`;
    document.querySelector(`.card[data-os="${os}"]`).classList.add("mine");
  }
  // Every link already points at the Releases page, so any failure here
  // (offline, rate limit, no release yet) leaves a working page.
  try {
    const res = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`);
    if (!res.ok) return;
    const rel = await res.json();
    const date = new Date(rel.published_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
    document.getElementById("download-meta").textContent = `${rel.tag_name} · Released ${date}`;
    document.getElementById("hero-meta").textContent = `${rel.tag_name} · Free · Windows · macOS · Linux · Offline, no tracking`;
    for (const [key, pattern] of Object.entries(ASSET)) {
      const asset = rel.assets.find((a) => pattern.test(a.name));
      if (!asset) continue;
      const card = document.querySelector(`.card[data-os="${key}"]`);
      card.href = asset.browser_download_url;
      const size = card.querySelector("[data-size]");
      size.textContent = `${size.textContent} · ${(asset.size / 1e6).toFixed(1)} MB`;
      if (key === os) hero.href = asset.browser_download_url;
    }
  } catch (e) {
    /* keep the Releases page links */
  }
}

// ------------------------------------------------------------ start
renderHero();
loop(heroTick, 4000);
loop(smartTick, 3200);
loop(filterTick, 3600);
scanRun();
wireDownloads();
