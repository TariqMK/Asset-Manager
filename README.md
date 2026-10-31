# Asset Manager

A lightweight desktop app for organising your image and design-asset folders with **tags, notes and collections** — without ever moving, renaming or modifying your original files.

Point it at the folders you already use, and Asset Manager builds a browsable, searchable library on top of them. Everything it knows about your files lives in its own portable data folder, so your source folders stay exactly as they are.

## Features

- **Non-destructive** — your files are never moved, renamed, edited or deleted. Removing something from the library only removes Asset Manager's record of it.
- **Watched folders** — add any folder (local, external drive or network share) and it's scanned for images, including subfolders or just the top folder — your choice. Rescan any time to pick up new files.
- **Live scan log** — scans run in the background, with a small log in the corner showing progress as each image is processed.
- **Drag & drop import** — drop individual images onto the window, or use *Import Files…*, to add files that live outside your watched folders.
- **Tags and notes** — tag any image and attach free-form notes. Browse by tag from the sidebar or filter the grid by tag.
- **Collections** — group files into a nested tree of collections, independent of where they live on disk. A file can be in as many collections as you like.
  - **Manual collections** — pick exactly which files belong.
  - **Smart collections** — membership is calculated live from tag rules (match *any* / *all* tags, combine multiple rules with AND / OR), so they never go stale.
- **Search** — find files by filename, tag or note text.
- **Missing-file tracking** — if a file disappears from its last known location, its tags and notes are kept and it's flagged as *Missing*. Use *Relink…* to point it at its new location.
- **Disconnected drive detection** — if a whole watched folder is unreachable (e.g. an unplugged drive), it's shown as disconnected instead of marking every file as missing.
- **Portable** — all library data sits in one `library_data/` folder (next to the app on Windows and Linux), so you can back it up, zip it or move it as one unit.

**Supported formats:** PNG, JPG/JPEG, GIF, WebP, BMP, TIFF and SVG.

## Download

Ready-to-run builds are on the [Releases page](https://github.com/TariqMK/Asset-Manager/releases):

| Platform | File | How to run |
| --- | --- | --- |
| Windows 10 / 11 | `AssetManager-vX.Y.Z-windows-x64.zip` | Unzip anywhere and run `AssetManager.exe` |
| macOS (Apple Silicon) | `AssetManager-vX.Y.Z-macos-arm64.zip` | Unzip and open `AssetManager.app` |
| Linux (x64) | `AssetManager-vX.Y.Z-linux-x64.tar.gz` | Extract and run `AssetManager/AssetManager` |

The version you're running is shown in the window title and next to the app name in the sidebar.

> **macOS:** the app isn't signed with an Apple Developer certificate yet, so macOS will block it the first time. Right-click `AssetManager.app` → **Open** → **Open**, or run `xattr -cr AssetManager.app` in Terminal.

> **Windows:** the app uses the Microsoft Edge WebView2 runtime, which comes with Windows 11 and most up-to-date Windows 10 installs.

## Run from source

### Requirements

- Python 3.10+ (developed on Python 3.14)
- Windows is the main development platform. On Linux, also install the Qt backend with `pip install "pywebview[qt]"`.

### Setup

```bash
git clone https://github.com/TariqMK/Asset-Manager.git
```

```bash
cd Asset-Manager
```

```bash
python -m venv venv
```

```bash
venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

```bash
python app.py
```

The app opens in its own window. On first launch, click **Add a Folder** to start building your library. When run from source, the version shows as `dev`.

### Build it yourself

You can package the app with PyInstaller. It doesn't cross-compile, so build on the operating system you're building for:

```bash
pip install pyinstaller
```

```bash
python build.py
```

The build is written to `dist/AssetManager/` on Windows and Linux (copy that whole folder wherever you want to run it from), or `dist/AssetManager.app` on macOS.

Every build is stamped with a version. Set the `VERSION` environment variable to choose it; otherwise it comes from `git describe`, e.g. `v0.3.0-2-g1a2b3c4` for two commits after the `v0.3.0` tag.

## Using Asset Manager

| Task | How |
| --- | --- |
| Add a folder to watch | Click **+** next to *Watched Folders*, pick a folder, and choose whether to include subfolders |
| Import individual images | Drag them onto the window, or click **Import Files…** |
| Pick up new files | Click **Rescan All**, or rescan a single folder from the sidebar |
| Tag or annotate an image | Click it to open the inspector, then add tags and notes |
| Create a collection | Click **+** next to *Collections*, choose *Manual* or *Smart* |
| Add an image to a collection | Tick the collection in the image's inspector panel |
| Find files that have moved | Open **Missing** in the sidebar, then use **Relink…** |
| Stop tracking a file | Click **Remove from Library** in the inspector (the file itself is untouched) |

## Where your data is stored

Asset Manager keeps everything in a `library_data/` folder:

- **Windows and Linux:** next to the app (or next to `app.py` when running from source)
- **macOS:** `~/Library/Application Support/AssetManager/library_data`, so updating the app never touches your library

```
library_data/
├── library.json        # watched folders and settings
├── collections.json    # your collection tree
├── index/              # per-folder file records (tags, notes, metadata)
└── thumbnails/         # generated preview images
```

All data is plain JSON, and every write is atomic, so a crash or power cut can't leave a half-written file behind. Writes are also retried briefly if a sync client such as OneDrive or Dropbox has the file locked.

To back up your library, copy the `library_data/` folder. To start fresh, delete it.

## Built with

- [Flask](https://flask.palletsprojects.com/) — local API serving the UI
- [pywebview](https://pywebview.flowrl.com/) — native desktop window
- [Pillow](https://python-pillow.org/) — thumbnail generation
- Vanilla HTML, CSS and JavaScript for the interface

## Releasing

Releases are built by a GitHub Actions workflow that only runs when started by hand:

1. Go to **Actions → Release → Run workflow**.
2. Choose **draft** or **public**, and whether this is a **major**, **minor** or **patch** release.

The workflow works out the next version from existing tags and releases (drafts included), builds for Windows, macOS and Linux, then tags the commit and creates the release with all three builds attached. Nothing is tagged unless all three builds succeed.

## Contributing

Issues and pull requests are welcome. If you're planning a larger change, please open an issue first to discuss it.
