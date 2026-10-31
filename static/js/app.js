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

function showCollectionModal(existingNode = null) {
  return new Promise((resolve) => {
    const root = document.getElementById("modal-root");
    const backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop";
    const isEdit = !!existingNode;
    const initialType = existingNode ? existingNode.type : "manual";
    const initial = normalizeTagFilterForEdit(existingNode ? existingNode.tag_filter : null);
    const rules = initial.rules; // array of {tags: Set, match: "any"|"all"}, mutated in place

    backdrop.innerHTML = `
      <div class="modal" style="width:400px;max-height:82vh;overflow-y:auto;">
        <h3>${isEdit ? "Edit Collection" : "New Collection"}</h3>
        <div>
          <label class="modal-label">Name</label>
          <input id="col-name" type="text" style="width:100%" value="${existingNode ? existingNode.name : ""}" placeholder="e.g. Inspiration">
        </div>
        <div>
          <label class="modal-label">Type</label>
          <select id="col-type" style="width:100%">
            <option value="manual">Manual — add files yourself</option>
            <option value="smart">Smart — auto-include by tag rules</option>
          </select>
        </div>
        <div id="smart-fields" hidden>
          <div id="combine-wrap" style="display:none;">
            <label class="modal-label">Combine rules with</label>
            <select id="col-combine" style="width:100%">
              <option value="and">AND — file must match every rule</option>
              <option value="or">OR — file must match at least one rule</option>
            </select>
          </div>
          <div id="rules-container"></div>
          <button id="btn-add-rule" class="subtle" type="button" style="margin-top:8px;width:100%;">+ Add another rule</button>
        </div>
        <div class="modal-actions">
          <button id="modal-cancel">Cancel</button>
          <button class="primary" id="modal-confirm">${isEdit ? "Save" : "Create"}</button>
        </div>
      </div>`;
    root.appendChild(backdrop);

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
            ${rules.length > 1 ? '<button type="button" class="icon subtle btn-remove-rule">×</button>' : ""}
          </div>
          <label class="modal-label">Match</label>
          <select class="rule-match" style="width:100%">
            <option value="any">Any of these tags</option>
            <option value="all">All of these tags</option>
          </select>
          <label class="modal-label">Tags</label>
          <div class="tag-checklist rule-tag-checklist"></div>
          <input type="text" class="rule-tag-add" placeholder="Add a tag and press Enter…" style="width:100%;margin-top:6px;">
        `;
        block.querySelector(".rule-match").value = rule.match;
        block.querySelector(".rule-match").onchange = (e) => { rule.match = e.target.value; };

        function renderChecklist() {
          const listEl = block.querySelector(".rule-tag-checklist");
          listEl.innerHTML = "";
          const allTagNames = new Set(state.tags.map((t) => t.name));
          rule.tags.forEach((t) => allTagNames.add(t));
          if (allTagNames.size === 0) {
            listEl.innerHTML = `<div style="font-size:12px;color:var(--text-dim);">No tags yet — add one below.</div>`;
          }
          Array.from(allTagNames).sort().forEach((name) => {
            const row = document.createElement("label");
            row.className = "collection-check";
            row.innerHTML = `<input type="checkbox" ${rule.tags.has(name) ? "checked" : ""}> ${name}`;
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

    function close(result) { root.removeChild(backdrop); resolve(result); }
    backdrop.querySelector("#modal-cancel").onclick = () => close(null);
    backdrop.querySelector("#modal-confirm").onclick = () => {
      const name = backdrop.querySelector("#col-name").value.trim();
      if (!name) return;
      const type = typeSelect.value;
      const result = { name, type };
      if (type === "smart") {
        const cleanRules = rules
          .map((r) => ({ tags: Array.from(r.tags), match: r.match }))
          .filter((r) => r.tags.length > 0);
        result.tag_filter = { rules: cleanRules, combine: backdrop.querySelector("#col-combine").value };
      }
      close(result);
    };
  });
}

function confirmModal(message) {
  return new Promise((resolve) => {
    const root = document.getElementById("modal-root");
    const backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop";
    backdrop.innerHTML = `
      <div class="modal">
        <h3>${message}</h3>
        <div class="modal-actions">
          <button id="modal-cancel">Cancel</button>
          <button class="danger" id="modal-confirm">Confirm</button>
        </div>
      </div>`;
    root.appendChild(backdrop);
    backdrop.querySelector("#modal-cancel").onclick = () => { root.removeChild(backdrop); resolve(false); };
    backdrop.querySelector("#modal-confirm").onclick = () => { root.removeChild(backdrop); resolve(true); };
  });
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

function navItem({ label, count, active, onClick, extraButtons, icon, badge, title }) {
  const li = document.createElement("li");
  li.className = "nav-item" + (active ? " active" : "");
  li.innerHTML = `<span class="label"></span><span class="nav-badge"></span><span class="count"></span><span class="row-actions"></span>`;
  li.querySelector(".label").textContent = (icon ? icon + " " : "") + label;
  if (count !== undefined) li.querySelector(".count").textContent = count;
  if (badge) li.querySelector(".nav-badge").textContent = badge;
  if (title) li.title = title;
  li.addEventListener("click", (e) => {
    if (e.target.closest(".row-actions")) return;
    onClick();
  });
  if (extraButtons) {
    const actions = li.querySelector(".row-actions");
    extraButtons.forEach((btn) => {
      const b = document.createElement("button");
      b.className = "icon";
      b.textContent = btn.icon;
      b.title = btn.title;
      b.onclick = (e) => { e.stopPropagation(); btn.onClick(); };
      actions.appendChild(b);
    });
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
        badge: root.reachable === false ? "disconnected" : undefined,
        title: root.reachable === false
          ? `${root.path}\nCan't reach this folder right now (unplugged drive or offline share?). Its files keep their tags and won't be marked missing.`
          : root.path,
        active: state.view.type === "root" && state.view.id === root.id,
        onClick: () => setView({ type: "root", id: root.id }),
        extraButtons: [
          { icon: "⟳", title: "Rescan", onClick: () => rescanRoot(root.id) },
          { icon: "×", title: "Stop watching", onClick: () => removeRoot(root.id) },
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
        icon: node.type === "smart" ? "⚡" : undefined,
        onClick: () => setView({ type: "collection", id: node.id }),
        extraButtons: [
          { icon: "+", title: "New sub-collection", onClick: () => addCollection(node.id) },
          { icon: "✎", title: node.type === "smart" ? "Edit rule" : "Rename", onClick: () => renameCollection(node) },
          { icon: "×", title: "Delete", onClick: () => deleteCollection(node) },
        ],
      });
      container.appendChild(li);
      if (node.children && node.children.length) {
        const childUl = document.createElement("ul");
        childUl.className = "collection-children";
        li.appendChild(childUl);
        renderNodes(node.children, childUl);
      }
    });
  }
  renderNodes(state.collections, tree);
}

function renderTagFilter() {
  const el = document.getElementById("tag-filter");
  el.innerHTML = "";
  state.tags.slice(0, 12).forEach((tag) => {
    const chip = document.createElement("span");
    chip.className = "tag-chip" + (state.activeTag === tag.name ? " active" : "");
    chip.textContent = tag.name;
    chip.onclick = () => toggleActiveTag(tag.name);
    el.appendChild(chip);
  });
}

let tagsSidebarCollapsed = false;

function renderTagsSidebar() {
  const el = document.getElementById("tags-sidebar-list");
  el.innerHTML = "";
  if (state.tags.length === 0) {
    el.innerHTML = `<li style="padding:6px 8px;font-size:12px;color:var(--text-dim);">No tags yet</li>`;
    return;
  }
  state.tags.forEach((tag) => {
    el.appendChild(
      navItem({
        label: tag.name,
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

function renderGrid() {
  const grid = document.getElementById("grid");
  const emptyState = document.getElementById("empty-state");
  grid.innerHTML = "";

  if (state.files.length === 0) {
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;

  state.files.forEach((file) => {
    const card = document.createElement("div");
    card.className = "thumb-card" + (file.id === state.selectedFileId ? " selected" : "");
    card.dataset.id = file.id;

    const isMissing = file.status === "missing";
    const hasThumb = file.thumbnail && IMAGE_EXTENSIONS.has(extOf(file.filename));

    card.innerHTML = `
      <div class="thumb-image-wrap">
        ${hasThumb
          ? `<img src="/api/thumbnails/${file.id}.png" loading="lazy" alt="">`
          : `<span class="placeholder-icon">▨</span>`}
      </div>
      ${isMissing ? `<span class="thumb-missing-badge">Missing</span>` : ""}
      <div class="thumb-meta">
        <div class="thumb-filename" title="${file.filename}">${file.filename}</div>
        <div class="thumb-tags">${file.tags.slice(0, 3).map((t) => `<span class="mini-tag">${t}</span>`).join("")}</div>
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
  renderGrid();
  await renderInspector();
}

async function renderInspector() {
  const file = state.files.find((f) => f.id === state.selectedFileId);
  if (!file) return;

  const inspector = document.getElementById("inspector");
  inspector.hidden = false;

  const hasThumb = file.thumbnail && IMAGE_EXTENSIONS.has(extOf(file.filename));
  document.getElementById("inspector-preview").src = hasThumb ? `/api/thumbnails/${file.id}.png` : "";
  document.getElementById("missing-banner").hidden = file.status !== "missing";
  document.getElementById("btn-relink").hidden = file.status !== "missing";
  document.getElementById("inspector-filename").textContent = file.filename;
  document.getElementById("inspector-path").textContent = file.path;

  const metaBits = [];
  if (file.width && file.height) metaBits.push(`${file.width}×${file.height}`);
  if (file.size_bytes) metaBits.push(formatBytes(file.size_bytes));
  metaBits.push(file.root_label);
  document.getElementById("inspector-meta").textContent = metaBits.join(" · ");

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
    chip.innerHTML = `${tag} <button title="Remove">×</button>`;
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
  input.placeholder = "Add tag…";
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
    el.innerHTML = `<div style="font-size:12px;color:var(--text-dim);">No collections yet.</div>`;
    return;
  }
  const memberOf = new Set(await api(`/api/files/${file.id}/collections`));
  el.innerHTML = "";
  for (const col of flat) {
    const isSmart = col.type === "smart";
    const row = document.createElement("label");
    row.className = "collection-check";
    const checked = memberOf.has(col.id);
    row.innerHTML = `<input type="checkbox" ${checked ? "checked" : ""} ${isSmart ? "disabled" : ""}> ${col.name}${isSmart ? '<span class="smart-badge">auto</span>' : ""}`;
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
  const ok = await confirmModal("Remove this file from the library? Your file on disk is not affected.");
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
  await api("/api/roots", { method: "POST", body: JSON.stringify({ path }) });
  await loadRoots();
  await loadTags();
  await loadFiles();
}

async function rescanRoot(rootId) {
  const summary = await api(`/api/roots/${rootId}/rescan`, { method: "POST" });
  await loadRoots();
  await loadFiles();
  if (summary.root_unreachable) {
    const root = state.roots.find((r) => r.id === rootId);
    alert(`Couldn't reach "${root ? root.label : "this folder"}" -- is the drive connected?\nNothing was marked missing.`);
  }
}

async function rescanAll() {
  const summaries = await api("/api/roots/rescan-all", { method: "POST" });
  await loadRoots();
  await loadFiles();
  const unreachable = summaries
    .filter((s) => s.root_unreachable)
    .map((s) => (state.roots.find((r) => r.id === s.root_id) || {}).label || "?");
  if (unreachable.length) {
    alert(`Couldn't reach: ${unreachable.join(", ")} -- is the drive connected?\nFiles in those folders were not marked missing.`);
  }
}

async function removeRoot(rootId) {
  const ok = await confirmModal("Stop watching this folder? Your files are not affected, but this app will forget their tags.");
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
  const ok = await confirmModal(`Delete "${node.name}" and its sub-collections? Files stay in your library.`);
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
      alert("Couldn't read file paths from the drop. Try \"Import Files…\" instead.");
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
  document.getElementById("tags-section-header").onclick = () => {
    tagsSidebarCollapsed = !tagsSidebarCollapsed;
    document.getElementById("tags-sidebar-list").hidden = tagsSidebarCollapsed;
    document.getElementById("tags-chevron").textContent = tagsSidebarCollapsed ? "▸" : "▾";
  };
  document.getElementById("btn-import").onclick = importFilesFlow;
  document.getElementById("btn-rescan").onclick = rescanAll;
  document.getElementById("btn-close-inspector").onclick = closeInspector;

  document.getElementById("search").addEventListener("input", debounce((e) => {
    state.search = e.target.value;
    loadFiles();
  }, 300));
}

async function boot() {
  setupStaticEventListeners();
  setupDragAndDrop();
  await Promise.all([loadRoots(), loadCollections(), loadTags()]);
  await loadFiles();
}

document.addEventListener("DOMContentLoaded", boot);
