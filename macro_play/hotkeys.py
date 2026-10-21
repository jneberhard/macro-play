from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import sys
from typing import Callable, Iterable
import uuid


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
class MacroHotkeyBinding:
    hotkey: str
    macro_path: str
    macro_name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "MacroHotkeyBinding":
        hotkey = str(raw.get("hotkey", ""))
        display_to_binding(hotkey)
        macro_path = str(raw.get("macro_path", "")).strip()
        if not macro_path:
            raise ValueError("A macro hotkey must reference a saved macro file.")
        return cls(
            hotkey=hotkey,
            macro_path=macro_path,
            macro_name=str(raw.get("macro_name", "Saved macro")),
            id=str(raw.get("id") or uuid.uuid4().hex[:10]),
        )


@dataclass(slots=True)
class AppSettings:
    play_hotkey: str = DEFAULT_PLAY_HOTKEY
    macro_hotkeys: list[MacroHotkeyBinding] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | None = None) -> "AppSettings":
        path = path or default_settings_path()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Settings must be a JSON object.")
            hotkey = str(raw.get("play_hotkey", DEFAULT_PLAY_HOTKEY))
            display_to_binding(hotkey)
            macro_hotkeys = []
            used_bindings = {display_to_binding(hotkey)} - {None}
            for item in raw.get("macro_hotkeys", []):
                try:
                    if not isinstance(item, dict):
                        continue
                    candidate = MacroHotkeyBinding.from_dict(item)
                    binding = display_to_binding(candidate.hotkey)
                    if binding is None or binding in used_bindings:
                        continue
                    used_bindings.add(binding)
                    macro_hotkeys.append(candidate)
                except (AttributeError, TypeError, ValueError):
                    continue
            return cls(play_hotkey=hotkey, macro_hotkeys=macro_hotkeys)
        except (AttributeError, OSError, ValueError, TypeError):
            return cls()

    def save(self, path: Path | None = None) -> None:
        path = path or default_settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


def reset_settings_for_startup(path: Path | None = None) -> AppSettings:
    """Start with no previous custom hotkeys or saved-macro assignments."""
    settings = AppSettings()
    try:
        settings.save(path)
    except OSError:
        # The app can still use clean in-memory defaults if settings cannot be written.
        pass
    return settings


def prepare_hotkey_assignments(assignments: dict[str, str]) -> dict[str, str]:
    """Convert token/display assignments into unique pynput binding/token pairs."""
    prepared: dict[str, str] = {}
    for token, display in assignments.items():
        binding = display_to_binding(display)
        if binding is None:
            continue
        if binding in prepared:
            raise ValueError(f"{display} is already in use for this session. Choose a different hotkey.")
        prepared[binding] = token
    return prepared


class GlobalHotkeyRegistry:
    """Owns all app-wide macro playback shortcuts."""

    def __init__(self, callback: Callable[[str], None]) -> None:
        self.callback = callback
        self.listener = None
        self.assignments: dict[str, str] = {}

    def configure(self, assignments: dict[str, str]) -> None:
        self.stop()
        prepared = prepare_hotkey_assignments(assignments)
        self.assignments = dict(assignments)
        if not prepared:
            return
        try:
            from pynput import keyboard
        except ImportError as exc:
            raise RuntimeError("pynput is required for global hotkeys.") from exc
        callbacks = {
            binding: (lambda assignment_token=token: self.callback(assignment_token))
            for binding, token in prepared.items()
        }
        self.listener = keyboard.GlobalHotKeys(callbacks)
        self.listener.start()

    def stop(self) -> None:
        if self.listener is not None:
            self.listener.stop()
            self.listener = None

