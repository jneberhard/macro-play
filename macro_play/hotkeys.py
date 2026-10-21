from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sys
from typing import Callable, Iterable


DEFAULT_PLAY_HOTKEY = "Ctrl + F9"
MODIFIER_ORDER = ("Ctrl", "Alt", "Shift", "Cmd")
MODIFIER_BINDINGS = {"Ctrl": "<ctrl>", "Alt": "<alt>", "Shift": "<shift>", "Cmd": "<cmd>"}
MODIFIER_KEYSYMS = {
    "Control_L": "Ctrl", "Control_R": "Ctrl",
    "Alt_L": "Alt", "Alt_R": "Alt", "Option_L": "Alt", "Option_R": "Alt",
    "Shift_L": "Shift", "Shift_R": "Shift",
    "Meta_L": "Cmd", "Meta_R": "Cmd", "Super_L": "Cmd", "Super_R": "Cmd",
    "Win_L": "Cmd", "Win_R": "Cmd", "Command": "Cmd",
}
SPECIAL_KEYS = {
    "space": ("Space", "<space>"),
    "Return": ("Enter", "<enter>"),
    "Tab": ("Tab", "<tab>"),
    "BackSpace": ("Backspace", "<backspace>"),
    "Delete": ("Delete", "<delete>"),
    "Insert": ("Insert", "<insert>"),
    "Home": ("Home", "<home>"),
    "End": ("End", "<end>"),
    "Prior": ("Page Up", "<page_up>"),
    "Next": ("Page Down", "<page_down>"),
    "Left": ("Left", "<left>"),
    "Right": ("Right", "<right>"),
    "Up": ("Up", "<up>"),
    "Down": ("Down", "<down>"),
}


def hotkey_from_keypress(modifiers: Iterable[str], keysym: str) -> str:
    """Create a display shortcut from a Tk key event."""
    modifier_set = set(modifiers)
    active = [modifier for modifier in MODIFIER_ORDER if modifier in modifier_set]
    if keysym in MODIFIER_KEYSYMS:
        raise ValueError("Press a non-modifier key to finish the shortcut.")
    if keysym.upper().startswith("F") and keysym[1:].isdigit() and 1 <= int(keysym[1:]) <= 24:
        key = keysym.upper()
    elif len(keysym) == 1 and keysym.isalnum():
        if not active:
            raise ValueError("Add Ctrl, Alt, Shift, or Cmd to letters and numbers.")
        key = keysym.upper()
    elif keysym in SPECIAL_KEYS:
        if not active:
            raise ValueError("Add a modifier to this key.")
        key = SPECIAL_KEYS[keysym][0]
    else:
        raise ValueError("That key is not supported. Try a letter, number, function key, or navigation key.")
    result = " + ".join([*active, key])
    display_to_binding(result)  # Validate reserved and backend-supported combinations.
    return result


def display_to_binding(display: str) -> str | None:
    if display == "Disabled":
        return None
    parts = [part.strip() for part in display.split("+") if part.strip()]
    if not parts:
        raise ValueError("Choose a hotkey.")
    modifiers = [part for part in parts[:-1] if part in MODIFIER_BINDINGS]
    if len(modifiers) != len(parts) - 1 or len(set(modifiers)) != len(modifiers):
        raise ValueError("The hotkey contains an invalid modifier.")
    key = parts[-1]
    if key.upper().startswith("F") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        key_binding = f"<{key.lower()}>"
    elif len(key) == 1 and key.isalnum():
        if not modifiers:
            raise ValueError("Letters and numbers require a modifier.")
        key_binding = key.lower()
    else:
        reverse_special = {label: binding for label, binding in SPECIAL_KEYS.values()}
        if key not in reverse_special or not modifiers:
            raise ValueError("The hotkey contains an unsupported key.")
        key_binding = reverse_special[key]
    canonical = " + ".join([*[m for m in MODIFIER_ORDER if m in modifiers], key.upper() if len(key) == 1 else key])
    if canonical in {"F8", "Ctrl + F8"}:
        raise ValueError("F8 and Ctrl + F8 are reserved for emergency stop.")
    return "+".join([*(MODIFIER_BINDINGS[m] for m in MODIFIER_ORDER if m in modifiers), key_binding])


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
            display_to_binding(hotkey)
            return cls(play_hotkey=hotkey)
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
        binding = display_to_binding(selection)
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

