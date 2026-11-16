"""Снимок окна инструмента: проверяем светлую тему на плотном интерфейсе."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promethea import tools, ui  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs"


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(ui.qss())
    src = str(OUT / "sample-source.jpg")
    window = tools.ResizeWindow([src], lambda *a, **k: None)
    window.show()
    app.processEvents()
    window.grab().save(str(OUT / "tool-resize.png"))
    window.close()
    print("saved tool-resize.png")
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
