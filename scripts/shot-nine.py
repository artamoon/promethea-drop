"""Проверочный снимок меню с девятью форматами (плотное кольцо)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promethea import ui  # noqa: E402
from promethea.radial import Item, RadialMenu  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs"


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(ui.qss())

    def rings(paths):
        return {"Convert": [Item(n, hint="Format") for n in
                            ("PNG", "WebP", "JPG", "HEIC", "TIFF", "AVIF", "BMP", "PDF", "GIF")]}

    src = str(OUT / "sample-source.jpg")
    menu = RadialMenu(rings, lambda paths: "840 KB")
    menu.popup(QPoint(700, 400), [src])
    end = time.monotonic() + 0.45
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.02)
    menu.grab().save(str(OUT / "menu-nine.png"))
    menu.close()
    print("saved menu-nine.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
