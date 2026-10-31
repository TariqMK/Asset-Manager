"""
App-wide constants.

DATA_DIR sits next to the app itself (portable, like your other tools) --
not in AppData -- so the whole library.json / index / thumbnails folder
can be zipped up, moved, or backed up as one unit.
"""
import os
import sys

if getattr(sys, "frozen", False):
    # Running as a PyInstaller-built .exe
    APP_DIR = os.path.dirname(sys.executable)
else:
    # Running from source
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if getattr(sys, "frozen", False) and sys.platform == "darwin":
    # A macOS .app bundle isn't a safe place to write: replacing the app
    # on update would wipe the library, and an unsigned app launched
    # from Downloads runs from a read-only translocated copy.
    DATA_DIR = os.path.join(
        os.path.expanduser("~/Library/Application Support"), "AssetManager", "library_data"
    )
else:
    DATA_DIR = os.path.join(APP_DIR, "library_data")
INDEX_DIR = os.path.join(DATA_DIR, "index")
THUMB_DIR = os.path.join(DATA_DIR, "thumbnails")

LIBRARY_FILE = os.path.join(DATA_DIR, "library.json")
COLLECTIONS_FILE = os.path.join(DATA_DIR, "collections.json")
IMPORTED_INDEX_FILE = os.path.join(INDEX_DIR, "_imported.json")

CONTEXT_FILE = os.path.join(APP_DIR, "context.txt")

# Images/design assets only -- scope decision, see context.txt
SUPPORTED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".svg",
}

THUMBNAIL_MAX_SIZE = 320  # px, longest edge

for _d in (DATA_DIR, INDEX_DIR, THUMB_DIR):
    os.makedirs(_d, exist_ok=True)
