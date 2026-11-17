"""Починка кодировки: PowerShell 5.1 иногда портит не-ASCII при передаче аргументов.

Скрипт ищет в исходниках последовательности, которые получаются, если UTF-8
прочитать как cp1251.
"""
from __future__ import annotations

import re
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



if __name__ == "__main__":
    raise SystemExit(scan())
