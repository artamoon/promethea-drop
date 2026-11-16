"""Create PROMETHEA icon assets from the supplied vector logo."""
from __future__ import annotations

import io
import struct
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "promethea" / "assets"
SIZE = 1024


def master() -> Image.Image:
    svg = (ASSETS / "logo-source.svg").read_text(encoding="utf-8")
    # Keep the supplied geometry intact; only change its ink to the brand lime.
    svg = svg.replace('fill="#1C1C1C"', 'fill="#E4F222"').replace('stroke="black"', 'stroke="none"')
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        raise ValueError("Invalid source logo")
    canvas = QImage(SIZE, SIZE, QImage.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.transparent)
    p = QPainter(canvas)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#1C1C1C"))
    p.drawRoundedRect(QRectF(0, 0, SIZE, SIZE), 204, 204)
    # Breathing room preserves the logo's straight edges inside the rounded tile.
    renderer.render(p, QRectF(133, 133, 758, 758))
    p.end()
    from promethea.ui import pil_from_qimage
    return pil_from_qimage(canvas)


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    image = master()
    image.resize((512, 512), Image.Resampling.LANCZOS).save(ASSETS / "promethea.png")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    image.save(ASSETS / "promethea.ico", format="ICO", sizes=[(s, s) for s in sizes])
    chunks = []
    for tag, size in (("icp4",16),("icp5",32),("ic07",128),("ic08",256),("ic09",512),("ic10",1024)):
        buf = io.BytesIO()
        image.resize((size, size), Image.Resampling.LANCZOS).save(buf, format="PNG")
        data = buf.getvalue()
        chunks.append(tag.encode("ascii") + struct.pack(">I", len(data) + 8) + data)
    body = b"".join(chunks)
    (ASSETS / "promethea.icns").write_bytes(b"icns" + struct.pack(">I", len(body) + 8) + body)
    print("Created icon assets", flush=True)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    main()
