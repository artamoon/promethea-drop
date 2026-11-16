"""Что видит триггер в текущем активном окне (для проверки на живой системе)."""
from __future__ import annotations

import ctypes
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from promethea.trigger import is_file_window  # noqa: E402

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

hwnd = user32.GetForegroundWindow()
buf = ctypes.create_unicode_buffer(256)
user32.GetClassNameW(hwnd, buf, 256)
cls = buf.value

pid = ctypes.c_ulong()
user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
handle = kernel32.OpenProcess(0x1000, False, pid.value)
proc = ""
if handle:
    size = ctypes.c_ulong(260)
    pbuf = ctypes.create_unicode_buffer(260)
    if kernel32.QueryFullProcessImageNameW(handle, 0, pbuf, ctypes.byref(size)):
        proc = os.path.basename(pbuf.value)
    kernel32.CloseHandle(handle)

print(f"class={cls!r} process={proc!r} allowed={is_file_window(cls, proc)}")
