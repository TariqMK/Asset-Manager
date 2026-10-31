"""
Thumbnail cache.

Thumbnails are generated once per file (keyed by file id, not path) and
cached as PNG in library_data/thumbnails/. PNG rather than WEBP/JPEG so
this never depends on an optional libwebp build being present, and
transparency in PNGs/GIFs is preserved instead of flattened onto a
black background.
"""
import os

from PIL import Image, ImageOps

from . import config


def thumbnail_path(file_id):
    return os.path.join(config.THUMB_DIR, f"{file_id}.png")


def delete_thumbnail(thumb_filename):
    if not thumb_filename:
        return
    path = os.path.join(config.THUMB_DIR, thumb_filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def generate_thumbnail(source_path, dest_path, max_size=None):
    """Generates a thumbnail for source_path at dest_path.
    Returns (original_width, original_height) on success, or None on
    failure (corrupt file, unreadable format, etc) -- callers should
    treat that as "no dimensions available" rather than crash the scan.
    """
    max_size = max_size or config.THUMBNAIL_MAX_SIZE
    try:
        with Image.open(source_path) as img:
            width, height = img.size
            img = ImageOps.exif_transpose(img)  # respect camera rotation
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            img.save(dest_path, format="PNG")
            return width, height
    except Exception:
        return None
