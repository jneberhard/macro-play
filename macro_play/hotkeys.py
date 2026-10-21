from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sys
from typing import Callable


HOTKEY_OPTIONS: dict[str, str | None] = {
    "Ctrl + F9": "<ctrl>+<f9>",
    "Ctrl + F10": "<ctrl>+<f10>",
    "Ctrl + F11": "<ctrl>+<f11>",
    "Ctrl + F12": "<ctrl>+<f12>",
    "Ctrl + Alt + P": "<ctrl>+<alt>+p",
    "Ctrl + Shift + P": "<ctrl>+<shift>+p",
    "F9": "<f9>",
    "F10": "<f10>",
    "F11": "<f11>",
    "F12": "<f12>",
    "Disabled": None,
}

DEFAULT_PLAY_HOTKEY = "Ctrl + F9"


def default_settings_path() -> Path:
    if os.name == "nt" and os.getenv("APPDATA"):
        return Path(os.environ["APPDATA"]) / "Macro Play" / "settings.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Macro Play" / "settings.json"
    return Path.home() / ".config" / "macro-play" / "settings.json"


@dataclass(slots=True)
class AppSettings:
    play_hotkey: str = DEFAULT_PLAY_HOTKEY

    @classmethod
    def load(cls, path: Path | None = None) -> "AppSettings":
        path = path or default_settings_path()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            hotkey = str(raw.get("play_hotkey", DEFAULT_PLAY_HOTKEY))
            return cls(play_hotkey=hotkey if hotkey in HOTKEY_OPTIONS else DEFAULT_PLAY_HOTKEY)
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self, path: Path | None = None) -> None:
        path = path or default_settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


class GlobalPlayHotkey:
    """Owns the app-wide playback shortcut listener."""

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self.listener = None
        self.selection = "Disabled"

    def configure(self, selection: str) -> None:
        self.stop()
        binding = HOTKEY_OPTIONS.get(selection)
        if selection not in HOTKEY_OPTIONS:
            raise ValueError(f"Unknown hotkey: {selection}")
        self.selection = selection
        if binding is None:
            return
        try:
            from pynput import keyboard
        except ImportError as exc:
            raise RuntimeError("pynput is required for global hotkeys.") from exc
        self.listener = keyboard.GlobalHotKeys({binding: self.callback})
        self.listener.start()

    def stop(self) -> None:
        if self.listener is not None:
            self.listener.stop()
            self.listener = None

