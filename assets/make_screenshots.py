"""Retakes the README screenshots from the real app, filled with made-up sample data.

Writes (1280 x 800 px window, saved at 2x):
  assets/screenshots/library-dark.png             All files, with one image open in the details panel
  assets/screenshots/smart-collections-dark.png   A smart collection built from tag rules
  assets/screenshots/missing-files-dark.png       The Missing view, with a file ready to relink

How it works: it draws sample images into a temporary folder, builds a
library there with the app's own backend, serves the real Flask app and
its UI, and captures the page in Qt WebEngine. Your own library_data
folder is never read or changed. Paths in the UI are shown as
C:\\Users\\Alex\\Pictures\\..., so no real folder names appear.

Run it from the repo root with the app's requirements plus PySide6:
    pip install -r requirements.txt PySide6
    python assets/make_screenshots.py
"""

import json
import math
import os
import random
import shutil
import sys
import tempfile
import threading
from pathlib import Path

# ------------------------------------------------------------ settings
VERSION = "1.2.2"  # Newest release tag. Shown in the sidebar instead of "dev".
WINDOW = (1280, 800)  # Window size in px; saved at 2x. Fits 3 grid columns beside the details panel.
FAKE_PARENT = r"C:\Users\Alex\Pictures"  # Shown in place of the temporary folder.
# ---------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "assets" / "screenshots"
sys.path.insert(0, str(REPO))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # No window on screen.
os.environ["QT_SCALE_FACTOR"] = "2"
# The offscreen platform has no GPU, so Chromium must draw in software.
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing --log-level=3"

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps  # noqa: E402

# ------------------------------------------------------------ sample images

PHOTO = (1600, 1067)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def ridge(width, base, roughness, rng, points=257):
    """A mountain ridgeline by midpoint displacement: list of y values."""
    ys = [0.0] * points
    ys[0], ys[-1] = rng.uniform(-1, 1), rng.uniform(-1, 1)
    step, scale = points - 1, 1.0
    while step > 1:
        half = step // 2
        for i in range(half, points - 1, step):
            ys[i] = (ys[i - half] + ys[i + half]) / 2 + rng.uniform(-scale, scale)
        step, scale = half, scale * roughness
    return [(i * width / (points - 1), base + y * 90) for i, y in enumerate(ys)]


def grain(img, amount=10):
    noise = Image.effect_noise(img.size, amount).convert("RGB")
    return ImageChops.add(img, noise, scale=1.0, offset=-128)


def landscape(seed, sky_top, sky_low, sun, far, near, sun_pos=(0.62, 0.42), layers=4,
              lake=False, fog=False):
    rng = random.Random(seed)
    w, h = PHOTO
    sky = ImageOps.colorize(Image.linear_gradient("L").resize((w, h)), sky_top, sky_low)
    img = sky.convert("RGB")

    if sun:
        glow = Image.new("RGB", (w, h), (0, 0, 0))
        sx, sy = sun_pos[0] * w, sun_pos[1] * h
        ImageDraw.Draw(glow).ellipse((sx - 260, sy - 260, sx + 260, sy + 260), fill=sun)
        img = ImageChops.screen(img, glow.filter(ImageFilter.GaussianBlur(160)))
        ImageDraw.Draw(img).ellipse((sx - 46, sy - 46, sx + 46, sy + 46), fill=lerp(sun, (255, 255, 240), 0.6))

    horizon = h * (0.62 if lake else 0.72)
    for i in range(layers):
        t = i / max(1, layers - 1)
        line = ridge(w, horizon - (layers - i) * h * 0.07, 0.55, rng)
        layer = Image.new("L", (w, h), 0)
        ImageDraw.Draw(layer).polygon(line + [(w, h), (0, h)], fill=255)
        colour = Image.new("RGB", (w, h), lerp(far, near, t))
        if i < layers - 1:
            layer = layer.filter(ImageFilter.GaussianBlur(2 * (layers - i)))
        img.paste(colour, (0, 0), layer)
        if fog and i < layers - 1:
            mist = ImageOps.colorize(Image.linear_gradient("L").resize((w, h)), sky_low, sky_low)
            band = Image.new("L", (w, h), 0)
            y = int(horizon - (layers - i - 1) * h * 0.07)
            ImageDraw.Draw(band).rectangle((0, y - 40, w, y + 60), fill=110)
            img.paste(mist, (0, 0), band.filter(ImageFilter.GaussianBlur(40)))

    if lake:
        top = int(horizon)
        reflection = ImageOps.flip(img.crop((0, top - (h - top), w, top)))
        reflection = Image.blend(reflection, Image.new("RGB", reflection.size, near), 0.35)
        ripples = ImageDraw.Draw(reflection)
        for _ in range(140):
            y = rng.randint(0, reflection.height)
            x = rng.randint(0, w)
            ripples.line((x, y, x + rng.randint(40, 220), y), fill=lerp(near, sky_low, 0.4), width=1)
        img.paste(reflection, (0, top))
    return grain(img, 12)


def font(size, bold=False):
    for name in (("seguisb.ttf", "segoeuib.ttf") if bold else ("segoeui.ttf",)) + ("DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def northwind_logo(dark):
    """Mark above the wordmark, centred, so the app's square thumbnail crop keeps all of it."""
    w, h = 1600, 900
    bg, ink, accent = ((32, 26, 22), (242, 233, 220), (196, 140, 82)) if dark else ((242, 233, 220), (44, 36, 30), (176, 112, 58))
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    cx, cy, r = w // 2, 300, 130
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ink, width=18)
    d.polygon([(cx, cy - 84), (cx + 46, cy + 54), (cx, cy + 22), (cx - 46, cy + 54)], fill=accent)
    d.text((cx, 560), "Northwind", font=font(120, bold=True), fill=ink, anchor="mm")
    d.text((cx, 680), "COFFEE ROASTERS", font=font(44), fill=accent, anchor="mm")
    return img


def palette_card():
    img = Image.new("RGB", (1600, 900), (250, 247, 242))
    d = ImageDraw.Draw(img)
    swatches = [((44, 36, 30), "Roast 900", "#2C241E"), ((176, 112, 58), "Copper 500", "#B0703A"),
                ((214, 186, 150), "Crema 300", "#D6BA96"), ((242, 233, 220), "Milk 100", "#F2E9DC"),
                ((92, 116, 98), "Sage 600", "#5C7462")]
    for i, (c, name, hexv) in enumerate(swatches):
        x = 80 + i * 296
        d.rounded_rectangle((x, 120, x + 260, 620), 24, fill=c, outline=(220, 214, 205), width=2)
        d.text((x, 660), name, font=font(40, bold=True), fill=(44, 36, 30))
        d.text((x, 716), hexv, font=font(34), fill=(120, 110, 100))
    return img


def illustration(seed, bg, colours):
    rng = random.Random(seed)
    img = Image.new("RGB", (1400, 1400), bg)
    d = ImageDraw.Draw(img)
    for _ in range(9):
        c = rng.choice(colours)
        x, y, r = rng.randint(100, 1300), rng.randint(100, 1300), rng.randint(90, 320)
        kind = rng.random()
        if kind < 0.4:
            d.ellipse((x - r, y - r, x + r, y + r), fill=c)
        elif kind < 0.7:
            start = rng.choice([0, 90, 180, 270])
            d.pieslice((x - r, y - r, x + r, y + r), start, start + 180, fill=c)
        else:
            d.rounded_rectangle((x - r, y - r // 2, x + r, y + r // 2), r // 2, fill=c)
    return grain(img, 6)


def texture(seed, tint, blur, contrast):
    rng = random.Random(seed)
    base = Image.effect_noise((1200, 1200), 60).filter(ImageFilter.GaussianBlur(blur))
    base = ImageOps.autocontrast(base, cutoff=contrast)
    img = ImageOps.colorize(base, lerp(tint, (0, 0, 0), 0.25), lerp(tint, (255, 255, 255), 0.35))
    d = ImageDraw.Draw(img)
    for _ in range(40):
        x, y = rng.randint(0, 1200), rng.randint(0, 1200)
        d.line((x, y, x + rng.randint(-200, 200), y + rng.randint(-30, 30)), fill=lerp(tint, (0, 0, 0), 0.35), width=1)
    return grain(img, 8)


def phone_screen(accent, title):
    img = Image.new("RGB", (1200, 1600), (236, 236, 240))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((330, 120, 870, 1480), 64, fill=(20, 20, 22))
    d.rounded_rectangle((350, 140, 850, 1460), 48, fill=(250, 250, 252))
    d.rounded_rectangle((390, 220, 810, 600), 28, fill=accent)
    d.text((390, 650), title, font=font(52, bold=True), fill=(28, 28, 30))
    for i in range(4):
        d.rounded_rectangle((390, 740 + i * 46, 810 - (i % 2) * 120, 764 + i * 46), 12, fill=(222, 222, 228))
    d.rounded_rectangle((390, 1300, 810, 1380), 40, fill=(28, 28, 30))
    d.text((520, 1314), "Get started", font=font(38, bold=True), fill=(250, 250, 252))
    return img


SUNRISE = dict(sky_top=(38, 52, 92), sky_low=(244, 170, 120), sun=(255, 196, 130))
SUNSET = dict(sky_top=(52, 36, 78), sky_low=(236, 120, 92), sun=(255, 150, 90))
BLUE_HOUR = dict(sky_top=(14, 24, 52), sky_low=(84, 110, 160), sun=None)
OVERCAST = dict(sky_top=(120, 128, 136), sky_low=(196, 200, 204), sun=None)

# (relative path, image factory, tags, order); lower order shows first in the grid.
SAMPLES = [
    ("Photography/Iceland 2025/vestrahorn-sunrise.jpg",
     lambda: landscape(4, **SUNRISE, far=(150, 110, 120), near=(26, 22, 30), lake=True, sun_pos=(0.62, 0.3)),
     ["landscape", "sunrise", "iceland", "mountains", "hero"], 0),
    ("Design Library/Brand/Northwind Coffee/logo-primary.png", lambda: northwind_logo(False),
     ["logo", "brand", "northwind"], 1),
    ("Photography/Lake District/buttermere-morning.jpg",
     lambda: landscape(11, sky_top=(96, 140, 190), sky_low=(226, 222, 206), sun=(255, 236, 200),
                       sun_pos=(0.3, 0.3), far=(120, 140, 150), near=(30, 46, 40), lake=True),
     ["landscape", "lake-district", "water", "sunrise"], 2),
    ("Design Library/Illustrations/spring-campaign-01.png",
     lambda: illustration(3, (246, 238, 226), [(232, 140, 98), (92, 116, 98), (44, 36, 30), (214, 186, 150)]),
     ["illustration", "hero"], 3),
    ("Photography/Iceland 2025/kirkjufell-golden-hour.jpg",
     lambda: landscape(21, **SUNSET, far=(130, 80, 90), near=(20, 16, 24), sun_pos=(0.78, 0.5)),
     ["landscape", "sunset", "iceland", "mountains"], 4),
    ("Design Library/UI/onboarding-welcome.png", lambda: phone_screen((176, 112, 58), "Fresh every week"),
     ["ui", "mobile", "northwind"], 5),
    ("Photography/Lake District/wastwater-sunset.jpg",
     lambda: landscape(8, **SUNSET, far=(110, 70, 96), near=(24, 18, 28), lake=True, sun_pos=(0.45, 0.48)),
     ["landscape", "sunset", "lake-district", "water"], 6),
    ("Design Library/Textures/paper-warm.jpg", lambda: texture(2, (226, 210, 186), 1.2, 1),
     ["texture", "paper"], 7),
    ("Photography/Iceland 2025/jokulsarlon-blue-hour.jpg",
     lambda: landscape(15, **BLUE_HOUR, far=(70, 90, 130), near=(12, 16, 28), lake=True),
     ["landscape", "iceland", "water"], 8),
    ("Design Library/Brand/Northwind Coffee/colour-palette.png", palette_card,
     ["brand", "northwind"], 9),
    ("Photography/Lake District/catbells-fog.jpg",
     lambda: landscape(30, **OVERCAST, far=(150, 156, 160), near=(52, 60, 58), fog=True, layers=5),
     ["landscape", "lake-district", "fog", "mountains"], 10),
    ("Design Library/Illustrations/spring-campaign-02.png",
     lambda: illustration(9, (32, 40, 36), [(232, 140, 98), (214, 186, 150), (92, 116, 98), (246, 238, 226)]),
     ["illustration"], 11),
    ("Photography/Iceland 2025/reynisfjara-overcast.jpg",
     lambda: landscape(42, **OVERCAST, far=(110, 116, 122), near=(22, 24, 26), layers=3),
     ["landscape", "iceland", "fog"], 12),
    ("Design Library/Brand/Northwind Coffee/logo-reversed.png", lambda: northwind_logo(True),
     ["logo", "brand", "northwind"], 13),
    ("Design Library/Textures/concrete-grey.jpg", lambda: texture(7, (150, 150, 148), 2.5, 2),
     ["texture"], 14),
    ("Design Library/UI/onboarding-subscribe.png", lambda: phone_screen((92, 116, 98), "Pick your roast"),
     ["ui", "mobile", "northwind"], 15),
    ("Photography/Lake District/derwentwater-dawn.jpg",
     lambda: landscape(5, **SUNRISE, far=(140, 120, 140), near=(28, 30, 40), lake=True, sun_pos=(0.2, 0.46)),
     ["landscape", "sunrise", "lake-district", "water"], 16),
]
SELECTED = "vestrahorn-sunrise.jpg"
SELECTED_NOTE = "Shot at 05:40 from the black-sand spit. Use for the spring homepage hero, cropped to 16:9."
MISSING = "catbells-fog.jpg"


def build_library(sample_dir: Path):
    """Draw the sample images and build a library with the app's own backend."""
    from backend import collections, library

    for rel, make, _tags, _order in SAMPLES:
        path = sample_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        image = make()
        image.save(path, quality=90) if path.suffix == ".jpg" else image.save(path)

    roots = {}
    for name in ("Photography", "Design Library"):
        root = library.add_root(str(sample_dir / name))
        library.scan_root(root["id"])
        roots[name] = root

    by_name = {f["filename"]: f for f in library.list_files()}
    for rel, _make, tags, _order in SAMPLES:
        name = Path(rel).name
        library.update_file(by_name[name]["id"], tags=tags,
                            notes=SELECTED_NOTE if name == SELECTED else None)

    # Fix the grid order: the app lists the newest "added" first.
    order = {Path(rel).name: o for rel, _m, _t, o in SAMPLES}
    for root in roots.values():
        shard = library._load_shard(root["id"])
        for key, record in shard["files"].items():
            record["added"] = f"2025-06-{30 - order[Path(key).name]:02d}T09:00:00+00:00"
        library._save_shard(root["id"], shard)

    ids = {f["filename"]: f["id"] for f in library.list_files()}
    refresh = collections.create("Website refresh")
    heroes = collections.create("Homepage heroes", parent_id=refresh["id"])
    collections.add_files(heroes["id"], [ids[SELECTED], ids["spring-campaign-01.png"], ids["buttermere-morning.jpg"]])
    collections.add_files(refresh["id"], [ids["onboarding-welcome.png"], ids["paper-warm.jpg"]])
    rebrand = collections.create("Northwind rebrand")
    collections.add_files(rebrand["id"], [ids["logo-primary.png"], ids["logo-reversed.png"], ids["colour-palette.png"]])
    golden = collections.create("Golden hour", type="smart", tag_filter={
        "rules": [{"tags": ["sunrise", "sunset"], "match": "any"}, {"tags": ["landscape"], "match": "all"}],
        "combine": "and",
    })

    # One file moved away outside the app, so the Missing view has something to show.
    (sample_dir / "Photography/Lake District" / MISSING).unlink()
    library.scan_root(roots["Photography"]["id"])
    return {"selected": ids[SELECTED], "missing": ids[MISSING], "golden": golden["id"]}


def serve(sample_dir: Path):
    """Serve the real Flask app, with the temporary folder shown as FAKE_PARENT."""
    from werkzeug.serving import make_server

    import app as asset_app

    real = os.path.normpath(str(sample_dir))
    real_json, fake_json = json.dumps(real)[1:-1], json.dumps(FAKE_PARENT)[1:-1]

    @asset_app.app.after_request
    def hide_real_paths(response):
        if response.mimetype in ("application/json", "text/html"):
            body = response.get_data(as_text=True)
            response.set_data(body.replace(real_json, fake_json).replace(real, FAKE_PARENT))
        return response

    server = make_server("127.0.0.1", 0, asset_app.app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def capture(port: int, ids: dict, private_markers: list[str]):
    from PySide6.QtCore import QEventLoop, QTimer, QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv[:1])  # noqa: F841
    view = QWebEngineView()
    view.setFixedSize(*WINDOW)
    view.show()

    def wait(ms):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    def run(js):
        loop, result = QEventLoop(), {}
        view.page().runJavaScript(js, 0, lambda r: (result.setdefault("r", r), loop.quit()))
        loop.exec()
        return result.get("r")

    loop = QEventLoop()
    view.loadFinished.connect(loop.quit)
    view.load(QUrl(f"http://127.0.0.1:{port}/"))
    loop.exec()
    wait(1500)

    shots = [
        ("library", f"selectFile('{ids['selected']}')"),
        ("smart-collections", f"setView({{type: 'collection', id: '{ids['golden']}'}})"),
        ("missing-files", f"setView({{type: 'smart', id: 'missing'}}); "
                          f"setTimeout(async () => {{ await selectFile('{ids['missing']}'); "
                          "document.getElementById('btn-relink').scrollIntoView({block: 'nearest'}); }, 400)"),
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, js in shots:
        run("closeInspector(); setView({type: 'smart', id: 'all'}); document.activeElement.blur()")
        wait(800)
        run(js)
        wait(1500)
        text = run("document.body.innerText") or ""
        leaked = [m for m in private_markers if m and m.lower() in text.lower()]
        if leaked:
            sys.exit(f"Stopped: the {name} view shows private text: {leaked}")
        # Every section of the details panel must keep its full height. When the
        # panel is taller than the window it scrolls; nothing may be squeezed.
        squeezed = json.loads(run("""JSON.stringify([...document.querySelectorAll('#inspector > *')]
            .filter(el => el.getClientRects().length && el.scrollHeight > el.clientHeight + 1)
            .map(el => `${el.id || el.className}: ${el.clientHeight} of ${el.scrollHeight} px`))""") or "[]")
        if squeezed:
            sys.exit(f"Stopped: the {name} view squeezes details panel sections: {squeezed}")
        out = OUT_DIR / f"{name}-dark.png"
        view.grab().save(str(out))
        print(f"Wrote {out.relative_to(REPO)}")


def main():
    temp = Path(tempfile.mkdtemp(prefix="am-shots-")).resolve()
    sample_dir, data_dir = temp / "samples", temp / "library_data"
    sample_dir.mkdir()
    try:
        from backend import config, version

        # Keep the real library untouched: every data path points into temp.
        config.DATA_DIR = str(data_dir)
        config.INDEX_DIR = str(data_dir / "index")
        config.THUMB_DIR = str(data_dir / "thumbnails")
        config.LIBRARY_FILE = str(data_dir / "library.json")
        config.COLLECTIONS_FILE = str(data_dir / "collections.json")
        config.IMPORTED_INDEX_FILE = str(data_dir / "index" / "_imported.json")
        for d in (config.INDEX_DIR, config.THUMB_DIR):
            os.makedirs(d, exist_ok=True)
        version.__version__ = VERSION

        ids = build_library(sample_dir)
        server = serve(sample_dir)
        markers = [str(temp), os.environ.get("USERNAME", ""), os.environ.get("USER", ""),
                   os.environ.get("COMPUTERNAME", ""), str(REPO)]
        capture(server.server_port, ids, markers)
        server.shutdown()
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    main()
