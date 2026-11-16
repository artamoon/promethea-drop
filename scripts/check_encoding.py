"""Починка кодировки: PowerShell 5.1 иногда портит не-ASCII при передаче аргументов.

Скрипт ищет в исходниках последовательности, которые получаются, если UTF-8
прочитать как cp1251, и восстанавливает файл tests/test_v11.py из апстрима
(единственное намеренное отличие — имя папки PROMETHEA).
"""
from __future__ import annotations

import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOJIBAKE = ("вЂ", "РІ", "Рµ", "С‚", "СЏ", "РЅ", "Р°")


def scan() -> int:
    bad = []
    for path in sorted(ROOT.joinpath("promethea").rglob("*.py")) + sorted(ROOT.joinpath("tests").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(token in line for token in MOJIBAKE):
                bad.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()[:100]}")
    print("\n".join(bad) if bad else "кодировка в порядке")
    return 1 if bad else 0


def restore_tests() -> None:
    url = "https://codeload.github.com/llamaboi55/DragShift/zip/refs/heads/main"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    tests = ROOT / "tests"
    for name in archive.namelist():
        if "/tests/" not in name or not name.endswith(".py"):
            continue
        data = archive.read(name).decode("utf-8")
        data = data.replace("out.parent.name == \"DragShift\"", "out.parent.name == \"PROMETHEA\"")
        data = data.replace("from dragshift ", "from promethea ")
        data = data.replace("from dragshift.", "from promethea.")
        (tests / Path(name).name).write_text(data, encoding="utf-8")
        print("restored", Path(name).name)


if __name__ == "__main__":
    if "--restore-tests" in sys.argv:
        restore_tests()
    raise SystemExit(scan())
