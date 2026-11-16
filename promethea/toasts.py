"""Уведомления в правом нижнем углу: светлые карточки со стопкой.

Пока идёт работа — карточка со спиннером, затем результат: миниатюра, что
изменилось («2,4 МБ → 610 КБ · на 75 % меньше») и действия Open · Show · Undo.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import (QEasingCurve, QFile, QRect, QRectF, Qt, QTimer, QUrl,
                            QVariantAnimation, Signal)
from PySide6.QtGui import (QColor, QCursor, QDesktopServices, QFont, QFontMetrics,
                           QGuiApplication, QPainter, QPen)
from PySide6.QtWidgets import QWidget

from . import ui
from .util import ui_family

W, H = 380, 96
GAP = 10
MARGIN = 18
PAD = 10          # поле под тень внутри окна


def reveal(path: str | Path):
    path = str(path)
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", path])
    else:
        from . import platform_linux
        if not platform_linux.reveal(path):
            subprocess.Popen(["xdg-open", str(Path(path).parent)])


def open_file(path: str | Path):
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def trash(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """Move results to the trash, preserving files when the operation fails."""
    moved, failed = [], []
    for path in paths:
        path = Path(path)
        if path.is_file() and QFile.moveToTrash(str(path)):
            moved.append(path)
        else:
            failed.append(path)
    return moved, failed


class ToastCard(QWidget):
    closed = Signal(object)

    def __init__(self, stack: "ToastStack"):
        super().__init__(None)
        self.stack = stack
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint |
                            Qt.WindowDoesNotAcceptFocus | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.resize(W, H)
        self.state = "working"     # working | done | error | info
        self.title = ""
        self.detail = ""
        self.good = ""
        self.result = None
        self.spin = 0.0
        self.hover_btn = -1
        self.buttons: list[tuple[str, QRectF]] = []
        self._fade = 0.0
        self.fade = QVariantAnimation(self, startValue=0.0, endValue=1.0, duration=180,
                                      easingCurve=QEasingCurve.OutCubic)
        self.fade.valueChanged.connect(self._set_fade)
        self.spinner = QTimer(self, interval=16, timeout=self._spin)
        self.life = QTimer(self, singleShot=True, timeout=self.dismiss)

    # ------------------------------------------------------------ state
    def working(self, title: str, detail: str = ""):
        self.state, self.title, self.detail = "working", title, detail
        self.spinner.start()
        self.update()

    def done(self, r):
        self.spinner.stop()
        self.state, self.result = "done", r
        self.title, self.detail, self.good = r.title, r.detail, r.good
        self.life.start(6500)
        self.update()

    def error(self, title: str, detail: str):
        self.spinner.stop()
        self.state, self.title, self.detail = "error", title, detail
        self.life.start(9000)
        self.update()

    def info(self, title: str, detail: str, ms: int = 4500):
        self.spinner.stop()
        self.state, self.title, self.detail = "info", title, detail
        self.life.start(ms)
        self.update()

    def _spin(self):
        self.spin = (self.spin + 7) % 360
        self.update()

    def _set_fade(self, v):
        self._fade = float(v)
        self.setWindowOpacity(self._fade)
        self.update()

    def appear(self, rect: QRect):
        self.setGeometry(rect)
        ui.apply_shape(self, ui.rounded_path(QRectF(0, 0, W, H), 16))
        self.setWindowOpacity(0.0)
        self.show()
        self.fade.start()

    def relocate(self, rect: QRect):
        if rect != self.geometry():
            self.setGeometry(rect)

    def dismiss(self):
        self.spinner.stop()
        self.life.stop()
        self.hide()
        self.closed.emit(self)
        self.deleteLater()

    # ------------------------------------------------------------ input
    def enterEvent(self, e):
        self.life.stop()

    def leaveEvent(self, e):
        self.hover_btn = -1
        if self.state in ("done", "info"):
            self.life.start(2500)
        elif self.state == "error":
            self.life.start(4000)
        self.update()

    def mouseMoveEvent(self, e):
        hb = -1
        for i, (_, r) in enumerate(self.buttons):
            if r.contains(e.position()):
                hb = i
        if hb != self.hover_btn:
            self.hover_btn = hb
            self.setCursor(Qt.PointingHandCursor if hb >= 0 else Qt.ArrowCursor)
            self.update()

    def mouseReleaseEvent(self, e):
        if QRectF(W - 38, 12, 24, 24).contains(e.position()):
            self.dismiss()
            return
        for name, r in self.buttons:
            if r.contains(e.position()):
                self._act(name)
                return
        if self.state == "done" and self.result and self.result.outs:
            reveal(self.result.outs[0])
            self.dismiss()

    def _act(self, name: str):
        r = self.result
        if not r:
            return
        if name == "Open":
            open_file(r.outs[0])
            self.dismiss()
        elif name == "Show":
            reveal(r.outs[0])
            self.dismiss()
        elif name == "Undo":
            moved, failed = trash(r.outs)
            bin_name = "Recycle Bin" if sys.platform == "win32" else "Trash"
            if failed:
                # Keep the remaining results available for another attempt.
                r.outs = failed
                self.title = "Undo incomplete"
                self.detail = f"{len(failed)} file(s) could not be moved to {bin_name}"
                self.good = ""
                self.life.start(9000)
                self.update()
            else:
                self.result = None
                self.good = ""
                n = len(moved)
                self.info("Undone", f"Moved {n} file{'s' if n != 1 else ''} to the {bin_name}", 2500)

    # ------------------------------------------------------------ paint
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        card = QRectF(self.rect()).adjusted(PAD, 2, -PAD, -PAD - 2)
        ui.paint_shadow(p, card, 14, spread=10, alpha=24, offset=6)
        p.setPen(QPen(ui.LINE, 1))
        p.setBrush(ui.SURFACE)
        p.drawRoundedRect(card, 14, 14)

        err = self.state == "error"
        # A quiet status line across the top keeps the card contents aligned.
        bar = QColor(ui.OK) if self.state == "done" else (ui.ERR if err else ui.INK_MUTE)
        p.setPen(Qt.NoPen)
        p.setBrush(bar)
        p.drawRoundedRect(QRectF(card.left() + 24, card.top() + 1,
                                 card.width() - 48, 3), 1.5, 1.5)

        x = card.left() + 18
        title_top = card.top() + 12

        if self.state == "working":
            # A short travelling line shows activity without a status icon.
            track = QRectF(x, card.bottom() - 13, 60, 2)
            p.setPen(Qt.NoPen)
            p.setBrush(ui.LINE)
            p.drawRoundedRect(track, 1, 1)
            p.setBrush(ui.INK_SOFT)
            offset = (self.spin / 360.0) * (track.width() - 18)
            p.drawRoundedRect(QRectF(track.left() + offset, track.top(), 18, 2), 1, 1)

        tw = card.right() - 34 - x

        f = QFont(ui_family(True))
        f.setPixelSize(16)
        f.setWeight(QFont.Normal)
        p.setFont(f)
        fm = QFontMetrics(f)
        title = fm.elidedText(self.title, Qt.ElideRight, int(tw) - (70 if self.good else 0))
        p.setPen(ui.INK)
        p.drawText(QRectF(x, title_top, tw, 20), Qt.AlignLeft | Qt.AlignVCenter, title)

        # единственное число, которое важно: «на 75 % меньше»
        if self.good:
            gx = x + fm.horizontalAdvance(title) + 8
            f2 = QFont(ui_family(False))
            f2.setPixelSize(10)
            f2.setWeight(QFont.DemiBold)
            fm2 = QFontMetrics(f2)
            gw = fm2.horizontalAdvance(self.good) + 14
            chip = QRectF(gx, title_top + 1, min(gw, card.right() - 34 - gx), 18)
            if chip.width() > 20:
                p.setPen(Qt.NoPen)
                p.setBrush(ui.LIME)
                p.drawRoundedRect(chip, 9, 9)
                p.setFont(f2)
                p.setPen(ui.INK)
                p.drawText(chip, Qt.AlignCenter, self.good)

        f = QFont(ui_family(False))
        f.setPixelSize(11)
        f.setWeight(QFont.Normal)
        p.setFont(f)
        p.setPen(ui.INK_SOFT)
        detail_width = int(card.right() - 18 - x)
        detail = QFontMetrics(f).elidedText(self.detail, Qt.ElideRight, detail_width)
        p.drawText(QRectF(x, title_top + 22, detail_width, 18), Qt.AlignLeft | Qt.AlignTop, detail)

        f.setPixelSize(12)
        p.setFont(f)
        p.setPen(ui.INK_MUTE)
        p.drawText(QRectF(card.right() - 32, card.top() + 8, 22, 22), Qt.AlignCenter, "×")

        # действия: светлые кнопки, выбранная — белая с тёмной линией
        self.buttons = []
        if self.state == "done" and self.result and self.result.outs:
            names = ["Open", "Show", "Undo"]
            labels = {"Open": "Open", "Show": "Show", "Undo": "Undo"}
            f.setPixelSize(11)
            f.setWeight(QFont.DemiBold)
            p.setFont(f)
            bx = card.left() + 18
            gap = 6
            bw = (card.width() - 36 - gap * 2) / len(names)
            for i, nme in enumerate(names):
                br = QRectF(bx, card.bottom() - 28, bw, 22)
                self.buttons.append((nme, br))
                p.setPen(QPen(ui.LINE_STRONG if self.hover_btn == i else ui.LINE, 1))
                p.setBrush(ui.SURFACE if self.hover_btn == i else ui.SURFACE_ALT)
                p.drawRoundedRect(br, 6, 6)
                p.setPen(ui.INK)
                p.drawText(br, Qt.AlignCenter, labels[nme])
                bx += bw + gap


class ToastStack:
    """Owns the cards and keeps them stacked bottom-right of the active screen."""

    def __init__(self):
        self.cards: list[ToastCard] = []

    def _screen_rect(self) -> QRect:
        scr = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        return scr.availableGeometry()

    def _slot(self, i: int) -> QRect:
        g = self._screen_rect()
        x = g.right() - W - MARGIN
        y = g.bottom() - MARGIN - H - i * (H + GAP)
        return QRect(x, y, W, H)

    def new(self) -> ToastCard:
        c = ToastCard(self)
        c.closed.connect(self._closed)
        while len(self.cards) >= 4:
            self.cards[0].dismiss()
        self.cards.append(c)
        c.appear(self._slot(len(self.cards) - 1))
        return c

    def _closed(self, card):
        if card in self.cards:
            self.cards.remove(card)
        for i, c in enumerate(self.cards):
            c.relocate(self._slot(i))

    # conveniences
    def info(self, title: str, detail: str, ms: int = 4500) -> ToastCard:
        c = self.new()
        c.info(title, detail, ms)
        return c

    def error(self, title: str, detail: str) -> ToastCard:
        c = self.new()
        c.error(title, detail)
        return c
