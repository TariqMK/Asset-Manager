"""
Collections: a nested tree, independent of where files physically live.
A file can belong to any number of collections regardless of which
watched root (or import) it came from.

Two kinds of collection node:
  - "manual"  -- membership is an explicit list of file ids, edited by
                 hand (checkbox in the inspector, or drag-and-drop later).
  - "smart"   -- membership is computed live from one or more tag rules
                 combined with AND/OR (see library.evaluate_tag_filter()):
                   tag_filter: {"rules": [{"tags": [...], "match": "any"|"all"}, ...],
                                "combine": "and"|"or"}
                 The older single-rule shape ({"tags": [...], "match": ...})
                 is still accepted. No file_ids are stored for these; they
                 can never go stale relative to your tags because they're
                 recomputed on every read.

collections.json:
{
  "nodes": {
    "<id>": {
      "id": "...", "name": "Inspiration", "parent_id": null,
      "children": ["<id2>"],
      "type": "manual", "file_ids": ["fid1", "fid2"], "tag_filter": null
    },
    "<id2>": {
      "id": "...", "name": "Warm Tones", "parent_id": "<id>",
      "children": [],
      "type": "smart", "file_ids": [],
      "tag_filter": {"rules": [{"tags": ["sunset", "warm"], "match": "any"}],
                     "combine": "and"}
    }
  },
  "root_order": ["<id>", ...]
}
"""
import uuid

from . import config, library
from .storage import read_json, write_json


def _empty():
    return {"nodes": {}, "root_order": []}


def load():
    return read_json(config.COLLECTIONS_FILE, default=_empty())


def save(data):
    write_json(config.COLLECTIONS_FILE, data)


def create(name, parent_id=None, type="manual", tag_filter=None):
    data = load()
    node = {
        "id": uuid.uuid4().hex,
        "name": name,
        "parent_id": parent_id,
        "children": [],
        "type": type,
        "file_ids": [],
        "tag_filter": tag_filter if type == "smart" else None,
    }
    data["nodes"][node["id"]] = node
    if parent_id:
        parent = data["nodes"].get(parent_id)
        if parent is None:
            raise ValueError(f"Unknown parent collection: {parent_id}")
        parent["children"].append(node["id"])
    else:
        data["root_order"].append(node["id"])
    save(data)
    return node


def update(collection_id, name=None, tag_filter=None):
    """Renames a collection and/or updates its smart tag rule. Passing
    tag_filter promotes/keeps the collection as "smart"."""
    data = load()
    node = data["nodes"].get(collection_id)
    if node is None:
        return None
    if name is not None:
        node["name"] = name
    if tag_filter is not None:
        node["type"] = "smart"
        node["tag_filter"] = tag_filter
        node["file_ids"] = []
    save(data)
    return node


def _descendants(data, collection_id):
    """All ids in the subtree rooted at collection_id, including itself."""
    ids = [collection_id]
    node = data["nodes"].get(collection_id)
    if node:
        for child_id in node["children"]:
            ids.extend(_descendants(data, child_id))
    return ids


def delete(collection_id):
    """Deletes a collection and its sub-collections. Never touches the
    underlying files or their tags -- only removes the grouping."""
    data = load()
    node = data["nodes"].get(collection_id)
    if node is None:
        return False
    for cid in _descendants(data, collection_id):
        data["nodes"].pop(cid, None)
    parent_id = node["parent_id"]
    if parent_id and parent_id in data["nodes"]:
        data["nodes"][parent_id]["children"] = [
            c for c in data["nodes"][parent_id]["children"] if c != collection_id
        ]
    else:
        data["root_order"] = [c for c in data["root_order"] if c != collection_id]
    save(data)
    return True


def _node_file_ids(node, tag_index=None):
    if node.get("type") == "smart":
        return library.evaluate_tag_filter(node.get("tag_filter"), tag_index=tag_index)
    return set(node.get("file_ids", []))


def add_files(collection_id, file_ids):
    data = load()
    node = data["nodes"].get(collection_id)
    if node is None:
        return None
    if node.get("type") == "smart":
        raise ValueError(
            "This is a smart collection -- it auto-includes files by tag. "
            "Edit its tag rule instead of adding files directly."
        )
    existing = set(node["file_ids"])
    node["file_ids"].extend(fid for fid in file_ids if fid not in existing)
    save(data)
    return node


def remove_file(collection_id, file_id):
    data = load()
    node = data["nodes"].get(collection_id)
    if node is None:
        return None
    if node.get("type") == "smart":
        raise ValueError(
            "This is a smart collection -- remove the matching tag from "
            "the file instead of removing it here."
        )
    node["file_ids"] = [f for f in node["file_ids"] if f != file_id]
    save(data)
    return node


def prune_file_ids(file_ids):
    """Drops file ids from every manual collection. Called when files
    stop being tracked (Remove from Library, Stop watching a folder) so
    collections don't keep -- and count -- ids that no longer exist."""
    gone = set(file_ids)
    if not gone:
        return
    data = load()
    changed = False
    for node in data["nodes"].values():
        kept = [f for f in node.get("file_ids", []) if f not in gone]
        if len(kept) != len(node.get("file_ids", [])):
            node["file_ids"] = kept
            changed = True
    if changed:
        save(data)


def collection_ids_for_file(file_id):
    """Ids of every collection that directly contains file_id (manual
    membership, or a smart rule it matches). Not inherited from
    sub-collections -- this is what the inspector's checkboxes show."""
    data = load()
    tag_index = library.build_tag_index()
    return [
        cid for cid, node in data["nodes"].items()
        if file_id in _node_file_ids(node, tag_index)
    ]


def get_tree():
    """Returns the tree in a nested, frontend-friendly shape."""
    data = load()
    # One pass over the library shared by every smart collection in the
    # tree, instead of one pass per collection -- see build_tag_index().
    tag_index = library.build_tag_index()

    def build(node_id):
        node = data["nodes"][node_id]
        return {
            "id": node["id"],
            "name": node["name"],
            "type": node.get("type", "manual"),
            "tag_filter": node.get("tag_filter"),
            "file_count": len(_node_file_ids(node, tag_index)),
            "children": [build(c) for c in node["children"]],
        }

    return [build(rid) for rid in data["root_order"] if rid in data["nodes"]]


def get_file_ids(collection_id, include_descendants=True):
    data = load()
    if collection_id not in data["nodes"]:
        return set()
    ids = _descendants(data, collection_id) if include_descendants else [collection_id]
    tag_index = library.build_tag_index()
    file_ids = set()
    for cid in ids:
        file_ids.update(_node_file_ids(data["nodes"][cid], tag_index))
    return file_ids
