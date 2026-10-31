"""
Library data layer.

Design (see /context.txt for the full rationale):

  library_data/
    library.json          -- watched root folders + app settings
    collections.json       -- the nested collection tree
    index/
      <root-id>.json        -- one shard per watched root: {relative_path: record}
      _imported.json         -- drag-and-dropped files not under any watched root:
                                {absolute_path: record}
    thumbnails/
      <file-id>.png

A file record looks like:
{
  "id": "uuid4",
  "tags": ["ui", "dark-mode"],
  "notes": "",
  "added": "2026-08-29T12:00:00",
  "status": "ok" | "missing",
  "width": 1920, "height": 1080,
  "size_bytes": 123456,
  "mtime": 1735500000.0,
  "thumbnail": "<id>.png"
}

Files are identified everywhere else in the app by their `id`, never by
path -- paths can move. `_build_lookup()` maps id -> (shard_name, key) so
any endpoint can find a record quickly without caring where it lives.
"""
import os
import uuid
from datetime import datetime, timezone

from . import config
from .storage import read_json, write_json
from .thumbnails import generate_thumbnail, thumbnail_path, delete_thumbnail


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _is_supported_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in config.SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------- library.json

def load_library():
    return read_json(config.LIBRARY_FILE, default={"roots": [], "settings": {}})


def save_library(data):
    write_json(config.LIBRARY_FILE, data)


def list_roots():
    return load_library().get("roots", [])


def add_root(path, label=None):
    path = os.path.normpath(path)
    lib = load_library()
    for r in lib["roots"]:
        if os.path.normpath(r["path"]) == path:
            return r  # already watching this folder
    root = {
        "id": uuid.uuid4().hex,
        "path": path,
        "label": label or os.path.basename(path.rstrip(os.sep)) or path,
        "added": _now_iso(),
    }
    lib["roots"].append(root)
    save_library(lib)
    _save_shard(root["id"], {"root_id": root["id"], "files": {}})
    return root


def remove_root(root_id):
    """Stops tracking a root. Never touches the actual files on disk --
    only deletes this app's index shard for it. Returns the ids of the
    records that were dropped, so callers can clean up references to
    them (e.g. manual collections)."""
    lib = load_library()
    lib["roots"] = [r for r in lib["roots"] if r["id"] != root_id]
    save_library(lib)
    removed_ids = []
    shard_path = _shard_path(root_id)
    if os.path.exists(shard_path):
        # keep thumbnails cleanup best-effort
        shard = _load_shard(root_id)
        for record in shard.get("files", {}).values():
            removed_ids.append(record["id"])
            delete_thumbnail(record.get("thumbnail"))
        os.remove(shard_path)
    return removed_ids


def get_root(root_id):
    for r in list_roots():
        if r["id"] == root_id:
            return r
    return None


# ---------------------------------------------------------------- index shards

def _shard_path(root_id):
    return os.path.join(config.INDEX_DIR, f"{root_id}.json")


def _load_shard(root_id):
    return read_json(_shard_path(root_id), default={"root_id": root_id, "files": {}})


def _save_shard(root_id, data):
    write_json(_shard_path(root_id), data)


def _load_imported():
    return read_json(config.IMPORTED_INDEX_FILE, default={"files": {}})


def _save_imported(data):
    write_json(config.IMPORTED_INDEX_FILE, data)


# ---------------------------------------------------------------- scanning

def scan_root(root_id):
    """Walk a watched root on disk, updating its index shard:
    - new supported image files get a fresh record + thumbnail
    - previously-known files that still exist get marked "ok"
    - previously-known files that no longer resolve get marked "missing"
      (their record, tags, and notes are kept, never deleted)
    Returns a summary dict.
    """
    root = get_root(root_id)
    if root is None:
        raise ValueError(f"Unknown root: {root_id}")

    if not os.path.isdir(root["path"]):
        # The watched folder itself isn't reachable right now -- e.g. an
        # unplugged external drive or an unmounted network share. This is
        # NOT the same thing as individual files having moved: bail out
        # without touching any file's status, otherwise every file under
        # this root would get wrongly flagged "missing" on every scan
        # until the drive is plugged back in.
        return {
            "root_id": root_id,
            "added": 0,
            "updated": 0,
            "newly_missing": 0,
            "root_unreachable": True,
        }

    shard = _load_shard(root_id)
    files = shard.setdefault("files", {})
    seen_relpaths = set()
    added, updated, missing = 0, 0, 0

    for dirpath, _dirnames, filenames in os.walk(root["path"]):
        for filename in filenames:
            if not _is_supported_image(filename):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, root["path"])
            seen_relpaths.add(rel_path)

            record = files.get(rel_path)
            try:
                stat = os.stat(abs_path)
            except OSError:
                continue

            if record is None:
                record = _new_record()
                files[rel_path] = record
                added += 1
            elif record.get("status") == "missing":
                updated += 1

            record["status"] = "ok"
            record["size_bytes"] = stat.st_size
            record["mtime"] = stat.st_mtime

            thumb_file = thumbnail_path(record["id"])
            if not os.path.exists(thumb_file) or record.get("_mtime_at_thumb") != stat.st_mtime:
                dims = generate_thumbnail(abs_path, thumb_file)
                if dims:
                    record["width"], record["height"] = dims
                record["_mtime_at_thumb"] = stat.st_mtime
                record["thumbnail"] = os.path.basename(thumb_file)

    # anything we know about but didn't see on disk this pass -> missing
    for rel_path, record in files.items():
        if rel_path not in seen_relpaths and record.get("status") != "missing":
            record["status"] = "missing"
            missing += 1

    _save_shard(root_id, shard)
    return {
        "root_id": root_id,
        "added": added,
        "updated": updated,
        "newly_missing": missing,
        "root_unreachable": False,
    }


def scan_all_roots():
    return [scan_root(r["id"]) for r in list_roots()] + [scan_imported()]


def _location_reachable(abs_path):
    """True if the drive / network share holding abs_path is reachable.
    Imported files have no watched root to check, so this is their
    equivalent of scan_root()'s root-level isdir() check."""
    drive, _rest = os.path.splitdrive(abs_path)
    anchor = (drive + os.sep) if drive else os.sep
    return os.path.isdir(anchor)


def scan_imported():
    """Re-check every drag-and-dropped / imported file, same rules as
    scan_root(): found -> "ok" (thumbnail refreshed if the file changed),
    not found -> "missing" (record, tags and notes kept). Files whose
    whole drive or share is unreachable are left untouched, so an
    unplugged drive doesn't flag everything on it as missing."""
    imported = _load_imported()
    files = imported.setdefault("files", {})
    updated, missing, unreachable = 0, 0, 0

    for abs_path, record in files.items():
        if not _location_reachable(abs_path):
            unreachable += 1
            continue
        try:
            stat = os.stat(abs_path)
        except OSError:
            if record.get("status") != "missing":
                record["status"] = "missing"
                missing += 1
            continue

        if record.get("status") == "missing":
            updated += 1
        record["status"] = "ok"
        record["size_bytes"] = stat.st_size
        record["mtime"] = stat.st_mtime

        thumb_file = thumbnail_path(record["id"])
        if not os.path.exists(thumb_file) or record.get("_mtime_at_thumb") != stat.st_mtime:
            dims = generate_thumbnail(abs_path, thumb_file)
            if dims:
                record["width"], record["height"] = dims
            record["_mtime_at_thumb"] = stat.st_mtime
            record["thumbnail"] = os.path.basename(thumb_file)

    _save_imported(imported)
    return {
        "root_id": "_imported",
        "added": 0,
        "updated": updated,
        "newly_missing": missing,
        "root_unreachable": False,
        "unreachable_files": unreachable,
    }


def _new_record():
    return {
        "id": uuid.uuid4().hex,
        "tags": [],
        "notes": "",
        "added": _now_iso(),
        "status": "ok",
        "width": None,
        "height": None,
        "size_bytes": 0,
        "mtime": None,
        "thumbnail": None,
    }


# ---------------------------------------------------------------- imported (drag & drop)

def import_files(abs_paths):
    """Add one or more individual files by absolute path, outside of any
    watched root. Used for drag-and-drop of single files."""
    imported = _load_imported()
    files = imported.setdefault("files", {})
    created = []

    for abs_path in abs_paths:
        abs_path = os.path.normpath(abs_path)
        if not _is_supported_image(os.path.basename(abs_path)):
            continue
        if abs_path in files and files[abs_path].get("status") == "ok":
            continue  # already have it
        try:
            stat = os.stat(abs_path)
        except OSError:
            continue

        record = files.get(abs_path) or _new_record()
        record["status"] = "ok"
        record["size_bytes"] = stat.st_size
        record["mtime"] = stat.st_mtime

        thumb_file = thumbnail_path(record["id"])
        dims = generate_thumbnail(abs_path, thumb_file)
        if dims:
            record["width"], record["height"] = dims
        record["_mtime_at_thumb"] = stat.st_mtime
        record["thumbnail"] = os.path.basename(thumb_file)

        files[abs_path] = record
        created.append(record["id"])

    _save_imported(imported)
    return created


# ---------------------------------------------------------------- lookup / CRUD by id

def _iter_shards():
    """Yields (shard_name, path_key_field, load_fn, save_fn) for every shard,
    where shard_name is a root_id or "_imported"."""
    for r in list_roots():
        yield r["id"], lambda rid=r["id"]: _load_shard(rid), lambda data, rid=r["id"]: _save_shard(rid, data)
    yield "_imported", _load_imported, _save_imported


def find_record(file_id):
    """Returns (shard_name, key, record, save_fn) or None."""
    for shard_name, load_fn, save_fn in _iter_shards():
        data = load_fn()
        for key, record in data.get("files", {}).items():
            if record["id"] == file_id:
                return shard_name, key, record, (lambda d=data, s=save_fn: s(d))
    return None


def update_file(file_id, tags=None, notes=None):
    found = find_record(file_id)
    if not found:
        return None
    _shard_name, _key, record, save = found
    if tags is not None:
        record["tags"] = sorted({t.strip() for t in tags if t.strip()})
    if notes is not None:
        record["notes"] = notes
    save()
    return record


def relink_file(file_id, new_absolute_path):
    """Point a missing record at a new location on disk, preserving its
    id, tags, and notes. If the new path falls inside a watched root it's
    re-keyed by relative path in that root's shard; otherwise it moves to
    the imported shard."""
    found = find_record(file_id)
    if not found:
        return None
    old_shard_name, old_key, record, _save = found
    new_absolute_path = os.path.normpath(new_absolute_path)

    try:
        stat = os.stat(new_absolute_path)
    except OSError:
        return None

    record["status"] = "ok"
    record["size_bytes"] = stat.st_size
    record["mtime"] = stat.st_mtime
    thumb_file = thumbnail_path(record["id"])
    dims = generate_thumbnail(new_absolute_path, thumb_file)
    if dims:
        record["width"], record["height"] = dims
    record["thumbnail"] = os.path.basename(thumb_file)

    # figure out the destination shard
    dest_shard_name = "_imported"
    dest_key = new_absolute_path
    for r in list_roots():
        root_path = os.path.normpath(r["path"])
        if new_absolute_path.lower().startswith(root_path.lower() + os.sep):
            dest_shard_name = r["id"]
            dest_key = os.path.relpath(new_absolute_path, root_path)
            break

    # remove from old location
    if old_shard_name == "_imported":
        old_data = _load_imported()
    else:
        old_data = _load_shard(old_shard_name)
    old_data["files"].pop(old_key, None)
    if old_shard_name == "_imported":
        _save_imported(old_data)
    else:
        _save_shard(old_shard_name, old_data)

    # add to new location
    if dest_shard_name == old_shard_name and old_shard_name != "_imported":
        # same shard reference we already popped from -- reuse old_data
        old_data["files"][dest_key] = record
        _save_shard(dest_shard_name, old_data)
    elif dest_shard_name == "_imported":
        new_data = _load_imported() if old_shard_name != "_imported" else old_data
        new_data["files"][dest_key] = record
        _save_imported(new_data)
    else:
        new_data = _load_shard(dest_shard_name)
        new_data["files"][dest_key] = record
        _save_shard(dest_shard_name, new_data)

    return record


def delete_file(file_id, delete_thumb=True):
    """Removes a record from the library (does NOT touch the file on
    disk). Used when the user wants to stop tracking a file entirely."""
    found = find_record(file_id)
    if not found:
        return False
    shard_name, key, record, _save = found
    if shard_name == "_imported":
        data = _load_imported()
        data["files"].pop(key, None)
        _save_imported(data)
    else:
        data = _load_shard(shard_name)
        data["files"].pop(key, None)
        _save_shard(shard_name, data)
    if delete_thumb:
        delete_thumbnail(record.get("thumbnail"))
    return True


# ---------------------------------------------------------------- listing / search

def _resolve_abs_path(shard_name, key):
    if shard_name == "_imported":
        return key
    root = get_root(shard_name)
    return os.path.join(root["path"], key) if root else key


def list_files(collection_file_ids=None, tag=None, status=None, search=None, root_id=None):
    """Returns a flat list of file dicts (record + id + resolved path +
    which root, for display), optionally filtered. root_id limits the
    results to one watched root's shard (or "_imported")."""
    results = []
    for shard_name, load_fn, _save_fn in _iter_shards():
        if root_id and shard_name != root_id:
            continue
        data = load_fn()
        root_label = "Imported" if shard_name == "_imported" else (get_root(shard_name) or {}).get("label", "?")
        for key, record in data.get("files", {}).items():
            if collection_file_ids is not None and record["id"] not in collection_file_ids:
                continue
            if tag and tag not in record.get("tags", []):
                continue
            if status and record.get("status") != status:
                continue
            if search:
                haystack = (key + " " + " ".join(record.get("tags", [])) + " " + record.get("notes", "")).lower()
                if search.lower() not in haystack:
                    continue
            item = dict(record)
            item.pop("_mtime_at_thumb", None)
            item["filename"] = os.path.basename(key)
            item["root_label"] = root_label
            item["path"] = _resolve_abs_path(shard_name, key)
            results.append(item)
    results.sort(key=lambda r: r.get("added", ""), reverse=True)
    return results


def all_tags():
    tags = set()
    for _shard_name, load_fn, _save_fn in _iter_shards():
        for record in load_fn().get("files", {}).values():
            tags.update(record.get("tags", []))
    return sorted(tags)


def tag_counts():
    """Returns {tag_name: number_of_files}, used for the sidebar tag list."""
    counts = {}
    for _shard_name, load_fn, _save_fn in _iter_shards():
        for record in load_fn().get("files", {}).values():
            for t in record.get("tags", []):
                counts[t] = counts.get(t, 0) + 1
    return counts


def files_matching_tags(tags, match="any", tag_index=None):
    """Returns the set of file ids whose tags satisfy a single rule.
    match="any" -> file has at least one of `tags`.
    match="all" -> file has every one of `tags`.

    Pass a precomputed `tag_index` (from build_tag_index()) when
    checking several rules in a row -- e.g. rendering the whole
    collection tree, which may have many smart collections, each with
    several rules -- so the library is only scanned once instead of
    once per rule.
    """
    wanted = set(tags)
    if not wanted:
        return set()
    index = tag_index if tag_index is not None else build_tag_index()
    sets = [index.get(t, set()) for t in wanted]
    if match == "all":
        result = sets[0]
        for s in sets[1:]:
            result = result & s
        return result
    result = set()
    for s in sets:
        result |= s
    return result


def evaluate_tag_filter(tag_filter, tag_index=None):
    """Evaluates a smart collection's full filter, which may have
    several independent rules combined with AND/OR:

        {"rules": [{"tags": [...], "match": "any"|"all"}, ...],
         "combine": "and"|"or"}

    Each rule is evaluated on its own (its own tags + its own any/all),
    then the rules' resulting sets are combined: "and" intersects them
    (a file must satisfy every rule), "or" unions them (satisfying any
    one rule is enough). This is what lets you express something like
    "(sunset OR sunrise) AND landscape" as two rules combined with AND.

    Also accepts the older single-rule shape ({"tags": [...], "match":
    ...}) for collections created before multi-rule support existed --
    treated as a single rule, so nothing already saved breaks.
    """
    if not tag_filter:
        return set()
    index = tag_index if tag_index is not None else build_tag_index()

    rules = tag_filter.get("rules")
    if rules is None:
        rules = [{"tags": tag_filter.get("tags", []), "match": tag_filter.get("match", "any")}]
    rules = [r for r in rules if r.get("tags")]  # ignore empty/incomplete rules
    if not rules:
        return set()

    combine = tag_filter.get("combine", "and")
    rule_results = [files_matching_tags(r["tags"], r.get("match", "any"), tag_index=index) for r in rules]

    if combine == "or":
        result = set()
        for r in rule_results:
            result |= r
        return result
    result = rule_results[0]
    for r in rule_results[1:]:
        result = result & r
    return result


def build_tag_index():
    """Maps each tag -> the set of file ids carrying it.

    This is NOT a persistent cache -- it's built fresh from current
    records on every call and never stored anywhere, so it can never
    go stale. It exists purely to avoid re-scanning the whole library
    once per smart-collection rule when several are evaluated together
    (see collections.get_tree()); each individual call is still a full
    pass over the library, same cost as before -- the saving comes from
    sharing that one pass across many callers in the same request.
    """
    index = {}
    for _shard_name, load_fn, _save_fn in _iter_shards():
        for record in load_fn().get("files", {}).values():
            for t in record.get("tags", []):
                index.setdefault(t, set()).add(record["id"])
    return index
