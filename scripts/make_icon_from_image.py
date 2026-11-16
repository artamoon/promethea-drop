"""Иконка приложения из готового знака: обрезать поля, собрать .ico/.png/.icns.

Источник — webp с чёрным знаком на белом фоне. Скрипт находит границы знака,
делает квадрат, слегка скругляет плитку и пишет набор размеров.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "promethea" / "assets"
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else None
MASTER = 1024
CORNER = 0.20          # скругление плитки, доля стороны


def build_master() -> Image.Image:
    if SOURCE is None:
        raise SystemExit("Укажите путь к изображению: python scripts/make_icon_from_image.py <image>")
    src = Image.open(SOURCE).convert("RGB")
    # границы тёмных пикселей = сам знак
    mask = src.convert("L").point(lambda v: 255 if v < 128 else 0)
    box = mask.getbbox()
    if box is None:
        raise SystemExit("на изображении нет тёмного знака")
    glyph = src.crop(box)

    # квадрат по большей стороне, знак по центру
    side = max(glyph.size)
    pad = int(side * 0.02)
    side += pad * 2
    square = Image.new("RGB", (side, side), (255, 255, 255))
    square.paste(glyph, ((side - glyph.width) // 2, (side - glyph.height) // 2))

    master = square.resize((MASTER, MASTER), Image.LANCZOS).convert("RGBA")

    # прозрачные углы: плитка со скруглением
    radius = int(MASTER * CORNER)
    alpha = Image.new("L", (MASTER, MASTER), 0)
    ImageDraw.Draw(alpha).rounded_rectangle([0, 0, MASTER - 1, MASTER - 1], radius=radius, fill=255)
    master.putalpha(alpha)
    return master


def icns(chunks: dict[str, bytes]) -> bytes:
    body = b"".join(k.encode("ascii") + struct.pack(">I", len(v) + 8) + v for k, v in chunks.items())
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def main() -> int:
    master = build_master()
    ASSETS.mkdir(parents=True, exist_ok=True)

    master.resize((512, 512), Image.LANCZOS).save(ASSETS / "promethea.png")

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    frames = [master.resize(s, Image.LANCZOS) for s in sizes]
    frames[-1].save(ASSETS / "promethea.ico", format="ICO", sizes=sizes)

    spec = {
        "icp4": 16, "icp5": 32, "ic07": 128, "ic08": 256, "ic09": 512, "ic10": 1024,
    }
    chunks: dict[str, bytes] = {}
    for tag, size in spec.items():
        buf = ASSETS / f".icns-{size}.png"
        master.resize((size, size), Image.LANCZOS).save(buf)
        chunks[tag] = buf.read_bytes()
        buf.unlink()
    (ASSETS / "promethea.icns").write_bytes(icns(chunks))

    for name in ("promethea.png", "promethea.ico", "promethea.icns"):
        print(f"{name}: {(ASSETS / name).stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
