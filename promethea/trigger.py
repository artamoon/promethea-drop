"""Watches for "left button held + mouse moved + Shift pressed" in a file manager, which
is what a Shift+drag of a file looks like. Polling global input state is simple, needs no
admin rights and can't stall the system the way a broken hook can.
Windows: GetAsyncKeyState. macOS: NSEvent.pressedMouseButtons / modifierFlags (no
Accessibility or Input Monitoring permission required)."""
from __future__ import annotations

import ctypes
import os
import sys

from PySide6.QtCore import QObject, QPoint, QTimer, Signal
from PySide6.QtGui import QCursor

VK_LBUTTON, VK_SHIFT, VK_ESCAPE = 0x01, 0x10, 0x1B
DRAG_THRESHOLD = 10   # px the mouse must travel with the button held
NO_DRAG_TIMEOUT = 50  # ticks (≈ 0.75 s) to wait for a file drag to enter before hiding

# Окна, из которых действительно тянут файлы: Проводник, рабочий стол и его слои.
# Shift+drag в Figma, Photoshop или тексте не должен открывать меню.
FILE_WINDOW_CLASSES = {"CabinetWClass", "ExploreWClass", "Progman", "WorkerW"}
FILE_PROCESSES = {"explorer.exe"}


def is_file_window(class_name: str, process_name: str = "") -> bool:
    """Можно ли считать перетаскивание файловым — по классу окна и процессу."""
    if class_name in FILE_WINDOW_CLASSES:
        return True
    return process_name.lower() in FILE_PROCESSES


class PrometheaWatcher(QObject):
    show_menu = Signal(QPoint)
    toggle_ring = Signal()
    hide_menu = Signal()

    def __init__(self, menu_visible, menu_got_drag, parent=None):
        super().__init__(parent)
        self.menu_visible = menu_visible
        self.menu_got_drag = menu_got_drag
        self.enabled = True
        self.vk = VK_SHIFT
        self.key_name = "shift"
        self._down_at: QPoint | None = None
        self._shift_was = False
        self._fired = False
        self._idle_ticks = 0
        self._shown_at = QPoint()
        self._user32 = ctypes.windll.user32 if sys.platform == "win32" else None
        self._mac = None
        if sys.platform == "darwin":
            from . import platform_mac
            self._mac = platform_mac if platform_mac.OK else None
        elif sys.platform.startswith("linux"):
            from . import platform_linux
            # same interface as platform_mac: left_button_down / key_down / escape_down
            self._mac = platform_linux if platform_linux.available() else None
        self.timer = QTimer(self, interval=15, timeout=self._tick)
        self._hide_timer = QTimer(self, singleShot=True, interval=120, timeout=self.hide_menu.emit)

    def set_key(self, name: str):
        self.key_name = name
        self.vk = {"shift": VK_SHIFT, "ctrl": 0x11, "alt": 0x12}.get(name, VK_SHIFT)

    def start(self):
        if self._user32 is not None or self._mac is not None:
            self.timer.start()

    def _down(self, vk: int) -> bool:
        return bool(self._user32.GetAsyncKeyState(vk) & 0x8000)

    def _window_class(self, hwnd) -> str:
        buf = ctypes.create_unicode_buffer(256)
        self._user32.GetClassNameW(hwnd, buf, 256)
        return buf.value

    def _process_name(self, hwnd) -> str:
        """Имя exe окна: нужно, когда класс незнакомый, а владелец всё равно Проводник."""
        pid = ctypes.c_ulong()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid.value)   # QUERY_LIMITED_INFORMATION
        if not handle:
            return ""
        try:
            size = ctypes.c_ulong(260)
            buf = ctypes.create_unicode_buffer(260)
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return ""
            return os.path.basename(buf.value)
        finally:
            kernel32.CloseHandle(handle)

    def _file_context(self) -> bool:
        """Тянут ли файл: Проводник или рабочий стол, а не холст Figma."""
        if self._user32 is None:
            return True   # macOS и Linux проверяют платформенные модули
        hwnd = self._user32.GetForegroundWindow()
        if not hwnd:
            return False
        return is_file_window(self._window_class(hwnd), self._process_name(hwnd))

    def _state(self) -> tuple[bool, bool, bool]:
        """(left button, trigger key, escape)"""
        if self._mac is not None:
            m = self._mac
            return m.left_button_down(), m.key_down(self.key_name), m.escape_down()
        return self._down(VK_LBUTTON), self._down(self.vk), self._down(VK_ESCAPE)

    def _tick(self):
        lbtn, shift, esc = self._state()
        pos = QCursor.pos()

        if self.menu_visible():
            if lbtn and not esc:
                self._hide_timer.stop()
            if not lbtn or esc:
                # drop happened (or was cancelled) – give the drop event a moment to land
                if not self._hide_timer.isActive():
                    self._hide_timer.start()
            elif shift and not self._shift_was and self.menu_got_drag():
                self.toggle_ring.emit()       # tap Shift again to flip Convert ⇄ Tools
            elif not self.menu_got_drag():
                # Close even if the pointer stops before a file drag enters.
                self._idle_ticks += 1
                if self._idle_ticks > NO_DRAG_TIMEOUT:
                    self.hide_menu.emit()
        else:
            self._hide_timer.stop()
            if lbtn:
                if self._down_at is None:
                    self._down_at = pos
                    self._fired = False
                moved = (pos - self._down_at).manhattanLength() >= DRAG_THRESHOLD
                if self.enabled and moved and shift and not self._fired and self._file_context():
                    self._fired = True
                    self._idle_ticks = 0
                    self._shown_at = pos
                    self.show_menu.emit(pos)
            else:
                self._down_at = None
                self._fired = False
        self._shift_was = shift
