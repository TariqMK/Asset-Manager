"""
Build the app with PyInstaller for the current platform.

PyInstaller doesn't cross-compile, so run this on the OS you're
building for (the release workflow runs it on Windows, macOS and Linux):

    pip install pyinstaller
    python build.py

Output lands in dist/:
  - Windows / Linux: dist/AssetManager/ -- copy that whole folder wherever
    you want to run it from; library_data/ is created alongside the
    executable on first launch, same portable pattern as your other tools.
  - macOS: dist/AssetManager.app -- library data goes to
    ~/Library/Application Support/AssetManager (see backend/config.py).

Every build is stamped with a version, shown in the app's title. It comes
from the VERSION environment variable (set by the release workflow), or
else from `git describe`, e.g. "0.3.0-2-g1a2b3c4" for two commits past
v0.3.0. backend/version.py is only rewritten for the build and put back
afterwards, so the repo copy stays "dev".
"""
import os
import subprocess
import sys

import PyInstaller.__main__

# Absolute paths, because PyInstaller resolves --icon relative to the spec
# file's folder, not the current folder.
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon")

args = [
    "app.py",
    "--name=AssetManager",
    "--windowed",
    "--noconfirm",
    f"--add-data=templates{os.pathsep}templates",
    f"--add-data=static{os.pathsep}static",
]

# pywebview picks its GUI backend at runtime, so PyInstaller's analyzer
# can miss it. Name the one each platform uses explicitly.
# The icon: Windows embeds the .ico in the exe (the window and taskbar use
# it too), macOS puts the .icns in the app bundle, and Linux executables
# have no file icon, so the PNG is bundled for the window icon instead.
if sys.platform == "win32":
    args += [
        "--hidden-import=webview.platforms.winforms",
        f"--icon={os.path.join(ICON_DIR, 'asset-manager.ico')}",
    ]
elif sys.platform == "darwin":
    args += [
        "--hidden-import=webview.platforms.cocoa",
        "--osx-bundle-identifier=com.tariqmk.assetmanager",
        f"--icon={os.path.join(ICON_DIR, 'asset-manager.icns')}",
    ]
else:
    args += [
        "--hidden-import=webview.platforms.qt",
        f"--add-data={os.path.join(ICON_DIR, 'asset-manager.png')}{os.pathsep}assets/icon",
    ]

VERSION_FILE = os.path.join("backend", "version.py")


def build_version():
    if os.environ.get("VERSION"):
        return os.environ["VERSION"].lstrip("v")
    try:
        described = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "dev"
    if not described.startswith("v"):
        # No release tags yet -- `describe --always` gave a bare commit hash
        return f"0.0.0-{described}"
    return described[1:]


version = build_version()
print(f"Building Asset Manager v{version}")

with open(VERSION_FILE, encoding="utf-8") as f:
    original = f.read()
try:
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(
            original.replace('__version__ = "dev"', f'__version__ = "{version}"', 1)
        )
    PyInstaller.__main__.run(args)
finally:
    with open(VERSION_FILE, "w", encoding="utf-8", newline="") as f:
        f.write(original)
