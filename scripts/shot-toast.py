"""Снимки уведомлений: стартовое (info) и результат (done)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promethea import ui  # noqa: E402
from promethea.report import Result  # noqa: E402
from promethea.toasts import H, W, ToastCard, ToastStack  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs"


def save(card: ToastCard, name: str) -> None:
    card.resize(W, H)
    card.show()
    QApplication.processEvents()
    card.grab().save(str(OUT / name))
    card.close()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(ui.qss())
    stack = ToastStack()

    info = ToastCard(stack)
    info.info("Undone", "Moved 1 file to the Recycle Bin")
    save(info, "toast-info.png")

    done = ToastCard(stack)
    done.done(Result(title="WebP · 2.4 MB → 610 KB", detail="Saved next to the original",
                     outs=[OUT / "sample-source.jpg"], good="75% smaller"))
    save(done, "toast.png")

    result = ToastCard(stack)
    result.done(Result(title="PNG → HEIC", detail="Screenshot 2026-10-31 115951.heic · 993×679 · 66.0 KB",
                       outs=[OUT / "sample-result.heic"]))
    save(result, "toast-result.png")

    working = ToastCard(stack)
    working.working("Converting to HEIC", "Screenshot 2026-10-31 115951.png")
    save(working, "toast-working.png")

    error = ToastCard(stack)
    error.error("Could not convert", "The file could not be opened")
    save(error, "toast-error.png")

    print("saved toast previews", flush=True)
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
