"""Радиальное меню, которое открывается под курсором во время Shift+drag.

Рисуется без стекла: белые капсулы с тонкой линией на светлом фоне, мягкая
тень под всем меню и один акцент — лайм на выбранном секторе. Никаких снимков
экрана, размытия и преломления.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import (QEasingCurve, QPoint, QPointF, QRectF, Qt, QTimer,
                            QVariantAnimation, Signal)
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QPainter,
                           QPainterPath, QPen)
from PySide6.QtWidgets import QWidget

from . import ui
from .util import resolve_shortcuts, ui_family, ui_mono, ui_serif


@dataclass
class Item:
    label: str
    glyph: str = ""      # оставлено для совместимости; иконки в меню не рисуются
    run: Callable[[list[str]], None] | None = None
    key: str = ""
    hint: str = ""


def blend(a: QColor, b: QColor, t: float) -> QColor:
    """Плавный переход цвета: заливка наливается вместе с выездом, без скачка."""
    t = max(0.0, min(1.0, t))
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


SIZE = 400          # сторона окна: место под тень и «поп» при наведении
R_OUT = 170         # внешний радиус секторов
R_IN = 68           # внутренний радиус
R_HUB = 58          # радиус центра
CORNER = 0          # скругление углов сектора: 0 — чистый сектор без перекрытий
HOVER_MS = 190      # длительность выезда лепестка
PUSH = 7.0          # насколько лепесток отходит от центра, px


def polar(c: QPointF, angle_deg: float, radius: float) -> QPointF:
    a = math.radians(angle_deg)
    return QPointF(c.x() + radius * math.cos(a), c.y() - radius * math.sin(a))


def sector_path(c: QPointF, r0: float, r1: float, a0: float, a1: float) -> QPainterPath:
    """Кольцевой сектор между углами a0..a1 (градусы, 0 = 3 часа, против часовой)."""
    path = QPainterPath()
    outer = QRectF(c.x() - r1, c.y() - r1, 2 * r1, 2 * r1)
    inner = QRectF(c.x() - r0, c.y() - r0, 2 * r0, 2 * r0)
    path.arcMoveTo(outer, a0)
    path.arcTo(outer, a0, a1 - a0)
    path.arcTo(inner, a1, -(a1 - a0))
    path.closeSubpath()
    return path


def angles(n: int, i: int) -> tuple[float, float]:
    span = 360.0 / n
    start = 90 + span / 2 - (i + 1) * span   # первый сектор по центру сверху, дальше по часовой
    # Общие радиальные границы дают шов одинаковой толщины по всей длине.
    return start, start + span


class RadialMenu(QWidget):
    activated = Signal(object, list)     # Item, paths
    dismissed = Signal()

    def __init__(self, build_rings: Callable[[list[str]], dict[str, list[Item]]],
                 describe: Callable[[list[str]], str]):
        super().__init__(None)
        self.build_rings = build_rings
        self.describe = describe
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint |
                            Qt.WindowDoesNotAcceptFocus | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.resize(SIZE, SIZE)

        self.paths: list[str] = []
        self.rings: dict[str, list[Item]] = {}
        self.ring_names: list[str] = []
        self.ring_idx = 0
        self.hover = -1          # индекс сектора, -2 = центр, -1 = ничего
        self.cursor_pos = QPointF(SIZE / 2, SIZE / 2)
        self.hub_text = ""
        self.got_drag = False
        self.click_mode = False  # открыто из трея/меню, а не перетаскиванием
        self._t = 1.0            # появление 0..1
        self._swap = 1.0         # смена кольца 0..1
        self.spring: list[float] = []      # текущее смещение 0..1
        self._from: list[float] = []       # с чего началась анимация
        self._to: list[float] = []         # к чему идёт
        self._t0: list[float] = []         # время старта, секунды

        self.anim = QVariantAnimation(self, startValue=0.0, endValue=1.0, duration=170,
                                      easingCurve=QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._set_t)
        self.swap_anim = QVariantAnimation(self, startValue=0.0, endValue=1.0, duration=200,
                                           easingCurve=QEasingCurve.OutCubic)
        self.swap_anim.valueChanged.connect(self._set_swap)
        self.frame = QTimer(self, interval=16, timeout=self._tick)   # 60 fps пружины

    # ------------------------------------------------------------ show / hide
    def popup(self, pos: QPoint | None = None, paths: list[str] | None = None):
        pos = pos or QCursor.pos()
        tl = pos - QPoint(SIZE // 2, SIZE // 2)
        scr = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        g = scr.geometry()
        tl.setX(min(max(tl.x(), g.left()), g.right() - SIZE))
        tl.setY(min(max(tl.y(), g.top()), g.bottom() - SIZE))
        self.move(tl)
        self.hover = -1
        self.got_drag = False
        self.click_mode = paths is not None
        if paths is not None:
            self._load(paths)
        else:
            self.paths, self.rings, self.ring_names = [], {}, []
            self.hub_text = "Drop a file"
        self._t = 0.0
        self.show()
        self.raise_()
        self.anim.start()
        self.frame.start()
        if self.click_mode:
            # ведёт себя как popup: клик мимо закрывает
            QTimer.singleShot(0, self.grabMouse)

    def close_menu(self):
        if self.isVisible():
            self.hide()
            self.frame.stop()
            self.dismissed.emit()

    def hideEvent(self, e):
        self.frame.stop()
        if QWidget.mouseGrabber() is self:
            self.releaseMouse()
        super().hideEvent(e)

    def _load(self, paths: list[str]):
        paths = resolve_shortcuts(paths)
        self.paths = paths
        self.rings = {k: v for k, v in self.build_rings(paths).items() if v}
        self.ring_names = list(self.rings)
        self.ring_idx = 0
        self.hub_text = self.describe(paths)
        self.spring = [0.0] * len(self.items)
        self._from = [0.0] * len(self.items)
        self._to = [0.0] * len(self.items)
        self._t0 = [0.0] * len(self.items)
        self.update()

    def next_ring(self):
        if len(self.ring_names) > 1:
            self.ring_idx = (self.ring_idx + 1) % len(self.ring_names)
            self.hover = -1
            self.spring = [0.0] * len(self.items)
            self._from = [0.0] * len(self.items)
            self._to = [0.0] * len(self.items)
            self._t0 = [0.0] * len(self.items)
            self._swap = 0.0
            self.swap_anim.start()
            self.update()

    def _set_t(self, v):
        self._t = float(v)
        self.update()

    def _set_swap(self, v):
        self._swap = float(v)
        self.update()

    def _retarget(self):
        """Пересчитать цели анимации: двигается только наведённый лепесток.

        Старт берётся от текущего значения, поэтому быстрый переход между
        лепестками продолжает движение с того же места — без рывка.
        """
        now = time.monotonic()
        n = len(self.spring)
        if n == 0:
            return
        for i in range(n):
            target = 1.0 if i == self.hover else 0.0
            if abs(self._to[i] - target) < 1e-6:
                continue
            self._from[i] = self.spring[i]
            self._to[i] = target
            self._t0[i] = now
        if not self.frame.isActive():
            self.frame.start()

    def _tick(self):
        now = time.monotonic()
        moving = False
        settled = True
        for i in range(len(self.spring)):
            target = self._to[i]
            if abs(self.spring[i] - target) < 1e-4:
                self.spring[i] = target
                continue
            p = (now - self._t0[i]) / (HOVER_MS / 1000.0)
            if p >= 1.0:
                self.spring[i] = target
                continue
            # smoothstep: мягкий старт и мягкое торможение, без перелёта
            k = p * p * (3.0 - 2.0 * p)
            self.spring[i] = self._from[i] + (target - self._from[i]) * k
            moving = True
            settled = False
        if moving:
            self.update()
        if settled:
            self.frame.stop()

    # ------------------------------------------------------------ geometry
    @property
    def items(self) -> list[Item]:
        if not self.ring_names:
            return []
        return self.rings[self.ring_names[self.ring_idx]]

    def _angles(self, n: int, i: int) -> tuple[float, float]:
        return angles(n, i)

    @staticmethod
    def _center() -> QPointF:
        return QPointF(SIZE / 2, SIZE / 2)

    def _petal_path(self, i: int, n: int, push: float = 0.0) -> QPainterPath:
        """Сектор, сжатый на радиус скругления: обводка с round join вернёт углы."""
        a0, a1 = angles(n, i)
        c = float(CORNER)
        r0 = R_IN + c + push
        r1 = R_OUT - c + push
        if c <= 0:
            return sector_path(self._center(), r0, r1, a0, a1)
        r_mid = (r0 + r1) / 2
        inset = math.degrees(math.asin(min(0.9, c / max(1.0, r_mid))))
        return sector_path(self._center(), r0, r1, a0 + inset, a1 - inset)

    def hit(self, pos: QPointF) -> int:
        c = self._center()
        dx, dy = pos.x() - c.x(), c.y() - pos.y()
        d = math.hypot(dx, dy)
        if d <= R_HUB + 4:
            return -2
        if d > R_OUT + 24 or not self.items:
            return -1
        ang = math.degrees(math.atan2(dy, dx)) % 360
        n = len(self.items)
        rel = (90 + 180.0 / n - ang) % 360
        return int(rel // (360.0 / n)) % n

    def _set_hover(self, h: int, pos: QPointF | None = None):
        if pos is not None:
            self.cursor_pos = QPointF(pos)
        if h != self.hover:
            self.hover = h
            self._retarget()
        self.update()

    # ------------------------------------------------------------ drag & drop
    @staticmethod
    def _local_paths(md) -> list[str]:
        if not md.hasUrls():
            return []
        return [u.toLocalFile() for u in md.urls() if u.isLocalFile() and u.toLocalFile()]

    def dragEnterEvent(self, e):
        paths = self._local_paths(e.mimeData())
        if not paths:
            e.ignore()
            return
        self.got_drag = True
        if resolve_shortcuts(paths) != self.paths:
            self._load(paths)
        e.setDropAction(Qt.CopyAction)  # Shift(=move) не должен удалять исходник
        e.accept()

    def dragMoveEvent(self, e):
        self._set_hover(self.hit(e.position()), e.position())
        e.setDropAction(Qt.CopyAction)
        e.accept()

    def dragLeaveEvent(self, e):
        self._set_hover(-1)

    def dropEvent(self, e):
        idx = self.hit(e.position())
        items = self.items
        if 0 <= idx < len(items):
            e.setDropAction(Qt.CopyAction)
            e.accept()
            item, paths = items[idx], list(self.paths)
            self.hide()
            QTimer.singleShot(0, lambda: self.activated.emit(item, paths))
        else:
            e.ignore()
            self.close_menu()

    # ------------------------------------------------------------ click mode
    def mouseMoveEvent(self, e):
        if self.click_mode:
            self._set_hover(self.hit(e.position()), e.position())

    def mouseReleaseEvent(self, e):
        if not self.click_mode:
            return
        if e.button() == Qt.RightButton:
            self.close_menu()
            return
        idx = self.hit(e.position())
        if idx == -2:
            self.next_ring()
        elif 0 <= idx < len(self.items):
            item, paths = self.items[idx], list(self.paths)
            self.hide()
            QTimer.singleShot(0, lambda: self.activated.emit(item, paths))
        else:
            self.close_menu()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_menu()
        elif e.key() in (Qt.Key_Tab, Qt.Key_Shift):
            self.next_ring()

    def leaveEvent(self, e):
        if self.click_mode:
            self._set_hover(-1)

    # ------------------------------------------------------------ painting
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        c = self._center()
        t = max(0.0, min(1.0, self._t))
        p.setOpacity(t)
        p.translate(c)
        s = 0.94 + 0.06 * t
        p.scale(s, s)
        p.translate(-c)

        items = self.items
        n = len(items)

        # сектора: соседние делят одну границу, поэтому заливка + тонкая линия
        for i in range(n):
            h = self.spring[i] if i < len(self.spring) else 0.0
            path = self._petal_path(i, n, push=PUSH * h)
            fill = blend(ui.SURFACE, ui.LIME, h)
            border = blend(ui.LINE, ui.LINE_STRONG, h)
            p.setPen(QPen(border, 1))
            p.setBrush(fill)
            p.drawPath(path)

        # подписи
        for i, it in enumerate(items):
            h = self.spring[i] if i < len(self.spring) else 0.0
            self._petal_label(p, it, i, n, h)

        self._paint_hub(p, c)

    def _paint_hub(self, p: QPainter, c: QPointF):
        hovered = self.hover
        items = self.items
        path = QPainterPath()
        path.addEllipse(c, R_HUB, R_HUB)
        p.save()
        p.translate(0, 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(52, 55, 58, 16))
        p.drawPath(path)
        p.restore()
        p.setPen(QPen(ui.LINE_STRONG, 1))
        p.setBrush(ui.SURFACE)
        p.drawPath(path)

        unsupported = not items and bool(self.paths)
        if unsupported:
            ext = Path(self.paths[0]).suffix.lower()
            top = "Not supported"
            sub = ext if ext else "this file"
        elif 0 <= hovered < len(items):
            top = items[hovered].label
            sub = items[hovered].hint or ""
        else:
            top = self.hub_text
            if len(self.ring_names) > 1:
                sub = f"{self.ring_names[self.ring_idx]} · Shift"
            elif self.ring_names:
                sub = self.ring_names[self.ring_idx]
            else:
                sub = ""

        f = ui_serif(17 if unsupported else 22)
        p.setFont(f)
        p.setPen(ui.INK)
        if unsupported:
            # в круге мало места: сообщение переносится на две строки, а не вылезает за край
            p.drawText(QRectF(c.x() - R_HUB + 10, c.y() - 30, 2 * R_HUB - 20, 44),
                       Qt.AlignCenter | Qt.TextWordWrap, top)
        else:
            fm = QFontMetrics(f)
            p.drawText(QRectF(c.x() - R_HUB + 4, c.y() - 24, 2 * R_HUB - 8, 26),
                       Qt.AlignCenter, fm.elidedText(top, Qt.ElideRight, int(2 * R_HUB - 8)))

        if sub:
            f2 = ui_mono(8)
            f2.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
            p.setFont(f2)
            p.setPen(ui.INK_MUTE)
            p.drawText(QRectF(c.x() - R_HUB + 6, c.y() + 14 if unsupported else c.y() + 4,
                              2 * R_HUB - 12, 18),
                       Qt.AlignHCenter | Qt.AlignTop, sub.upper())

    def _petal_label(self, p: QPainter, it: Item, i: int, n: int, h: float):
        a0, a1 = angles(n, i)
        mid = math.radians((a0 + a1) / 2)
        span = 360.0 / n
        r = (R_IN + R_OUT) / 2 + PUSH * h
        pt = QPointF(self._center().x() + r * math.cos(mid),
                     self._center().y() - r * math.sin(mid))
        p.save()
        p.setOpacity(p.opacity() * (0.3 + 0.7 * self._swap))

        name_font = ui_mono(11)
        name_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        hint_font = ui_mono(9)

        name_fm = QFontMetrics(name_font)
        hint_fm = QFontMetrics(hint_font)
        chord = 2 * r * math.sin(math.radians(max(1.0, span) / 2))
        max_w = max(52.0, chord * 0.88)

        name = name_fm.elidedText(it.label.upper(), Qt.ElideRight, int(max_w))
        hint = hint_fm.elidedText(it.hint, Qt.ElideRight, int(max_w)) if (it.hint and max_w >= 74) else ""

        p.setPen(blend(ui.INK, QColor("#1C1C1C"), h))
        p.setFont(name_font)
        if hint:
            p.drawText(QRectF(pt.x() - max_w / 2, pt.y() - 13, max_w, 18), Qt.AlignCenter, name)
            p.setFont(hint_font)
            p.setPen(blend(ui.INK_MUTE, QColor(28, 28, 28, 200), h))
            p.drawText(QRectF(pt.x() - max_w / 2, pt.y() + 4, max_w, 16), Qt.AlignCenter, hint)
        else:
            p.drawText(QRectF(pt.x() - max_w / 2, pt.y() - 10, max_w, 20), Qt.AlignCenter, name)
        p.restore()
