"""Светлая тема PROMETHEA Drop: палитра, стили и простая отрисовка поверхностей.

Никакого стекла: ни размытия, ни преломления, ни снимков экрана под окном.
Поверхность — это белая карточка с тонкой линией и мягкой нейтральной тенью.
Акцент один: лайм #E4F222, и он используется только там, где означает действие
или выбор.
"""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

# ---------------------------------------------------------------- палитра
PAPER = QColor("#EEECE6")        # фон окна и страницы
SURFACE = QColor("#FFFFFF")      # карточка, меню, поле ввода
SURFACE_ALT = QColor("#F6F4ED")  # наведённое состояние, заголовок таблицы
INK = QColor("#34373A")          # основной текст
INK_SOFT = QColor(52, 55, 58, 176)
INK_MUTE = QColor(52, 55, 58, 128)
LINE = QColor(52, 55, 58, 34)    # тонкая линия: 13 % графита
LINE_STRONG = QColor(52, 55, 58, 64)
LIME = QColor("#E4F222")         # единственный акцент
LIME_HOVER = QColor("#EAF64A")
LIME_INK = QColor("#5F6B10")     # лайм как текст на светлом — затемнённый
OK = QColor("#3F6B3C")
ERR = QColor("#A8402F")
WARN = QColor("#8A5A12")

SPACE = 4  # всё кратно 4


def qcolor(value: str | QColor) -> QColor:
    return value if isinstance(value, QColor) else QColor(value)


# ---------------------------------------------------------------- геометрия
def rounded_path(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def paint_shadow(p: QPainter, rect: QRectF, radius: float, spread: int = 16,
                 alpha: int = 26, offset: int = 6) -> None:
    """Мягкая нейтральная тень: несколько расширяющихся скруглений с малым alpha."""
    p.save()
    p.setPen(Qt.NoPen)
    for step in range(spread, 0, -2):
        k = step / spread
        col = QColor(52, 55, 58, max(2, int(alpha * (1 - k) ** 2)))
        p.setBrush(col)
        r = rect.adjusted(-step, -step + offset, step, step + offset)
        p.drawRoundedRect(r, radius + step, radius + step)
    p.restore()


def paint_surface(p: QPainter, path: QPainterPath, fill: QColor = SURFACE,
                  border: QColor | None = LINE, width: float = 1.0) -> None:
    p.setPen(QPen(border, width) if border is not None else Qt.NoPen)
    p.setBrush(fill)
    p.drawPath(path)


def paint_card(p: QPainter, rect: QRectF, radius: float = 14, fill: QColor = SURFACE,
               border: QColor | None = LINE, shadow: bool = True) -> QPainterPath:
    if shadow:
        paint_shadow(p, rect, radius)
    path = rounded_path(rect, radius)
    paint_surface(p, path, fill, border)
    return path


def apply_shape(widget: QWidget, path: QPainterPath) -> None:
    """Обрезать окно по контуру: нужно там, где нет композитора (X11 без композита)."""
    widget.setMask(path.toFillPolygon().toPolygon())


def no_compositor() -> bool:
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.dwmapi.DwmIsCompositionEnabled.__call__())
    except Exception:
        return False


# ---------------------------------------------------------------- стили
# Структура как у Nothing: служебный текст — моно, крупное — засечками.
_QSS = """
* { color: #34373A; font-family: "@FONT@", monospace; font-size: 9.5pt; }
QWidget#surfaceRoot { background: transparent; }

QLabel#title { font-family: "@SERIF@", serif; font-size: 14pt; font-weight: 400;
               letter-spacing: 0.2px; }
QLabel#dim, QLabel.dim { color: rgba(52,55,58,0.62); font-size: 9pt; }
QLabel#section { color: rgba(52,55,58,0.52); font-size: 8pt; }
QLabel#big { font-family: "@SERIF@", serif; font-size: 19pt; font-weight: 400; }
QLabel#good { color: #3F6B3C; }
QLabel#warn { color: #8A5A12; }

QPushButton {
  background: #FFFFFF; border: 1px solid rgba(52,55,58,0.16);
  border-radius: 6px; padding: 6px 14px; min-height: 18px; font-size: 9pt;
}
QPushButton:hover { background: #F6F4ED; }
QPushButton:pressed { background: #EDE9DF; }
QPushButton:checked { background: #34373A; border: 1px solid #34373A; color: #FFFFFF; }
QPushButton:checked:hover { background: #4B4F52; }
QPushButton:focus { border: 1px solid #5F6B10; }
QPushButton:disabled { color: rgba(52,55,58,0.38); background: #F6F4ED; }

QPushButton#primary {
  background: #E4F222; border: 1px solid rgba(52,55,58,0.22);
  color: #34373A; padding: 7px 18px; border-radius: 6px; font-size: 9pt;
}
QPushButton#primary:hover { background: #EAF64A; }
QPushButton#primary:pressed { background: #D6E414; }
QPushButton#primary:focus { border: 2px solid #34373A; }

QPushButton#chrome {
  background: transparent; border: none; color: rgba(52,55,58,0.55);
  font-size: 12pt; padding: 2px 8px; border-radius: 6px;
}
QPushButton#chrome:hover { background: rgba(52,55,58,0.08); color: #34373A; }

QPushButton#swatch { border-radius: 11px; padding: 0; min-width: 22px; max-width: 22px;
                     min-height: 22px; max-height: 22px; }
QPushButton#swatch:checked { border: 2px solid #34373A; }

QSlider::groove:horizontal { height: 4px; background: #E2DED3; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #34373A; border-radius: 2px; }
QSlider::handle:horizontal {
  background: #FFFFFF; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px;
  border: 1px solid rgba(52,55,58,0.35);
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
  background: #FFFFFF; border: 1px solid rgba(52,55,58,0.18);
  border-radius: 8px; padding: 5px 8px;
  selection-background-color: #E4F222; selection-color: #34373A;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
  border: 1px solid #34373A;
}
QComboBox { padding-right: 30px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right;
  width: 28px; border: none; background: transparent; }
QComboBox::down-arrow { image: url("@CHEVRON@"); width: 12px; height: 12px; }
QComboBox QAbstractItemView { background: #FFFFFF; border: 1px solid rgba(52,55,58,0.18);
  selection-background-color: #F6F4ED; selection-color: #34373A; }

QFrame#card { background: #FFFFFF; border: 1px solid rgba(52,55,58,0.10); border-radius: 12px; }

QCheckBox::indicator {
  width: 16px; height: 16px; border-radius: 4px;
  border: 1px solid rgba(52,55,58,0.35); background: #FFFFFF;
}
QCheckBox::indicator:checked { background: #E4F222; border: 1px solid #34373A; image: url("@CHECK@"); }

QTableWidget { background: #FFFFFF; border: 1px solid rgba(52,55,58,0.12);
  border-radius: 10px; gridline-color: rgba(52,55,58,0.08); }
QHeaderView { background: transparent; }
QTableCornerButton::section { background: transparent; border: none; }
QHeaderView::section { background: #F6F4ED; border: none; padding: 6px 8px;
  color: rgba(52,55,58,0.66); font-weight: 500; }

QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: rgba(52,55,58,0.22); border-radius: 5px;
  min-height: 32px; }
QScrollBar::handle:vertical:hover { background: rgba(52,55,58,0.34); }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: rgba(52,55,58,0.22); border-radius: 5px;
  min-width: 32px; }

QToolTip { background: #34373A; color: #EEECE6; border: none; border-radius: 6px;
  padding: 6px 8px; font-size: 9.5pt; }
QMenu { background: #FFFFFF; border: 1px solid rgba(52,55,58,0.16); border-radius: 10px;
  padding: 6px; }
QMenu::item { padding: 7px 16px; border-radius: 6px; }
QMenu::item:selected { background: #F6F4ED; }
QMenu::separator { height: 1px; background: rgba(52,55,58,0.10); margin: 6px 8px; }
"""


def qss() -> str:
    from .util import ui_family
    return (_QSS.replace("@FONT@", ui_family(False)).replace("@SERIF@", ui_family(True))
            .replace("@CHECK@", (Path(__file__).resolve().parent / "assets" / "check.png").as_posix())
            .replace("@CHEVRON@", (Path(__file__).resolve().parent / "assets" / "chevron.png").as_posix()))


def __getattr__(name):  # ui.QSS
    if name == "QSS":
        return qss()
    raise AttributeError(name)

# ---------------------------------------------------------------- PIL <-> QImage
def qimage_from_pil(pil_img):
    """PIL.Image -> QImage (без копирования через файл)."""
    from PySide6.QtGui import QImage
    if pil_img.mode not in ("RGB", "RGBA"):
        pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", pil_img.mode)
    fmt = QImage.Format_RGBA8888 if pil_img.mode == "RGBA" else QImage.Format_RGB888
    img = QImage(data, pil_img.width, pil_img.height, pil_img.width * len(pil_img.mode), fmt)
    return img.copy()


def pil_from_qimage(img):
    """QImage -> PIL.Image в RGBA."""
    from PIL import Image
    from PySide6.QtGui import QImage
    img = img.convertToFormat(QImage.Format_RGBA8888)
    w, h = img.width(), img.height()
    buf = bytes(img.constBits())
    return Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", 0, 1)