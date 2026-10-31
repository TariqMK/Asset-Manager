# Asset Manager

A lightweight desktop app for organising your image and design-asset folders with **tags, notes and collections** — without ever moving, renaming or modifying your original files.

Point it at the folders you already use, and Asset Manager builds a browsable, searchable library on top of them. Everything it knows about your files lives in its own portable data folder, so your source folders stay exactly as they are.

## Features

- **Non-destructive** — your files are never moved, renamed, edited or deleted. Removing something from the library only removes Asset Manager's record of it.
- **Watched folders** — add any folder (local, external drive or network share) and it's scanned recursively for images. Rescan any time to pick up new files.
- **Drag & drop import** — drop individual images onto the window, or use *Import Files…*, to add files that live outside your watched folders.
- **Tags and notes** — tag any image and attach free-form notes. Browse by tag from the sidebar or filter the grid by tag.
- **Collections** — group files into a nested tree of collections, independent of where they live on disk. A file can be in as many collections as you like.
  - **Manual collections** — pick exactly which files belong.
  - **Smart collections** — membership is calculated live from tag rules (match *any* / *all* tags, combine multiple rules with AND / OR), so they never go stale.
- **Search** — find files by filename, tag or note text.
- **Missing-file tracking** — if a file disappears from its last known location, its tags and notes are kept and it's flagged as *Missing*. Use *Relink…* to point it at its new location.
- **Disconnected drive detection** — if a whole watched folder is unreachable (e.g. an unplugged drive), it's shown as disconnected instead of marking every file as missing.
- **Portable** — all library data sits in a `library_data/` folder next to the app, so you can back it up, zip it or move it as one unit.

**Supported formats:** PNG, JPG/JPEG, GIF, WebP, BMP, TIFF and SVG.

## Getting started

### Requirements

- Windows 10 or 11
- Python 3.10+ (developed on Python 3.14)

Asset Manager uses [pywebview](https://pywebview.flowrl.com/), which on Windows relies on the Microsoft Edge WebView2 runtime. This is included with Windows 11 and most up-to-date Windows 10 installs.

### Run from source

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

The app opens in its own window. On first launch, click **Add a Folder** to start building your library.

### Build a standalone .exe

You can package the app into a self-contained Windows executable with PyInstaller (this must be run on Windows):

```bash
pip install pyinstaller
```

```bash
python build.py
```

The build is written to `dist/AssetManager/`. Copy that whole folder wherever you want to run it from and launch `AssetManager.exe`. A `library_data/` folder will be created alongside the exe on first run.

> If the built exe fails to open a window, add `--hidden-import=webview.platforms.winforms` to the options in `build.py` and rebuild.

## Using Asset Manager

| Task | How |
| --- | --- |
| Add a folder to watch | Click **+** next to *Watched Folders* in the sidebar |
| Import individual images | Drag them onto the window, or click **Import Files…** |
| Pick up new files | Click **Rescan All**, or rescan a single folder from the sidebar |
| Tag or annotate an image | Click it to open the inspector, then add tags and notes |
| Create a collection | Click **+** next to *Collections*, choose *Manual* or *Smart* |
| Add an image to a collection | Tick the collection in the image's inspector panel |
| Find files that have moved | Open **Missing** in the sidebar, then use **Relink…** |
| Stop tracking a file | Click **Remove from Library** in the inspector (the file itself is untouched) |

## Where your data is stored

Asset Manager keeps everything in a `library_data/` folder next to the app (or next to `app.py` when running from source):

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

## Contributing

Issues and pull requests are welcome. If you're planning a larger change, please open an issue first to discuss it.
