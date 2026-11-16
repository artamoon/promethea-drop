"""Снимок окна метаданных: проверяем, что снизу нет пустоты."""
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
    window = tools.MetadataWindow(str(OUT / "sample-source.jpg"), lambda *a, **k: None)
    window.show()
    app.processEvents()
    window.grab().save(str(OUT / "tool-metadata.png"))
    print("size:", window.width(), "x", window.height())
    window.close()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
