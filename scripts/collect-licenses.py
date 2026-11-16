"""Collect available notices for the current Windows build environment.

This is an inventory aid, not proof of complete third-party compliance.
Run with the Python environment used to build the application.
"""
from importlib import metadata
from pathlib import Path
import shutil
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "third-party-licenses"
PACKAGES = ("pymupdf", "pillow-heif", "pillow", "numpy", "lxml",
            "python-docx", "psutil", "pywin32", "typing-extensions",
            "PySide6", "PySide6-Essentials", "PySide6-Addons", "shiboken6",
            "pyinstaller")

OUT.mkdir(exist_ok=True)
for name in PACKAGES:
    dist = metadata.distribution(name)
    dest = OUT / (name + "-" + dist.version)
    dest.mkdir(exist_ok=True)
    (dest / "METADATA.txt").write_text(dist.read_text("METADATA") or "", encoding="utf-8")
    for item in dist.files or ():
        parts = item.parts
        if not any(p.endswith(".dist-info") for p in parts):
            continue
        sub = parts[1:]
        if not sub or not (sub[0].lower() == "licenses" or sub[-1].lower().startswith(("license", "copying", "notice"))):
            continue
        src = Path(dist.locate_file(item))
        if src.is_file():
            target = dest.joinpath(*sub)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)

ffmpeg = OUT / "FFmpeg"
ffmpeg.mkdir(exist_ok=True)
for filename in ("LICENSE.txt", "BUILD.txt"):
    shutil.copy2(ROOT / "vendor" / "ffmpeg" / filename, ffmpeg / filename)

python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.exists():
    (OUT / "Python").mkdir(exist_ok=True)
    shutil.copy2(python_license, OUT / "Python" / "LICENSE.txt")
else:
    print("WARNING: Python LICENSE.txt not found at", python_license)

gnu = OUT / "GNU"
gnu.mkdir(exist_ok=True)
for name in ("gpl-2.0", "gpl-3.0", "lgpl-3.0", "agpl-3.0"):
    with urlopen("https://www.gnu.org/licenses/" + name + ".txt", timeout=30) as response:
        (gnu / (name + ".txt")).write_bytes(response.read())

print("Collected available license files in", OUT)
