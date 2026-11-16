"""Контактный лист: пары «моно-подпись + серифный заголовок» в духе Nothing.

Плюс проверка кириллицы через Qt. Результат: docs/type-pairs.png и build/coverage.txt.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "build" / "fonts.txt"
OUT = ROOT / "docs" / "type-pairs.png"

W, ROW_H = 1240, 168
BG = (238, 236, 230)
INK = (52, 55, 58)
MUTED = (120, 124, 128)


def index() -> list[tuple[str, str, str]]:
    rows = []
    for line in FONTS.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def find(rows, *needles: str) -> str:
    for fam, style, path in rows:
        hay = f"{fam} {style} {Path(path).name}".lower()
        if all(n.lower() in hay for n in needles):
            return path
    raise SystemExit(f"не найден шрифт: {needles}")


def tracked(draw, xy, text, font, fill, tracking=3.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking


PAIRS = [
    ("Aspid Mono + Lancetta Serif", ("aspid", "mono"), ("lancetta", "serif")),
    ("Even Mono + Bibliografica Normal", ("even", "mono"), ("bibliografica", "normal regular")),
    ("Aspid Mono + Sustav Bold Serif", ("aspid", "mono"), ("sustav", "bold serif")),
    ("NType 82 + Georgia", ("ntype", "regular"), ("georgia", "regular")),
    ("Cascadia Mono + Cambria", ("cascadia", "roman"), ("cambria", "regular")),
    ("Consolas + Constantia", ("consolas", "regular"), ("constantia", "regular")),
]


def main() -> int:
    rows = index()
    sheet = Image.new("RGB", (W, ROW_H * len(PAIRS) + 24), BG)
    draw = ImageDraw.Draw(sheet)
    y = 12
    for title, mono_key, serif_key in PAIRS:
        mono_path = find(rows, *mono_key)
        serif_path = find(rows, *serif_key)
        mono = ImageFont.truetype(mono_path, 22)
        serif = ImageFont.truetype(serif_path, 62)
        tracked(draw, (48, y + 8), "LOOKS LIKE YOU'RE IN:", mono, MUTED, tracking=4.0)
        draw.text((48, y + 44), "INTERNATIONAL", font=serif, fill=INK)
        draw.text((W - 330, y + 12), title, font=ImageFont.truetype(mono_path, 15), fill=MUTED)
        if y + ROW_H < sheet.height:
            draw.line([(48, y + ROW_H - 14), (W - 48, y + ROW_H - 14)], fill=(210, 206, 198))
        y += ROW_H
    OUT.parent.mkdir(exist_ok=True)
    sheet.save(OUT)

    # кириллица: грузим каждый файл в Qt и смотрим QFontMetrics.inFont
    from PySide6.QtGui import QFont, QFontDatabase, QFontMetrics
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    lines = []
    for title, mono_key, serif_key in PAIRS:
        for key in (mono_key, serif_key):
            path = find(rows, *key)
            fid = QFontDatabase.addApplicationFont(path)
            fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
            family = fams[0] if fams else "?"
            fm = QFontMetrics(QFont(family))
            cyr = all(fm.inFont(ch) for ch in "Привет")
            lines.append(f"{title.split(' + ')[0] if key == mono_key else title.split(' + ')[1]} ({family}) cyrillic={cyr}")
    (ROOT / "build" / "coverage.txt").write_text("\n".join(lines), encoding="utf-8")
    print("saved", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
