"""Ремонт «кракозябр»: UTF-8, прочитанный как cp1251 и снова записанный в UTF-8.

PowerShell 5.1 иногда так портит не-ASCII при правках через командную строку.
Скрипт меняет пары символов обратно и печатает, сколько правок сделал.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# последовательность в файле -> настоящий символ
FIXES = {
    "вЂ¦": "…",
    "вЂ”": "—",
    "вЂ“": "–",
    "в€’": "−",
    "в†’": "→",
    "В·": "·",
    "В°": "°",
}


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    original = text
    for bad, good in FIXES.items():
        text = text.replace(bad, good)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return sum(original.count(b) for b in FIXES)
    return 0


def main() -> int:
    total = 0
    for path in list(ROOT.joinpath("promethea").rglob("*.py")) + list(ROOT.joinpath("tests").rglob("*.py")):
        count = fix_file(path)
        if count:
            print(f"{path.relative_to(ROOT)}: {count}")
            total += count
    print("итого правок:", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
