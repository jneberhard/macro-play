from __future__ import annotations

from dataclasses import dataclass
import ctypes
import ctypes.wintypes
import os
import subprocess
import sys
from typing import Any


@dataclass(slots=True)
class WindowState:
    title: str
    x: int
    y: int
    width: int
    height: int
    app: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "app": self.app,
        }


def foreground_window() -> WindowState | None:
    if sys.platform == "win32":
        return _windows_foreground()
    if sys.platform == "darwin":
        return _mac_foreground()
    return None


def restore_window(data: dict[str, Any]) -> bool:
    if sys.platform == "win32":
        return _windows_restore(data)
    if sys.platform == "darwin":
        return _mac_restore(data)
    return False


def _windows_foreground() -> WindowState | None:
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    length = user32.GetWindowTextLengthW(hwnd)
    if not length:
        return None
    title = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, title, length + 1)
    rect = ctypes.wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return WindowState(
        title=title.value,
        x=rect.left,
        y=rect.top,
        width=rect.right - rect.left,
        height=rect.bottom - rect.top,
    )


def _windows_restore(data: dict[str, Any]) -> bool:
    user32 = ctypes.windll.user32
    target = str(data.get("title", ""))
    if not target:
        return False
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

    def visit(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if not length:
            return True
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, length + 1)
        if title.value == target or target in title.value:
            matches.append(hwnd)
            return False
        return True

    user32.EnumWindows(callback_type(visit), 0)
    if not matches:
        return False
    hwnd = matches[0]
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetWindowPos(
        hwnd,
        0,
        int(data.get("x", 0)),
        int(data.get("y", 0)),
        max(100, int(data.get("width", 800))),
        max(100, int(data.get("height", 600))),
        0x0040,  # SWP_SHOWWINDOW
    )
    user32.SetForegroundWindow(hwnd)
    return True


def _osascript(source: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", source], capture_output=True, text=True, timeout=3, check=False
    )
    return result.stdout.strip()


def _mac_foreground() -> WindowState | None:
    script = '''tell application "System Events"
set p to first application process whose frontmost is true
set n to name of p
tell front window of p
set pos to position
set sz to size
return n & "|||" & (item 1 of pos) & "|||" & (item 2 of pos) & "|||" & (item 1 of sz) & "|||" & (item 2 of sz) & "|||" & name
end tell
end tell'''
    try:
        parts = _osascript(script).split("|||")
        if len(parts) != 6:
            return None
        return WindowState(parts[5], *(int(float(v)) for v in parts[1:5]), app=parts[0])
    except (ValueError, OSError, subprocess.SubprocessError):
        return None


def _mac_restore(data: dict[str, Any]) -> bool:
    app = str(data.get("app", "")).replace('"', '\\"')
    title = str(data.get("title", "")).replace('"', '\\"')
    if not app:
        return False
    script = f'''tell application "System Events"
tell application process "{app}"
set frontmost to true
set targetWindow to first window whose name contains "{title}"
set position of targetWindow to {{{int(data.get("x", 0))}, {int(data.get("y", 0))}}}
set size of targetWindow to {{{int(data.get("width", 800))}, {int(data.get("height", 600))}}}
end tell
end tell'''
    try:
        _osascript(script)
        return True
    except (OSError, subprocess.SubprocessError):
        return False

