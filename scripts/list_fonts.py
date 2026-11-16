"""Инвентаризация шрифтов на машине: семейство, стиль, файл.

Пишет build/fonts.txt и печатает только сводку, потому что в консоли
Windows не-ASCII ломается.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import ImageFont

ROOTS = [
    Path(r"C:\Windows\Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
    Path(__file__).resolve().parent.parent / "promethea" / "assets" / "fonts",
]
SUFFIXES = {".ttf", ".otf", ".ttc"}
OUT = Path(__file__).resolve().parent.parent / "build" / "fonts.txt"


def main() -> int:
    seen: dict[tuple[str, str], Path] = {}
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in SUFFIXES:
                continue
            try:
                font = ImageFont.truetype(str(path), 20)
                family, style = font.getname()
            except Exception:
                continue
            key = (family.strip(), style.strip())
            seen.setdefault(key, path)

    lines = [f"{fam}\t{style}\t{path}" for (fam, style), path in sorted(seen.items())]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("families:", len({k[0] for k in seen}), "files:", len(seen))
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
