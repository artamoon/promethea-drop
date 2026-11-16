"""Снимки окон PROMETHEA Drop без участия оконного менеджера.

Нужны для проверки внешнего вида: `Qt.grab()` рисует содержимое виджета
в PNG независимо от того, что происходит на рабочем столе.
Запуск: .venv\\Scripts\\python.exe scripts\\shots.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint, QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promethea import ui  # noqa: E402
from promethea.radial import Item, RadialMenu  # noqa: E402
from promethea.settings import Settings, SettingsWindow, WelcomeWindow  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs"


def sample_image() -> str:
    from PIL import Image

    path = OUT / "sample-source.jpg"
    if not path.exists():
        Image.new("RGB", (2400, 1600), (90, 70, 60)).save(path, quality=92)
    return str(path)


def build_rings(paths: list[str]) -> dict[str, list[Item]]:
    return {
        "Convert": [
            Item("WebP", hint="Smallest for web"),
            Item("PNG", hint="Lossless"),
            Item("JPG", hint="Small, universal"),
            Item("PDF", hint="Document"),
        ],
        "Tools": [
            Item("Compress", "⇲", "tool:Compress", "Shrink file size"),
            Item("Resize", "⤢", "tool:Resize", "Change dimensions"),
            Item("Crop", "⌗", "tool:Crop", "Trim to a ratio"),
            Item("Annotate", "✎", "tool:Annotate", "Arrows · text · steps"),
            Item("Edit", "☼", "tool:Edit", "Light · colour · rotate"),
            Item("Metadata", "ⓘ", "tool:Metadata", "View · remove GPS"),
        ],
    }


def wait(app: QApplication, ms: int) -> None:
    end = time.monotonic() + ms / 1000
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.02)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(ui.qss())
    OUT.mkdir(exist_ok=True)
    settings = Settings()

    w = WelcomeWindow(settings, "Shift")
    w.show()
    app.processEvents()
    w.grab().save(str(OUT / "welcome.png"))
    w.close()

    w = SettingsWindow(settings)
    w.show()
    app.processEvents()
    w.grab().save(str(OUT / "settings.png"))
    w.close()

    menu = RadialMenu(build_rings, lambda paths: "2.4 MB")
    menu.popup(QPoint(700, 400), [sample_image()])
    wait(app, 450)          # дать анимации появления доиграть
    menu.grab().save(str(OUT / "menu.png"))
    if menu.spring:
        menu.hover = 0
        menu.spring[0] = 1.0
        menu.update()
        wait(app, 120)
        menu.grab().save(str(OUT / "menu-hover.png"))
    menu.close()
    print("saved:", ", ".join(p.name for p in sorted(OUT.glob("*.png"))))
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
