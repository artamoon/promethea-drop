"""Снимок меню для неподдерживаемого файла: сообщение должно быть в центре."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promethea import ui  # noqa: E402
from promethea.radial import RadialMenu  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs"


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(ui.qss())

    target = Path(__file__).resolve().parent.parent / "dist" / "PrometheaDrop" / "PrometheaDrop.exe"
    if not target.exists():
        target = Path(__file__).resolve().parent.parent / "run.py"

    menu = RadialMenu(lambda paths: {}, lambda paths: "7.7 MB")
    menu.popup(QPoint(700, 400), [str(target)])
    end = time.monotonic() + 0.4
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)
    menu.grab().save(str(OUT / "menu-unsupported.png"))
    print("saved menu-unsupported.png", flush=True)
    menu.close()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
