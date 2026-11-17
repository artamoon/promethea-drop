"""macOS integration (only imported on darwin).

* Trigger: NSEvent.pressedMouseButtons / modifierFlags give the *global* mouse and
  modifier state, with no Accessibility or Input Monitoring permission needed.
* Start at login: a LaunchAgent plist.
"""
from __future__ import annotations

import os
import plistlib
import sys
from pathlib import Path

try:
    import AppKit  # pyobjc-framework-Cocoa
    import Quartz  # pyobjc-framework-Quartz
    OK = True
except Exception:  # pragma: no cover
    OK = False

# NSEventModifierFlags
SHIFT, CONTROL, OPTION, COMMAND = 1 << 17, 1 << 18, 1 << 19, 1 << 20
KEY_FLAGS = {"shift": SHIFT, "ctrl": CONTROL, "alt": OPTION}


# ---------------------------------------------------------------- input state
def left_button_down() -> bool:
    return bool(OK and AppKit.NSEvent.pressedMouseButtons() & 1)


def key_down(name: str) -> bool:
    return bool(OK and AppKit.NSEvent.modifierFlags() & KEY_FLAGS.get(name, SHIFT))


def escape_down() -> bool:
    if not OK:
        return False
    try:
        return bool(Quartz.CGEventSourceKeyState(Quartz.kCGEventSourceStateCombinedSessionState, 53))
    except Exception:
        return False


# ---------------------------------------------------------------- app behaviour
def become_accessory():
    """Menu-bar app: no Dock icon (the bundle also sets LSUIElement)."""
    if OK:
        AppKit.NSApplication.sharedApplication().setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory)


def activate():
    """Bring our windows to the front (accessory apps aren't activated automatically)."""
    if OK:
        AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)


def window_number(widget) -> int:
    """CGWindowID of a Qt top-level widget (winId() is an NSView*)."""
    if not OK:
        return 0
    try:
        import objc
        view = objc.objc_object(c_void_p=int(widget.winId()))
        win = view.window()
        return int(win.windowNumber()) if win is not None else 0
    except Exception:
        return 0


# ---------------------------------------------------------------- start at login
AGENT = Path.home() / "Library" / "LaunchAgents" / "com.promethea.app.plist"


def _program() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--quiet"]
    return [sys.executable, "-m", "promethea", "--quiet"]


def autostart_enabled() -> bool:
    return AGENT.exists()


def set_autostart(on: bool):
    if on:
        AGENT.parent.mkdir(parents=True, exist_ok=True)
        config = {"Label": "com.promethea.app", "ProgramArguments": _program(),
                  "RunAtLoad": True, "ProcessType": "Interactive"}
        if not getattr(sys, "frozen", False):
            # launchd does not start in the repository directory, so Python would
            # otherwise be unable to find the promethea package.
            config["WorkingDirectory"] = str(Path(__file__).resolve().parent.parent)
        with open(AGENT, "wb") as f:
            plistlib.dump(config, f)
    elif AGENT.exists():
        AGENT.unlink()


# ---------------------------------------------------------------- drag pasteboard
def drag_files() -> list[str]:
    """Files being dragged right now, read from the system drag pasteboard.
    macOS only tells a window about a drag once the cursor moves over it; reading the pasteboard
    lets the menu show its slices the moment it opens, even if the mouse is held perfectly still."""
    try:
        import AppKit
        from AppKit import NSPasteboard, NSURL
        name = getattr(AppKit, "NSPasteboardNameDrag", None) or getattr(AppKit, "NSDragPboard", "Apple CFPasteboard drag")
        pb = NSPasteboard.pasteboardWithName_(name)
        urls = pb.readObjectsForClasses_options_([NSURL], {"NSPasteboardURLReadingFileURLsOnlyKey": True}) or []
        out = [str(u.path()) for u in urls if u.isFileURL()]
        return [p for p in out if os.path.exists(p)]
    except Exception:
        return []
