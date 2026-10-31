"""
Asset Manager -- a non-destructive, Eagle-style tagging layer over your
own image folders. Never moves or renames your source files.

Run with:  python app.py
Packaged into a .exe with PyInstaller -- see build.py.
"""
import os
import threading

from flask import Flask, jsonify, request, send_file, render_template

import webview

from backend import config, library, collections as collections_backend
from backend.version import display_version

app = Flask(__name__, static_folder="static", template_folder="templates")


# ---------------------------------------------------------------- page

@app.route("/")
def index():
    return render_template("index.html", version=display_version())


# ---------------------------------------------------------------- roots

@app.route("/api/roots", methods=["GET"])
def get_roots():
    # "reachable" is checked live, not stored -- it lets the sidebar flag
    # an unplugged drive / unmounted share as disconnected.
    roots = [dict(r, reachable=os.path.isdir(r["path"])) for r in library.list_roots()]
    return jsonify(roots)


@app.route("/api/roots", methods=["POST"])
def add_root():
    payload = request.get_json(force=True)
    path = payload.get("path")
    if not path or not os.path.isdir(path):
        return jsonify({"error": "Not a valid folder path"}), 400
    root = library.add_root(path, label=payload.get("label"))
    summary = library.scan_root(root["id"])
    return jsonify({"root": root, "scan": summary})


@app.route("/api/roots/<root_id>/rescan", methods=["POST"])
def rescan_root(root_id):
    try:
        summary = library.scan_root(root_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify(summary)


@app.route("/api/roots/rescan-all", methods=["POST"])
def rescan_all():
    return jsonify(library.scan_all_roots())


@app.route("/api/roots/<root_id>", methods=["DELETE"])
def delete_root(root_id):
    removed_ids = library.remove_root(root_id)
    collections_backend.prune_file_ids(removed_ids)
    return jsonify({"ok": True})


@app.route("/api/pick-folder", methods=["POST"])
def pick_folder():
    window = webview.windows[0]
    result = window.create_file_dialog(webview.FOLDER_DIALOG)
    path = result[0] if result else None
    return jsonify({"path": path})


# ---------------------------------------------------------------- files

@app.route("/api/files", methods=["GET"])
def get_files():
    collection_id = request.args.get("collection_id")
    tag = request.args.get("tag")
    status = request.args.get("status")
    search = request.args.get("q")
    root_id = request.args.get("root_id")

    collection_file_ids = None
    if collection_id:
        collection_file_ids = collections_backend.get_file_ids(collection_id)

    files = library.list_files(
        collection_file_ids=collection_file_ids, tag=tag, status=status, search=search,
        root_id=root_id,
    )
    return jsonify(files)


@app.route("/api/files/<file_id>", methods=["PATCH"])
def patch_file(file_id):
    payload = request.get_json(force=True)
    record = library.update_file(
        file_id, tags=payload.get("tags"), notes=payload.get("notes")
    )
    if record is None:
        return jsonify({"error": "File not found"}), 404
    return jsonify(record)


@app.route("/api/files/<file_id>", methods=["DELETE"])
def remove_file(file_id):
    ok = library.delete_file(file_id)
    if not ok:
        return jsonify({"error": "File not found"}), 404
    collections_backend.prune_file_ids([file_id])
    return jsonify({"ok": True})


@app.route("/api/files/<file_id>/collections", methods=["GET"])
def get_file_collections(file_id):
    return jsonify(collections_backend.collection_ids_for_file(file_id))


@app.route("/api/files/<file_id>/relink", methods=["POST"])
def relink_file(file_id):
    window = webview.windows[0]
    result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False)
    if not result:
        return jsonify({"error": "Cancelled"}), 400
    record = library.relink_file(file_id, result[0])
    if record is None:
        return jsonify({"error": "Could not relink"}), 400
    return jsonify(record)


@app.route("/api/tags", methods=["GET"])
def get_tags():
    counts = library.tag_counts()
    return jsonify([{"name": t, "count": counts[t]} for t in sorted(counts.keys())])


@app.route("/api/thumbnails/<file_id>.png")
def get_thumbnail(file_id):
    from backend.thumbnails import thumbnail_path
    path = thumbnail_path(file_id)
    if not os.path.exists(path):
        return "", 404
    return send_file(path, mimetype="image/png")


# ---------------------------------------------------------------- import (drag & drop)

@app.route("/api/import", methods=["POST"])
def import_files():
    payload = request.get_json(force=True)
    paths = payload.get("paths", [])
    created_ids = library.import_files(paths)
    return jsonify({"created": created_ids})


@app.route("/api/pick-files", methods=["POST"])
def pick_files():
    window = webview.windows[0]
    file_types = ("Images (*.png;*.jpg;*.jpeg;*.gif;*.webp;*.bmp;*.tiff;*.svg)",)
    result = window.create_file_dialog(
        webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types
    )
    paths = list(result) if result else []
    created_ids = library.import_files(paths)
    return jsonify({"created": created_ids})


# ---------------------------------------------------------------- collections

@app.route("/api/collections", methods=["GET"])
def get_collections():
    return jsonify(collections_backend.get_tree())


@app.route("/api/collections", methods=["POST"])
def create_collection():
    payload = request.get_json(force=True)
    node = collections_backend.create(
        payload["name"],
        parent_id=payload.get("parent_id"),
        type=payload.get("type", "manual"),
        tag_filter=payload.get("tag_filter"),
    )
    return jsonify(node)


@app.route("/api/collections/<collection_id>", methods=["PATCH"])
def rename_collection(collection_id):
    payload = request.get_json(force=True)
    node = collections_backend.update(
        collection_id, name=payload.get("name"), tag_filter=payload.get("tag_filter")
    )
    if node is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(node)


@app.route("/api/collections/<collection_id>", methods=["DELETE"])
def delete_collection(collection_id):
    ok = collections_backend.delete(collection_id)
    if not ok:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"ok": True})


@app.route("/api/collections/<collection_id>/files", methods=["POST"])
def add_files_to_collection(collection_id):
    payload = request.get_json(force=True)
    try:
        node = collections_backend.add_files(collection_id, payload.get("file_ids", []))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if node is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(node)


@app.route("/api/collections/<collection_id>/files/<file_id>", methods=["DELETE"])
def remove_file_from_collection(collection_id, file_id):
    try:
        node = collections_backend.remove_file(collection_id, file_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if node is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(node)


# ---------------------------------------------------------------- boot

def run_flask():
    app.run(host="127.0.0.1", port=57433, debug=False, use_reloader=False)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    window = webview.create_window(
        f"Asset Manager {display_version()}",
        "http://127.0.0.1:57433/",
        width=1400,
        height=900,
        min_size=(1000, 640),
        background_color="#161616",
    )
    webview.start()
