// ------------------------------------------------------------------ state

const state = {
  view: { type: "smart", id: "all" },   // {type: 'smart'|'root'|'collection', id}
  activeTag: null,
  search: "",
  files: [],
  roots: [],
  collections: [],
  tags: [],
  selectedFileId: null,
};

// ------------------------------------------------------------------ api helper

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }
  const contentType = res.headers.get("content-type") || "";
  return contentType.includes("application/json") ? res.json() : null;
}

// ------------------------------------------------------------------ icons
// Lucide icons (lucide.dev, ISC licence), inlined so the app works offline.

const ICONS = {
  images: '<path d="M18 22H4a2 2 0 0 1-2-2V6"/><path d="m22 13-1.296-1.296a2.41 2.41 0 0 0-3.408 0L11 18"/><circle cx="12" cy="8" r="2"/><rect width="16" height="16" x="6" y="2" rx="2"/>',
  image: '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
  "image-off": '<line x1="2" x2="22" y1="2" y2="22"/><path d="M10.41 10.41a2 2 0 1 1-2.83-2.83"/><line x1="13.5" x2="6" y1="13.5" y2="21"/><line x1="18" x2="21" y1="12" y2="15"/><path d="M3.59 3.59A1.99 1.99 0 0 0 3 5v14a2 2 0 0 0 2 2h14c.55 0 1.052-.22 1.41-.59"/><path d="M21 15V5a2 2 0 0 0-2-2H9"/>',
  "image-plus": '<path d="M16 5h6"/><path d="M19 2v6"/><path d="M21 11.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7.5"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/><circle cx="9" cy="9" r="2"/>',
  tag: '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>',
  folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  "folder-plus": '<path d="M12 10v6"/><path d="M9 13h6"/><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  layers: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
  filter: '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
  pencil: '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  "chevron-down": '<path d="m6 9 6 6 6-6"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
};

function icon(name, extraClass = "") {
  return `<svg class="i ${extraClass}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;
}

// Static markup uses <i data-icon="name"> placeholders; swap them for SVGs.
function hydrateIcons(scope = document) {
  scope.querySelectorAll("i[data-icon]").forEach((el) => {
    const tmp = document.createElement("span");
    tmp.innerHTML = icon(el.dataset.icon, el.className);
    const svg = tmp.firstElementChild;
    if (el.id) svg.id = el.id;
    el.replaceWith(svg);
  });
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

// In-app feedback instead of alert() dialogs.
function toast(message, { error = false, duration = 6000 } = {}) {
  const el = document.createElement("div");
  el.className = "toast" + (error ? " error" : "");
  el.innerHTML = `${icon(error ? "alert" : "info")}<span></span>`;
  el.querySelector("span").textContent = message;
  document.getElementById("toast-root").appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ------------------------------------------------------------------ modal helper

function normalizeTagFilterForEdit(tagFilter) {
  if (!tagFilter) return { combine: "and", rules: [{ tags: new Set(), match: "any" }] };
  if (tagFilter.rules) {
    return {
      combine: tagFilter.combine || "and",
      rules: tagFilter.rules.length
        ? tagFilter.rules.map((r) => ({ tags: new Set(r.tags || []), match: r.match || "any" }))
        : [{ tags: new Set(), match: "any" }],
    };
  }
  // legacy single-rule shape: {"tags": [...], "match": "any"|"all"}
  return { combine: "and", rules: [{ tags: new Set(tagFilter.tags || []), match: tagFilter.match || "any" }] };
}

// Mounts a modal; Escape cancels, Enter (outside textareas/rule inputs) confirms.
function mountModal(innerHtml, { onCancel, onConfirm }) {
  const root = document.getElementById("modal-root");
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = innerHtml;
  hydrateIcons(backdrop);
  root.appendChild(backdrop);
  backdrop.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { e.preventDefault(); onCancel(); }
    if (e.key === "Enter" && !e.target.closest("textarea, .rule-tag-add, button")) {
      e.preventDefault();
      onConfirm();
    }
  });
  backdrop.addEventListener("mousedown", (e) => { if (e.target === backdrop) onCancel(); });
  return backdrop;
}

function showCollectionModal(existingNode = null) {
  return new Promise((resolve) => {
    const isEdit = !!existingNode;
    const initialType = existingNode ? existingNode.type : "manual";
    const initial = normalizeTagFilterForEdit(existingNode ? existingNode.tag_filter : null);
    const rules = initial.rules; // array of {tags: Set, match: "any"|"all"}, mutated in place

    const backdrop = mountModal(`
      <div class="modal" role="dialog" aria-modal="true">
        <h3>${isEdit ? "Edit collection" : "New collection"}</h3>
        <div class="modal-field">
          <label class="modal-label" for="col-name">Name</label>
          <input id="col-name" type="text" value="${esc(existingNode ? existingNode.name : "")}" placeholder="Inspiration">
        </div>
        <div class="modal-field">
          <label class="modal-label" for="col-type">Type</label>
          <select id="col-type">
            <option value="manual">Manual: add files yourself</option>
            <option value="smart">Smart: include files by tag rules</option>
          </select>
        </div>
        <div id="smart-fields" hidden>
          <div id="combine-wrap" class="modal-field" style="display:none;">
            <label class="modal-label" for="col-combine">Combine rules with</label>
            <select id="col-combine">
              <option value="and">And: a file must match every rule</option>
              <option value="or">Or: a file must match at least one rule</option>
            </select>
          </div>
          <div id="rules-container"></div>
          <button id="btn-add-rule" type="button"><i data-icon="plus"></i>Add another rule</button>
        </div>
        <div class="modal-actions">
          <button id="modal-cancel" type="button">Cancel</button>
          <button class="primary" id="modal-confirm" type="button">${isEdit ? "Save" : "Create"}</button>
        </div>
      </div>`, { onCancel: () => close(null), onConfirm: () => confirm() });

    const typeSelect = backdrop.querySelector("#col-type");
    typeSelect.value = initialType;
    backdrop.querySelector("#col-combine").value = initial.combine;
    const smartFields = backdrop.querySelector("#smart-fields");
    smartFields.hidden = typeSelect.value !== "smart";

    function renderRules() {
      backdrop.querySelector("#combine-wrap").style.display = rules.length > 1 ? "" : "none";
      const container = backdrop.querySelector("#rules-container");
      container.innerHTML = "";

      rules.forEach((rule, idx) => {
        const block = document.createElement("div");
        block.className = "rule-block";
        block.innerHTML = `
          <div class="rule-header">
            <span>Rule ${idx + 1}</span>
            ${rules.length > 1 ? `<button type="button" class="icon subtle btn-remove-rule" title="Remove rule" aria-label="Remove rule">${icon("x")}</button>` : ""}
          </div>
          <label class="modal-label">Match</label>
          <select class="rule-match" style="width:100%">
            <option value="any">Any of these tags</option>
            <option value="all">All of these tags</option>
          </select>
          <label class="modal-label">Tags</label>
          <div class="tag-checklist rule-tag-checklist"></div>
          <input type="text" class="rule-tag-add" placeholder="New tag, then Enter">
        `;
        block.querySelector(".rule-match").value = rule.match;
        block.querySelector(".rule-match").onchange = (e) => { rule.match = e.target.value; };

        function renderChecklist() {
          const listEl = block.querySelector(".rule-tag-checklist");
          listEl.innerHTML = "";
          const allTagNames = new Set(state.tags.map((t) => t.name));
          rule.tags.forEach((t) => allTagNames.add(t));
          if (allTagNames.size === 0) {
            listEl.innerHTML = `<div class="muted-note">No tags yet. Add one below</div>`;
          }
          Array.from(allTagNames).sort().forEach((name) => {
            const row = document.createElement("label");
            row.className = "collection-check";
            row.innerHTML = `<input type="checkbox" ${rule.tags.has(name) ? "checked" : ""}><span>${esc(name)}</span>`;
            row.querySelector("input").onchange = (e) => {
              if (e.target.checked) rule.tags.add(name);
              else rule.tags.delete(name);
            };
            listEl.appendChild(row);
          });
        }
        renderChecklist();

        block.querySelector(".rule-tag-add").onkeydown = (e) => {
          if (e.key === "Enter" && e.target.value.trim()) {
            rule.tags.add(e.target.value.trim());
            e.target.value = "";
            renderChecklist();
          }
        };

        const removeBtn = block.querySelector(".btn-remove-rule");
        if (removeBtn) removeBtn.onclick = () => { rules.splice(idx, 1); renderRules(); };

        container.appendChild(block);
      });
    }
    renderRules();

    typeSelect.onchange = () => { smartFields.hidden = typeSelect.value !== "smart"; };
    backdrop.querySelector("#btn-add-rule").onclick = () => {
      rules.push({ tags: new Set(), match: "any" });
      renderRules();
    };
    backdrop.querySelector("#col-name").focus();

    function close(result) { backdrop.remove(); resolve(result); }
    backdrop.querySelector("#modal-cancel").onclick = () => close(null);
    backdrop.querySelector("#modal-confirm").onclick = () => confirm();
    function confirm() {
      const name = backdrop.querySelector("#col-name").value.trim();
      if (!name) { backdrop.querySelector("#col-name").focus(); return; }
      const type = typeSelect.value;
      const result = { name, type };
      if (type === "smart") {
        const cleanRules = rules
          .map((r) => ({ tags: Array.from(r.tags), match: r.match }))
          .filter((r) => r.tags.length > 0);
        result.tag_filter = { rules: cleanRules, combine: backdrop.querySelector("#col-combine").value };
      }
      close(result);
    }
  });
}

// title: the question; detail: what happens to the user's files; action: the
// destructive verb on the confirm button (never a bare "OK").
function confirmModal({ title, detail, action }) {
  return new Promise((resolve) => {
    const backdrop = mountModal(`
      <div class="modal" role="alertdialog" aria-modal="true">
        <h3></h3>
        <div class="modal-text"></div>
        <div class="modal-actions">
          <button id="modal-cancel" type="button">Cancel</button>
          <button class="danger" id="modal-confirm" type="button"></button>
        </div>
      </div>`, { onCancel: () => close(false), onConfirm: () => close(true) });
    backdrop.querySelector("h3").textContent = title;
    backdrop.querySelector(".modal-text").textContent = detail;
    backdrop.querySelector("#modal-confirm").textContent = action;
    function close(result) { backdrop.remove(); resolve(result); }
    backdrop.querySelector("#modal-cancel").onclick = () => close(false);
    backdrop.querySelector("#modal-confirm").onclick = () => close(true);
    backdrop.querySelector("#modal-cancel").focus();
  });
}

function addFolderModal(path) {
  return new Promise((resolve) => {
    const backdrop = mountModal(`
      <div class="modal" role="dialog" aria-modal="true" style="width:440px;">
        <h3>Add folder</h3>
        <div class="modal-path"></div>
        <label class="collection-check">
          <input type="checkbox" id="add-recursive" checked><span>Include subfolders</span>
        </label>
        <div class="modal-actions">
          <button id="modal-cancel" type="button">Cancel</button>
          <button class="primary" id="modal-confirm" type="button">Add folder</button>
        </div>
      </div>`, { onCancel: () => close(null), onConfirm: () => confirm() });
    backdrop.querySelector(".modal-path").textContent = path;
    function close(result) { backdrop.remove(); resolve(result); }
    function confirm() { close({ recursive: backdrop.querySelector("#add-recursive").checked }); }
    backdrop.querySelector("#modal-cancel").onclick = () => close(null);
    backdrop.querySelector("#modal-confirm").onclick = confirm;
    backdrop.querySelector("#modal-confirm").focus();
  });
}

// ------------------------------------------------------------------ scan log

// Scans run in the background on the server; this polls their status and
// shows a small log in the corner so you can see a big folder working.
let scanLogHideTimer = null;

async function watchScan() {
  const panel = document.getElementById("scan-log");
  const linesEl = document.getElementById("scan-log-lines");
  const progressEl = document.getElementById("scan-log-progress");
  clearTimeout(scanLogHideTimer);
  panel.hidden = false;
  panel.classList.remove("done");

  let status;
  let lastRefresh = Date.now();
  while (true) {
    status = await api("/api/scan-status");
    document.getElementById("scan-log-title").textContent =
      status.running ? `Scanning ${status.label}…` : `Scanned ${status.label}`;
    linesEl.textContent = status.lines.join("\n");
    const p = status.progress;
    progressEl.textContent = p ? `${p.done.toLocaleString()} of ${p.total.toLocaleString()}  ${p.current}` : "";
    progressEl.hidden = !p;
    document.getElementById("scan-log-bar").hidden = !p;
    if (p) {
      document.getElementById("scan-log-bar-fill").style.transform =
        `scaleX(${p.total ? p.done / p.total : 0})`;
    }
    linesEl.scrollTop = linesEl.scrollHeight;
    if (!status.running) break;
    // Pick up newly-saved files every few seconds without waiting for the end.
    if (Date.now() - lastRefresh > 3000) { lastRefresh = Date.now(); loadRoots(); }
    await new Promise((r) => setTimeout(r, 250));
  }

  panel.classList.add("done");
  scanLogHideTimer = setTimeout(() => { panel.hidden = true; }, status.error ? 15000 : 5000);
  return status;
}

// Starts a scan; onStarted runs once the server has accepted it (before
// the scan finishes). Resolves to the final scan status, or null.
async function startScan(path, options, onStarted) {
  try {
    await api(path, { method: "POST", ...options });
  } catch (e) {
    toast(e.message, { error: true });
    return null;
  }
  if (onStarted) await onStarted();
  return watchScan();
}

// ------------------------------------------------------------------ loading data

async function loadRoots() {
  state.roots = await api("/api/roots");
  renderSidebar();
}

async function loadCollections() {
  state.collections = await api("/api/collections");
  renderSidebar();
}

async function loadTags() {
  state.tags = await api("/api/tags");
  renderTagFilter();
  renderTagsSidebar();
}

async function loadFiles() {
  const params = new URLSearchParams();
  if (state.view.type === "collection") params.set("collection_id", state.view.id);
  if (state.view.type === "root") params.set("root_id", state.view.id);
  if (state.view.type === "smart" && state.view.id === "missing") params.set("status", "missing");
  if (state.activeTag) params.set("tag", state.activeTag);
  if (state.search) params.set("q", state.search);

  state.files = await api(`/api/files?${params.toString()}`);
  renderGrid();
  updateMissingCount();
}

async function updateMissingCount() {
  const missing = await api("/api/files?status=missing");
  const el = document.getElementById("missing-count");
  el.textContent = missing.length > 0 ? missing.length : "";
}

// ------------------------------------------------------------------ sidebar rendering

function navItem({ label, count, active, onClick, extraButtons, iconName, badge, title, className }) {
  const li = document.createElement("li");
  li.className = "nav-item" + (active ? " active" : "") + (className ? " " + className : "");
  li.innerHTML = `
    <button class="nav-row" type="button">
      ${iconName ? icon(iconName) : ""}
      <span class="label"></span><span class="nav-badge"></span><span class="count"></span>
    </button>`;
  li.querySelector(".label").textContent = label;
  if (count !== undefined) li.querySelector(".count").textContent = count;
  if (badge) li.querySelector(".nav-badge").textContent = badge;
  if (title) li.querySelector(".nav-row").title = title;
  li.querySelector(".nav-row").addEventListener("click", onClick);
  if (extraButtons) {
    const actions = document.createElement("span");
    actions.className = "row-actions";
    extraButtons.forEach((btn) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "icon subtle";
      b.innerHTML = icon(btn.icon);
      b.title = btn.title;
      b.setAttribute("aria-label", btn.title);
      b.onclick = (e) => { e.stopPropagation(); btn.onClick(); };
      actions.appendChild(b);
    });
    li.appendChild(actions);
  }
  return li;
}

function renderSidebar() {
  // smart views active state
  document.querySelectorAll('.nav-item[data-type="smart"]').forEach((el) => {
    el.classList.toggle(
      "active",
      state.view.type === "smart" && state.view.id === el.dataset.view
    );
  });

  // roots
  const rootsList = document.getElementById("roots-list");
  rootsList.innerHTML = "";
  state.roots.forEach((root) => {
    rootsList.appendChild(
      navItem({
        label: root.label,
        iconName: "folder",
        badge: root.reachable === false ? "offline" : undefined,
        className: root.reachable === false ? "offline" : "",
        title: root.reachable === false
          ? `${root.path}\nCan't reach this folder right now (unplugged drive or offline share?). Its files keep their tags and won't be marked missing.`
          : root.path,
        active: state.view.type === "root" && state.view.id === root.id,
        onClick: () => setView({ type: "root", id: root.id }),
        extraButtons: [
          { icon: "refresh", title: "Rescan", onClick: () => rescanRoot(root.id) },
          { icon: "x", title: "Stop watching", onClick: () => removeRoot(root.id) },
        ],
      })
    );
  });

  // collections
  const tree = document.getElementById("collections-tree");
  tree.innerHTML = "";
  function renderNodes(nodes, container) {
    nodes.forEach((node) => {
      const li = navItem({
        label: node.name,
        count: node.file_count || undefined,
        active: state.view.type === "collection" && state.view.id === node.id,
        iconName: node.type === "smart" ? "filter" : "layers",
        title: node.type === "smart" ? "Smart collection: files are included by tag rules" : undefined,
        onClick: () => setView({ type: "collection", id: node.id }),
        extraButtons: [
          { icon: "plus", title: "New sub-collection", onClick: () => addCollection(node.id) },
          { icon: "pencil", title: node.type === "smart" ? "Edit rules" : "Rename", onClick: () => renameCollection(node) },
          { icon: "x", title: "Delete", onClick: () => deleteCollection(node) },
        ],
      });
      container.appendChild(li);
      if (node.children && node.children.length) {
        const childUl = document.createElement("ul");
        childUl.className = "nav-list";
        li.appendChild(childUl);
        renderNodes(node.children, childUl);
      }
    });
  }
  renderNodes(state.collections, tree);
  renderViewHeader();
}

// Tags are picked from the sidebar; the toolbar shows the active one as a
// removable filter next to the view title.
function renderTagFilter() {
  const el = document.getElementById("tag-filter");
  el.innerHTML = "";
  if (!state.activeTag) return;
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "filter-chip";
  chip.title = "Clear tag filter";
  chip.innerHTML = `<span></span>${icon("x")}`;
  chip.querySelector("span").textContent = state.activeTag;
  chip.onclick = () => toggleActiveTag(state.activeTag);
  el.appendChild(chip);
}

let tagsSidebarCollapsed = false;

function renderTagsSidebar() {
  const el = document.getElementById("tags-sidebar-list");
  el.innerHTML = "";
  if (state.tags.length === 0) {
    el.innerHTML = `<li class="sidebar-empty">No tags yet</li>`;
    return;
  }
  state.tags.forEach((tag) => {
    el.appendChild(
      navItem({
        label: tag.name,
        iconName: "tag",
        count: tag.count,
        active: state.activeTag === tag.name,
        onClick: () => toggleActiveTag(tag.name),
      })
    );
  });
}

function toggleActiveTag(tagName) {
  state.activeTag = state.activeTag === tagName ? null : tagName;
  renderTagFilter();
  renderTagsSidebar();
  loadFiles();
}

function setView(view) {
  state.view = view;
  state.selectedFileId = null;
  closeInspector();
  renderSidebar();
  loadFiles();
}

// ------------------------------------------------------------------ grid rendering

const IMAGE_EXTENSIONS = new Set(["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "tif"]);

function extOf(filename) {
  const parts = filename.split(".");
  return parts.length > 1 ? parts.pop().toLowerCase() : "";
}

// The signature catalogue line, like the label on a slide mount:
// "JPG · 1600×1000", plus the file size in the inspector.
function catalogueLine(file, withSize = false) {
  const bits = [extOf(file.filename).toUpperCase() || "FILE"];
  if (file.width && file.height) bits.push(`${file.width}×${file.height}`);
  if (withSize && file.size_bytes) bits.push(formatBytes(file.size_bytes));
  return bits.join(" · ");
}

function currentViewTitle() {
  const { type, id } = state.view;
  if (type === "smart") return id === "missing" ? "Missing" : "All files";
  if (type === "root") return (state.roots.find((r) => r.id === id) || {}).label || "Folder";
  const node = flattenCollections(state.collections).find((c) => c.id === id);
  return node ? node.name : "Collection";
}

function renderViewHeader() {
  document.getElementById("view-title").textContent = currentViewTitle();
  const n = state.files.length;
  document.getElementById("view-count").textContent = `${n.toLocaleString()} ${n === 1 ? "file" : "files"}`;
}

function renderEmptyState() {
  const title = document.getElementById("empty-title");
  const text = document.getElementById("empty-text");
  const actions = document.getElementById("empty-actions");
  const libraryEmpty = state.roots.length === 0 && state.view.type === "smart" && state.view.id === "all"
    && !state.search && !state.activeTag;
  actions.hidden = !libraryEmpty;
  if (libraryEmpty) {
    title.textContent = "No images here yet";
    text.textContent = "Add a folder you already use, or import individual files. Nothing on disk is moved or changed.";
  } else if (state.search || state.activeTag) {
    title.textContent = "No matches";
    text.textContent = "Nothing in this view matches the current search or tag filter.";
  } else if (state.view.type === "smart" && state.view.id === "missing") {
    title.textContent = "Nothing missing";
    text.textContent = "Every file is where the library last saw it.";
  } else {
    title.textContent = "Nothing in this view";
    text.textContent = state.view.type === "collection"
      ? "Add files to this collection from the details panel."
      : "This folder has no supported images yet. Rescan it to pick up new files.";
  }
}

function renderGrid() {
  const grid = document.getElementById("grid");
  const emptyState = document.getElementById("empty-state");
  grid.innerHTML = "";
  renderViewHeader();

  if (state.files.length === 0) {
    renderEmptyState();
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;

  state.files.forEach((file) => {
    const card = document.createElement("button");
    card.type = "button";
    const isMissing = file.status === "missing";
    card.className = "thumb-card"
      + (file.id === state.selectedFileId ? " selected" : "")
      + (isMissing ? " missing" : "");
    card.dataset.id = file.id;
    card.title = file.filename;

    const hasThumb = file.thumbnail && IMAGE_EXTENSIONS.has(extOf(file.filename));

    card.innerHTML = `
      <div class="thumb-image-wrap">
        ${hasThumb
          ? `<img src="/api/thumbnails/${file.id}.png" loading="lazy" alt="">`
          : icon("image", "placeholder-icon")}
        ${isMissing ? `<span class="thumb-missing-badge">${icon("alert")}Missing</span>` : ""}
      </div>
      <div class="thumb-meta">
        <div class="thumb-filename">${esc(file.filename)}</div>
        <div class="catalogue">${esc(catalogueLine(file))}</div>
        <div class="thumb-tags">${esc(file.tags.join(", "))}</div>
      </div>`;

    card.addEventListener("click", () => selectFile(file.id));
    grid.appendChild(card);
  });
}

// ------------------------------------------------------------------ inspector

function closeInspector() {
  state.selectedFileId = null;
  document.getElementById("inspector").hidden = true;
  document.querySelectorAll(".thumb-card.selected").forEach((c) => c.classList.remove("selected"));
}

async function selectFile(fileId) {
  state.selectedFileId = fileId;
  document.querySelectorAll(".thumb-card").forEach((c) => c.classList.toggle("selected", c.dataset.id === fileId));
  await renderInspector();
}

async function renderInspector() {
  const file = state.files.find((f) => f.id === state.selectedFileId);
  if (!file) return;

  const inspector = document.getElementById("inspector");
  inspector.hidden = false;

  const hasThumb = file.thumbnail && IMAGE_EXTENSIONS.has(extOf(file.filename));
  const preview = document.getElementById("inspector-preview");
  if (hasThumb) preview.src = `/api/thumbnails/${file.id}.png`;
  else preview.removeAttribute("src");
  document.getElementById("missing-banner").hidden = file.status !== "missing";
  document.getElementById("btn-relink").hidden = file.status !== "missing";
  const filenameEl = document.getElementById("inspector-filename");
  filenameEl.textContent = file.filename;
  filenameEl.title = file.filename;
  document.getElementById("inspector-path").textContent = file.path;
  document.getElementById("inspector-meta").textContent =
    [catalogueLine(file, true), file.root_label].filter(Boolean).join(" · ");

  renderTagsEditor(file);
  renderCollectionsEditor(file);

  const notesEl = document.getElementById("notes-editor");
  notesEl.value = file.notes || "";
  notesEl.oninput = debounce(() => saveFileField(file.id, { notes: notesEl.value }), 500);

  document.getElementById("btn-relink").onclick = () => relinkFile(file.id);
  document.getElementById("btn-remove").onclick = () => removeFileFromLibrary(file.id);
}

function renderTagsEditor(file) {
  const el = document.getElementById("tags-editor");
  el.innerHTML = "";
  file.tags.forEach((tag) => {
    const chip = document.createElement("span");
    chip.className = "editable-tag";
    chip.innerHTML = `<span>${esc(tag)}</span><button type="button" title="Remove tag" aria-label="Remove tag ${esc(tag)}">${icon("x")}</button>`;
    chip.querySelector("button").onclick = () => {
      const newTags = file.tags.filter((t) => t !== tag);
      saveFileField(file.id, { tags: newTags }, () => {
        file.tags = newTags;
        renderTagsEditor(file);
        renderGrid();
        renderCollectionsEditor(file);
        loadTags();
      });
    };
    el.appendChild(chip);
  });
  const input = document.createElement("input");
  input.id = "tag-input";
  input.placeholder = file.tags.length ? "Add tag" : "Add a tag, then Enter";
  input.setAttribute("aria-label", "Add tag");
  input.onkeydown = (e) => {
    if (e.key === "Enter" && input.value.trim()) {
      const newTags = [...file.tags, input.value.trim()];
      saveFileField(file.id, { tags: newTags }, () => {
        file.tags = newTags;
        input.value = "";
        renderTagsEditor(file);
        renderGrid();
        renderCollectionsEditor(file);
        loadTags();
      });
    }
  };
  el.appendChild(input);
}

function flattenCollections(nodes, out = []) {
  nodes.forEach((n) => { out.push(n); flattenCollections(n.children, out); });
  return out;
}

async function renderCollectionsEditor(file) {
  const el = document.getElementById("collections-editor");
  const flat = flattenCollections(state.collections);
  if (flat.length === 0) {
    el.innerHTML = `<div class="muted-note">No collections yet</div>`;
    return;
  }
  const memberOf = new Set(await api(`/api/files/${file.id}/collections`));
  el.innerHTML = "";
  for (const col of flat) {
    const isSmart = col.type === "smart";
    const row = document.createElement("label");
    row.className = "collection-check" + (isSmart ? " auto" : "");
    const checked = memberOf.has(col.id);
    row.innerHTML = `<input type="checkbox" ${checked ? "checked" : ""} ${isSmart ? "disabled" : ""}><span>${esc(col.name)}</span>${isSmart ? '<span class="smart-badge">by tags</span>' : ""}`;
    if (isSmart) row.title = "Smart collection: membership follows its tag rules";
    if (!isSmart) {
      row.querySelector("input").onchange = async (e) => {
        if (e.target.checked) {
          await api(`/api/collections/${col.id}/files`, { method: "POST", body: JSON.stringify({ file_ids: [file.id] }) });
        } else {
          await api(`/api/collections/${col.id}/files/${file.id}`, { method: "DELETE" });
        }
        loadCollections();
      };
    }
    el.appendChild(row);
  }
}

async function saveFileField(fileId, patch, onDone) {
  const updated = await api(`/api/files/${fileId}`, { method: "PATCH", body: JSON.stringify(patch) });
  const idx = state.files.findIndex((f) => f.id === fileId);
  if (idx >= 0) state.files[idx] = { ...state.files[idx], ...updated };
  if (onDone) onDone();
}

async function relinkFile(fileId) {
  try {
    await api(`/api/files/${fileId}/relink`, { method: "POST" });
    await loadFiles();
    await selectFile(fileId);
  } catch (e) { /* dialog cancelled or failed silently */ }
}

async function removeFileFromLibrary(fileId) {
  const ok = await confirmModal({
    title: "Remove this file from the library?",
    detail: "Its tags and notes are forgotten. The file on disk is not touched.",
    action: "Remove",
  });
  if (!ok) return;
  await api(`/api/files/${fileId}`, { method: "DELETE" });
  closeInspector();
  loadFiles();
  loadCollections();
  loadTags();
}

// ------------------------------------------------------------------ roots

async function addRootFlow() {
  const { path } = await api("/api/pick-folder", { method: "POST" });
  if (!path) return;
  const choice = await addFolderModal(path);
  if (!choice) return;
  const status = await startScan(
    "/api/roots",
    { body: JSON.stringify({ path, recursive: choice.recursive }) },
    loadRoots,  // show the folder in the sidebar straight away
  );
  if (!status) return;
  await loadRoots();
  await loadTags();
  await loadFiles();
}

async function rescanRoot(rootId) {
  const status = await startScan(`/api/roots/${rootId}/rescan`);
  if (!status) return;
  await loadRoots();
  await loadFiles();
  const summary = (status.summaries || [])[0] || {};
  if (summary.root_unreachable) {
    const root = state.roots.find((r) => r.id === rootId);
    toast(`Couldn't reach "${root ? root.label : "this folder"}". Check the drive is connected.\nNothing was marked missing.`, { error: true });
  }
}

async function rescanAll() {
  const status = await startScan("/api/roots/rescan-all");
  if (!status) return;
  await loadRoots();
  await loadFiles();
  const unreachable = (status.summaries || [])
    .filter((s) => s.root_unreachable)
    .map((s) => (state.roots.find((r) => r.id === s.root_id) || {}).label || "?");
  if (unreachable.length) {
    toast(`Couldn't reach ${unreachable.join(", ")}. Check the drive is connected.\nFiles in those folders were not marked missing.`, { error: true });
  }
}

async function removeRoot(rootId) {
  const ok = await confirmModal({
    title: "Stop watching this folder?",
    detail: "The library forgets the tags and notes on its files. The files on disk are not touched.",
    action: "Stop watching",
  });
  if (!ok) return;
  await api(`/api/roots/${rootId}`, { method: "DELETE" });
  if (state.view.type === "root" && state.view.id === rootId) setView({ type: "smart", id: "all" });
  await loadRoots();
  await loadFiles();
  await loadCollections();
  await loadTags();
}

// ------------------------------------------------------------------ collections

async function addCollection(parentId) {
  const result = await showCollectionModal();
  if (!result) return;
  await api("/api/collections", {
    method: "POST",
    body: JSON.stringify({
      name: result.name,
      parent_id: parentId || null,
      type: result.type,
      tag_filter: result.tag_filter || null,
    }),
  });
  await loadCollections();
}

async function renameCollection(node) {
  const result = await showCollectionModal(node);
  if (!result) return;
  const payload = { name: result.name };
  if (result.type === "smart") payload.tag_filter = result.tag_filter;
  await api(`/api/collections/${node.id}`, { method: "PATCH", body: JSON.stringify(payload) });
  await loadCollections();
  if (state.selectedFileId) await renderInspector();
}

async function deleteCollection(node) {
  const ok = await confirmModal({
    title: `Delete "${node.name}"?`,
    detail: "Its sub-collections are deleted too. The files stay in your library.",
    action: "Delete",
  });
  if (!ok) return;
  await api(`/api/collections/${node.id}`, { method: "DELETE" });
  if (state.view.type === "collection" && state.view.id === node.id) setView({ type: "smart", id: "all" });
  await loadCollections();
}

// ------------------------------------------------------------------ import / drag & drop

async function importFilesFlow() {
  await api("/api/pick-files", { method: "POST" });
  await loadFiles();
  await loadTags();
}

function setupDragAndDrop() {
  const overlay = document.getElementById("drop-overlay");
  let dragCounter = 0;

  window.addEventListener("dragenter", (e) => {
    e.preventDefault();
    dragCounter++;
    overlay.hidden = false;
  });
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("dragleave", () => {
    dragCounter--;
    if (dragCounter <= 0) { dragCounter = 0; overlay.hidden = true; }
  });
  window.addEventListener("drop", async (e) => {
    e.preventDefault();
    dragCounter = 0;
    overlay.hidden = true;

    const paths = [];
    for (const file of e.dataTransfer.files) {
      // pywebview's Chromium-based webview exposes the real filesystem
      // path on dropped File objects (non-standard, but supported by
      // the embedded webview, unlike a sandboxed browser tab).
      if (file.path) paths.push(file.path);
    }
    if (paths.length === 0) {
      toast("Couldn't read file paths from the drop. Use Import files instead.", { error: true });
      return;
    }
    await api("/api/import", { method: "POST", body: JSON.stringify({ paths }) });
    await loadFiles();
    await loadTags();
  });
}

// ------------------------------------------------------------------ utils

function debounce(fn, wait) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ------------------------------------------------------------------ boot

function setupStaticEventListeners() {
  document.querySelectorAll('.nav-item[data-type="smart"]').forEach((el) => {
    el.addEventListener("click", () => setView({ type: "smart", id: el.dataset.view }));
  });
  document.getElementById("btn-add-root").onclick = addRootFlow;
  document.getElementById("btn-empty-add-root").onclick = addRootFlow;
  document.getElementById("btn-add-collection").onclick = () => addCollection(null);
  document.getElementById("tags-section-header").onclick = (e) => {
    tagsSidebarCollapsed = !tagsSidebarCollapsed;
    document.getElementById("tags-sidebar-list").hidden = tagsSidebarCollapsed;
    e.currentTarget.setAttribute("aria-expanded", String(!tagsSidebarCollapsed));
  };
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !document.querySelector(".modal-backdrop") && state.selectedFileId) {
      closeInspector();
    }
  });
  document.getElementById("btn-import").onclick = importFilesFlow;
  document.getElementById("btn-rescan").onclick = rescanAll;
  document.getElementById("btn-close-inspector").onclick = closeInspector;

  document.getElementById("search").addEventListener("input", debounce((e) => {
    state.search = e.target.value;
    loadFiles();
  }, 300));
}

async function boot() {
  hydrateIcons();
  setupStaticEventListeners();
  setupDragAndDrop();
  document.getElementById("btn-close-scan-log").onclick = () => {
    document.getElementById("scan-log").hidden = true;
  };
  await Promise.all([loadRoots(), loadCollections(), loadTags()]);
  await loadFiles();
}

document.addEventListener("DOMContentLoaded", boot);
