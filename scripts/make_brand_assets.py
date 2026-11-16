"""Генератор иконок PROMETHEA Drop: знак «капля» на графитовой подложке.

Пишет promethea.ico (мультиразмерный), promethea.png и promethea.icns.
Запуск: .venv\\Scripts\\python.exe scripts\\make_brand_assets.py
"""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "promethea" / "assets"
GRAPHITE = (27, 29, 31, 255)
GRAPHITE_EDGE = (52, 55, 58, 255)
ORANGE = (200, 95, 50, 255)
ORANGE_LIGHT = (224, 122, 78, 255)
OFFWHITE = (238, 236, 230, 255)
MASTER = 1024


def draw_master() -> Image.Image:
    img = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = MASTER / 32

    # Скруглённая подложка.
    radius = int(7 * s)
    d.rounded_rectangle([0, 0, MASTER - 1, MASTER - 1], radius=radius, fill=GRAPHITE,
                        outline=GRAPHITE_EDGE, width=max(1, int(0.35 * s)))

    # Капля: круг + клин вверх.
    cx, cy = 16 * s, 19.5 * s
    r = 7.6 * s
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ORANGE)
    d.polygon([(cx, 5.2 * s), (cx - r * 0.92, cy), (cx + r * 0.92, cy)], fill=ORANGE)

    # Блик сверху — «стекло».
    d.ellipse([cx - r * 0.62, cy - r * 0.78, cx + r * 0.18, cy - r * 0.18], fill=ORANGE_LIGHT)

    # Вырез: знак D в негативном пространстве.
    hr = 3.3 * s
    hx, hy = cx + 0.9 * s, cy + 0.2 * s
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=OFFWHITE)
    return img


def icns(png_paths: dict[str, bytes]) -> bytes:
    """Минимальный .icns: контейнер из PNG-чанков."""
    body = b"".join(k.encode("ascii") + struct.pack(">I", len(v) + 8) + v for k, v in png_paths.items())
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def main() -> None:
    master = draw_master()
    ASSETS.mkdir(parents=True, exist_ok=True)

    master.resize((512, 512), Image.LANCZOS).save(ASSETS / "promethea.png")

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    frames = [master.resize(s, Image.LANCZOS) for s in sizes]
    frames[-1].save(ASSETS / "promethea.ico", format="ICO",
                    sizes=[(f.width, f.height) for f in frames])

    chunks = {}
    for tag, size in (("icp4", 16), ("icp5", 32), ("ic07", 128), ("ic08", 256), ("ic09", 512), ("ic10", 1024)):
        buf = ASSETS / f".icns-{size}.png"
        master.resize((size, size), Image.LANCZOS).save(buf)
        chunks[tag] = buf.read_bytes()
        buf.unlink()
    (ASSETS / "promethea.icns").write_bytes(icns(chunks))

    for name in ("promethea.png", "promethea.ico", "promethea.icns"):
        print(f"{name}: {(ASSETS / name).stat().st_size} bytes")


if __name__ == "__main__":
    main()
