"""Builds every Asset Manager brand image from the icon masters in assets/icon/.

Writes:
  assets/icon/asset-manager.png    1024 x 1024 px
  assets/icon/asset-manager.ico    16, 20, 24, 32, 40, 48, 64, 128, 256 px (Windows)
  assets/icon/asset-manager.icns   16 to 1024 px, with @2x sizes (macOS)
  assets/banner.png                README banner, 1280 x 320 px drawn at 2x
  assets/social-card.png           GitHub social preview, 1280 x 640 px
  docs/icon.svg, docs/apple-touch-icon.png (180 px), docs/social-card.png
                                   copies for the GitHub Pages site

The 16, 24 and 32 px sizes come from asset-manager-small.svg. All other sizes
come from asset-manager.svg. Colours match static/css/style.css.

Run it from the repo root with a Python that has PySide6 and Pillow. These are
only needed to make the images, not to run the app:
    pip install PySide6 Pillow
    python assets/make_assets.py

The banner and card use Segoe UI Variable and Cascadia Mono when installed
(Windows 11), so run it on Windows for matching results.
"""

import io
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QPointF, QRectF
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QGuiApplication,
    QImage,
    QPainter,
    QPen,
)
from PySide6.QtSvg import QSvgRenderer

# ------------------------------------------------------------ brand values
NAME = "Asset Manager"
TAGLINE = "Tag, sort and find images. Files untouched."
SUBLINE = "Windows · macOS · Linux"

BG_DEEP = "#0f0f10"  # --bg-deep
HAIRLINE = QColor(237, 237, 237, 36)  # --hairline-strong
TEXT = "#ededed"  # --text
TEXT_2 = "#a1a1a6"  # --text-2
TEXT_3 = "#85858b"  # --text-3
SANS = ["Segoe UI Variable Display", "Segoe UI", "SF Pro Display", "Helvetica Neue", "Arial"]
MONO = ["Cascadia Mono", "Consolas", "SF Mono", "Menlo", "DejaVu Sans Mono"]
# ------------------------------------------------------------------------

ASSETS = Path(__file__).resolve().parent
ICON_DIR = ASSETS / "icon"
MASTER = ICON_DIR / "asset-manager.svg"
SMALL = ICON_DIR / "asset-manager-small.svg"
SMALL_SIZES = {16, 24, 32}

ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]
ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]  # Pillow writes the @2x entries from these.


def render_svg(svg: Path, size: int) -> Image.Image:
    """Render an SVG to a square RGBA Pillow image of the given size."""
    renderer = QSvgRenderer(QByteArray(svg.read_bytes()))
    if not renderer.isValid():
        sys.exit(f"Cannot read {svg}")
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    buffer = QByteArray()
    qbuf = QBuffer(buffer)
    qbuf.open(QBuffer.OpenModeFlag.WriteOnly)
    image.save(qbuf, "PNG")
    qbuf.close()
    return Image.open(io.BytesIO(bytes(buffer))).convert("RGBA")


def icon(size: int) -> Image.Image:
    return render_svg(SMALL if size in SMALL_SIZES else MASTER, size)


def make_icons() -> None:
    png = ICON_DIR / "asset-manager.png"
    icon(1024).save(png)
    print(f"Wrote {png.relative_to(ASSETS.parent)}")

    ico = ICON_DIR / "asset-manager.ico"
    frames = [icon(s) for s in ICO_SIZES]
    # Pillow writes each frame as PNG inside the .ico.
    frames[-1].save(ico, format="ICO", sizes=[(s, s) for s in ICO_SIZES], append_images=frames[:-1])
    print(f"Wrote {ico.relative_to(ASSETS.parent)}")

    icns = ICON_DIR / "asset-manager.icns"
    images = [icon(s) for s in ICNS_SIZES]
    images[-1].save(icns, format="ICNS", append_images=images[:-1])
    print(f"Wrote {icns.relative_to(ASSETS.parent)}")


def font(families: list[str], pixel_size: int, weight: QFont.Weight) -> QFont:
    available = set(QFontDatabase.families())
    result = QFont()
    result.setFamilies([f for f in families if f in available] or families)
    result.setPixelSize(pixel_size)
    result.setWeight(weight)
    return result


def draw_master(painter: QPainter, rect: QRectF) -> None:
    QSvgRenderer(QByteArray(MASTER.read_bytes())).render(painter, rect)


def make_banner() -> None:
    """1280 x 320 px at 2x: icon, then name over tagline, centred as one group."""
    s = 2
    w, h = 1280 * s, 320 * s
    image = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Background card: 24 px radius, 1 px border.
    p.setPen(QPen(HAIRLINE, 1 * s))
    p.setBrush(QColor(BG_DEEP))
    p.drawRoundedRect(QRectF(0.5 * s, 0.5 * s, w - 1 * s, h - 1 * s), 24 * s, 24 * s)

    icon_size, gap = 176 * s, 40 * s
    name_font = font(SANS, 96 * s, QFont.Weight.DemiBold)
    tag_font = font(MONO, 24 * s, QFont.Weight.Normal)
    nm, tm = QFontMetrics(name_font), QFontMetrics(tag_font)
    text_w = max(nm.horizontalAdvance(NAME), tm.horizontalAdvance(TAGLINE))
    left = (w - (icon_size + gap + text_w)) / 2
    draw_master(p, QRectF(left, (h - icon_size) / 2, icon_size, icon_size))

    # Name (cap height) and tagline (x-height) stacked, centred on the icon.
    line_gap = 56 * s  # Leaves clear space under the descender of the "g" in the name.
    block = nm.capHeight() + line_gap + tm.xHeight()
    name_base = (h - block) / 2 + nm.capHeight()
    tx = left + icon_size + gap
    p.setFont(name_font)
    p.setPen(QColor(TEXT))
    p.drawText(QPointF(tx - name_font.pixelSize() * 0.035, name_base), NAME)
    p.setFont(tag_font)
    p.setPen(QColor(TEXT_2))
    p.drawText(QPointF(tx, name_base + line_gap + tm.xHeight()), TAGLINE)
    p.end()

    out = ASSETS / "banner.png"
    image.save(str(out))
    print(f"Wrote {out.relative_to(ASSETS.parent)}")


# Social card: the fixed GitHub repo-card layout, same values as the
# standard make_social_card.py. Everything stays 80 px inside each edge.
CARD_W, CARD_H, SAFE = 1280, 640, 80
CARD_ICON, CARD_ICON_TOP, CARD_ICON_GAP = 168, 150, 40
CARD_NAME_PX, CARD_NAME_SPACING = 112, 98
CARD_TAGLINE_PX, CARD_TAGLINE_BASELINE = 34, 420
CARD_SUBLINE_PX, CARD_SUBLINE_BASELINE = 24, 476


def fit(base: QFont, text: str, max_width: float) -> QFont:
    """Shrink the font 2 px at a time until the text fits max_width."""
    result = QFont(base)
    while QFontMetrics(result).horizontalAdvance(text) > max_width - 8 and result.pixelSize() > 12:
        result.setPixelSize(result.pixelSize() - 2)
    if result.pixelSize() < base.pixelSize():
        print(f'Warning: "{text}" shrank to {result.pixelSize()} px to fit.')
    return result


def make_social_card() -> QImage:
    image = QImage(CARD_W, CARD_H, QImage.Format.Format_ARGB32)
    image.fill(QColor(BG_DEEP))  # Full bleed: GitHub rounds and crops the card itself.
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    safe_w = CARD_W - 2 * SAFE

    name_font = font(SANS, CARD_NAME_PX, QFont.Weight.DemiBold)
    name_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, CARD_NAME_SPACING)
    icon_part = CARD_ICON + CARD_ICON_GAP
    name_font = fit(name_font, NAME, safe_w - icon_part)
    nm = QFontMetrics(name_font)
    left = (CARD_W - (icon_part + nm.horizontalAdvance(NAME))) / 2
    draw_master(p, QRectF(left, CARD_ICON_TOP, CARD_ICON, CARD_ICON))
    p.setFont(name_font)
    p.setPen(QColor(TEXT))
    baseline = CARD_ICON_TOP + CARD_ICON / 2 + nm.capHeight() / 2
    p.drawText(QPointF(left + icon_part - name_font.pixelSize() * 0.035, baseline), NAME)

    for text, px, colour, y in (
        (TAGLINE, CARD_TAGLINE_PX, TEXT_2, CARD_TAGLINE_BASELINE),
        (SUBLINE, CARD_SUBLINE_PX, TEXT_3, CARD_SUBLINE_BASELINE),
    ):
        f = fit(font(MONO, px, QFont.Weight.Normal), text, safe_w)
        p.setFont(f)
        p.setPen(QColor(colour))
        p.drawText(QPointF((CARD_W - QFontMetrics(f).horizontalAdvance(text)) / 2, y), text)
    p.end()

    out = ASSETS / "social-card.png"
    image.save(str(out))
    print(f"Wrote {out.relative_to(ASSETS.parent)}")
    return image


def check_safe_area(image: QImage) -> None:
    bg = QColor(BG_DEEP)
    xs, ys = [], []
    for y in range(image.height()):
        for x in range(image.width()):
            if image.pixelColor(x, y) != bg:
                xs.append(x)
                ys.append(y)
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    if x0 < SAFE or y0 < SAFE or x1 > CARD_W - SAFE or y1 > CARD_H - SAFE:
        sys.exit(f"Social card content x {x0}-{x1}, y {y0}-{y1} is outside the {SAFE} px safe area")
    print(f"Social card safe area check passed (content x {x0}-{x1}, y {y0}-{y1})")


def copy_to_site() -> None:
    """Pages serves only docs/, so the site gets its own copies."""
    docs = ASSETS.parent / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "icon.svg").write_bytes(MASTER.read_bytes())
    (docs / "social-card.png").write_bytes((ASSETS / "social-card.png").read_bytes())
    # iOS rounds the corners itself and shows transparency as black, so fill them.
    touch = Image.new("RGBA", (180, 180), BG_DEEP)
    touch.alpha_composite(render_svg(MASTER, 180))
    touch.convert("RGB").save(docs / "apple-touch-icon.png")
    print("Wrote docs/icon.svg, docs/social-card.png, docs/apple-touch-icon.png")


def main() -> None:
    app = QGuiApplication(sys.argv[:1])  # noqa: F841 - Qt needs an application object.
    make_icons()
    make_banner()
    check_safe_area(make_social_card())
    copy_to_site()


if __name__ == "__main__":
    main()
