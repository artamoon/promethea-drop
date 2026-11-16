"""Isolated Microsoft Word export, run in a short-lived helper process."""
from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    if len(argv) != 2 or sys.platform != "win32":
        return 2
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(argv[0], ReadOnly=True, AddToRecentFiles=False)
        doc.SaveAs(argv[1], FileFormat=17)
        return 0
    except Exception:
        return 1
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
