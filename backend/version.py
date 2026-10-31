"""
App version shown in the window title and the sidebar.

Left as "dev" in the repo; build.py overwrites this file with the build's
version just before PyInstaller runs (and restores it afterwards), so
every built app reports which version it is.
"""
__version__ = "dev"


def display_version():
    """"v1.2.3" for a release, plain "dev" when running from source."""
    return __version__ if __version__ == "dev" else f"v{__version__}"
