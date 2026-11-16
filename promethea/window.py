"""Светлое окно-карточка и просмотр изображения для всех редакторов."""
from __future__ import annotations

import sys

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizeGrip, QVBoxLayout,
                               QWidget)

from . import ui
from .brand import APP_NAME

IS_WIN = sys.platform == "win32"


class GlassWindow(QWidget):
    """Окно-карточка: белая поверхность, тонкая линия, мягкая тень.

    Имя класса сохранено, чтобы не трогать все окна инструментов, но стекла
    здесь больше нет: окно непрозрачное, фон не размывается.
    """

    RADIUS = 14
    SHADOW = 14
    TITLE_H = 34

    def __init__(self, title: str, parent=None, size=(760, 640)):
        super().__init__(parent)
        self.setWindowTitle(f"{title} — {APP_NAME}")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("surfaceRoot")
        self.setStyleSheet(ui.qss())
        self.resize(*size)
        self._drag: QPoint | None = None
        self._placed = False

        pad = self.SHADOW
        outer = QVBoxLayout(self)
        outer.setContentsMargins(pad + 18, pad + 8, pad + 18, pad + 14)
        outer.setSpacing(10)

        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("title")
        bar.addWidget(self.title_label)
        bar.addStretch(1)
        close = QPushButton("×")
        close.setObjectName("chrome")
        close.setToolTip("Close (Esc)")
        close.setFixedSize(26, 26)
        close.clicked.connect(self.close)
        bar.addWidget(close)
        outer.addLayout(bar)

        self.body = QVBoxLayout()
        self.body.setSpacing(12)
        outer.addLayout(self.body, 1)

        grip_row = QHBoxLayout()
        grip_row.addStretch(1)
        grip = QSizeGrip(self)
        grip.setFixedSize(14, 14)
        grip_row.addWidget(grip)
        grip_row.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(grip_row)

    # ---- window behaviour
    def present(self):
        """Показать окно по центру экрана под курсором."""
        from PySide6.QtGui import QCursor, QGuiApplication
        scr = (QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()).availableGeometry()
        self.resize(min(self.width(), scr.width() - 40), min(self.height(), scr.height() - 40))
        self.move(scr.center() - self.rect().center())
        self._placed = True
        self.show()
        if sys.platform == "darwin":
            from . import platform_mac
            platform_mac.activate()   # menu-bar apps aren't brought forward automatically
        self.raise_()
        self.activateWindow()

    def showEvent(self, e):
        # Диалоги без холста сжимаем по контенту: снизу не должно оставаться пустоты.
        if not self.findChildren(ImageView):
            self.layout().activate()
            hint = self.sizeHint().height()
            if 0 < hint < self.height():
                self.resize(self.width(), max(200, hint))
        super().showEvent(e)
        if not self._placed:
            scr = self.screen().availableGeometry()
            self.move(scr.center() - self.rect().center())
            self._placed = True

    def resizeEvent(self, e):
        super().resizeEvent(e)
        ui.apply_shape(self, ui.rounded_path(self._card_rect(), self.RADIUS))

    def _card_rect(self) -> QRectF:
        m = self.SHADOW
        return QRectF(self.rect()).adjusted(m, m, -m, -m)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < self.SHADOW + self.TITLE_H:
            handle = self.windowHandle()
            if handle is not None and handle.startSystemMove():
                return  # native move: snapping etc.
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        card = self._card_rect()
        ui.paint_shadow(p, card, self.RADIUS, spread=self.SHADOW, alpha=26, offset=8)
        p.setPen(QPen(ui.LINE, 1))
        p.setBrush(ui.SURFACE)
        p.drawRoundedRect(card, self.RADIUS, self.RADIUS)


class ImageView(QWidget):
    """Shows an image scaled to fit, with helpers to map between widget and image coords.
    Subclasses override `paint_overlay` and the mouse hooks."""

    changed = Signal()

    def __init__(self, image: QImage, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.setMouseTracking(True)
        self.set_image(image)

    def set_image(self, image: QImage):
        self.image = image
        self.pix = QPixmap.fromImage(image)
        self.update()

    # geometry
    def target_rect(self) -> QRectF:
        if self.image.isNull():
            return QRectF()
        avail = QRectF(self.rect()).adjusted(8, 8, -8, -8)
        s = min(avail.width() / self.image.width(), avail.height() / self.image.height())
        w, h = self.image.width() * s, self.image.height() * s
        return QRectF(avail.center().x() - w / 2, avail.center().y() - h / 2, w, h)

    def scale(self) -> float:
        t = self.target_rect()
        return t.width() / max(1, self.image.width())

    def to_image(self, pt):
        from PySide6.QtCore import QPointF
        t = self.target_rect()
        s = self.scale() or 1
        return QPointF((pt.x() - t.left()) / s, (pt.y() - t.top()) / s)

    def to_widget(self, pt):
        from PySide6.QtCore import QPointF
        t = self.target_rect()
        s = self.scale()
        return QPointF(t.left() + pt.x() * s, t.top() + pt.y() * s)

    def rect_to_widget(self, r: QRectF) -> QRectF:
        a = self.to_widget(r.topLeft())
        b = self.to_widget(r.bottomRight())
        return QRectF(a, b)

    def clamp_image(self, pt):
        from PySide6.QtCore import QPointF
        return QPointF(min(max(pt.x(), 0), self.image.width()), min(max(pt.y(), 0), self.image.height()))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.target_rect()
        # шахматка, чтобы прозрачность была видна на светлом фоне
        cell = 8
        p.save()
        p.setClipRect(t)
        p.fillRect(t, QColor("#FFFFFF"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#EFEBE1"))
        rows = int(t.height() // cell) + 1
        cols = int(t.width() // cell) + 1
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2:
                    p.drawRect(QRectF(t.left() + c * cell, t.top() + r * cell, cell, cell))
        p.restore()
        p.drawPixmap(t, self.pix, QRectF(self.pix.rect()))
        self.paint_overlay(p, t)

    def paint_overlay(self, p: QPainter, t: QRectF):
        pass
