"""Create a local source snapshot. This is not a full corresponding-source bundle."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
output = root / "dist" / "source" / "PROMETHEA-Drop-source-snapshot.zip"
files = [root / name for name in (
    "LICENSE", "NOTICE.md", "README.md", "requirements.txt", "run.py",
    "Promethea.spec", "install-mac.sh", ".gitignore",
    "docs/OPEN_SOURCE.md", "docs/LICENSE_AUDIT.md",
    "docs/INSTALLER_LICENSE_CHECK.md", "docs/build-environment.txt",
    "docs/menu.png", "docs/menu-hover.png", "docs/settings.png",
    "docs/welcome.png", "docs/tool-resize.png", "docs/false-positive.md",
    "vendor/ffmpeg/BUILD.txt", "vendor/ffmpeg/LICENSE.txt",
)]
for directory in ("promethea", "tests", "scripts", "installer", "packaging", "third-party-licenses"):
    files.extend(p for p in (root / directory).rglob("*") if p.is_file()
                 and "__pycache__" not in p.parts and p.suffix != ".pyc")
output.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
    for path in sorted(set(files)):
        if not path.is_file():
            raise FileNotFoundError(path)
        archive.write(path, "PROMETHEA-Drop/" + path.relative_to(root).as_posix())
print(output)
