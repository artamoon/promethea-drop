"""Проверка трея: состав меню и поведение левого клика (без диалога выбора файла)."""
from __future__ import annotations

import os
import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from promethea.app import PrometheaApp, PrometheaQApplication  # noqa: E402


def main() -> int:
    qapp = PrometheaQApplication(sys.argv)
    app = PrometheaApp(qapp)
    names = [a.text() for a in app.tray_menu.actions() if a.text()]
    print("actions:", names, flush=True)
    print("has About:", any("About" in n for n in names), flush=True)

    app._tray_click(QSystemTrayIcon.Trigger)
    end = time.monotonic() + 0.4
    while time.monotonic() < end:
        qapp.processEvents()
        time.sleep(0.01)
    print("menu visible after left click:", app.tray_menu.isVisible(), flush=True)
    app.tray_menu.close()
    qapp.quit()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
