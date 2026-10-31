"""
Build a single-folder Windows .exe with PyInstaller.

Run this ON WINDOWS (PyInstaller doesn't cross-compile):

    pip install pyinstaller
    python build.py

Output lands in dist/AssetManager/. Copy that whole folder wherever you
want to run it from -- library_data/ will be created alongside the exe
on first launch, same portable pattern as your other tools.
"""
import PyInstaller.__main__

PyInstaller.__main__.run([
    "app.py",
    "--name=AssetManager",
    "--windowed",
    "--noconfirm",
    "--add-data=templates;templates",
    "--add-data=static;static",
    # pywebview pulls in some backends PyInstaller's analyzer can miss;
    # if the built exe fails to open a window, add:
    #   --hidden-import=webview.platforms.winforms
    # or whichever backend pywebview picks on your machine.
])
