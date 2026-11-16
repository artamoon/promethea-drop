"""Проверка плавности выезда лепестка: печатает значения анимации по кадрам."""
from __future__ import annotations

import os
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
        return {"Convert": [Item(n, hint="Format") for n in ("WebP", "PNG", "JPG", "PDF")]}

    menu = RadialMenu(rings, lambda paths: "2.4 MB")
    menu.popup(QPoint(700, 400), [str(OUT / "sample-source.jpg")])

    # дать меню появиться
    end = time.monotonic() + 0.3
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)

    menu._set_hover(0)
    samples = []
    t0 = time.monotonic()
    shot_taken = False
    while time.monotonic() - t0 < 0.32:
        app.processEvents()
        time.sleep(0.01)
        samples.append(round(menu.spring[0], 3))
        if not shot_taken and time.monotonic() - t0 > 0.09:
            menu.grab().save(str(OUT / "menu-push.png"))
            shot_taken = True

    print("spring:", samples, flush=True)
    print("deltas:", [round(b - a, 3) for a, b in zip(samples, samples[1:])], flush=True)
    menu.close()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
