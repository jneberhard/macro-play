from __future__ import annotations

from dataclasses import dataclass
import math
import threading
import time
from typing import Callable

from .models import Action
from .windowing import foreground_window


@dataclass(slots=True)
class _Move:
    first: float
    last: float
    x: int
    y: int


@dataclass(slots=True)
class _Click:
    at: float
    x: int
    y: int
    button: str
    moved: bool = False


class EventBuilder:
    """Turns noisy input callbacks into a compact, editable action list."""

    def __init__(self, *, capture_windows: bool = True, excluded_title: str = "Macro Play") -> None:
        self.capture_windows = capture_windows
        self.excluded_title = excluded_title
        self.actions: list[Action] = []
        self._lock = threading.RLock()
        self._started = time.monotonic()
        self._last = self._started
        self._move: _Move | None = None
        self._click: _Click | None = None
        self._text = ""
        self._text_first = 0.0
        self._text_last = 0.0
        self._modifiers: set[str] = set()
        self._last_window_signature: tuple[object, ...] | None = None

    def _timestamp(self, value: float | None) -> float:
        """Keep callback metadata from being mistaken for a monotonic timestamp."""
        current = time.monotonic()
        if value is None:
            return current
        try:
            candidate = float(value)
        except (TypeError, ValueError):
            return current
        if not math.isfinite(candidate) or candidate < self._started - 1.0 or candidate > current + 60.0:
            return current
        return candidate

    def _delay(self, at: float) -> float:
        raw = at - self._last
        recording_age = max(0.0, at - self._started)
        if not math.isfinite(raw) or raw < 0.0 or raw > recording_age + 1.0:
            return 0.0
        return raw

    @staticmethod
    def _elapsed(start: float, end: float) -> float:
        value = end - start
        return value if math.isfinite(value) and value >= 0.0 else 0.0

    def _is_app_window(self) -> bool:
        state = foreground_window()
        return bool(state and self.excluded_title.lower() in state.title.lower())

    def _window(self, now: float) -> bool:
        state = foreground_window()
        if state and self.excluded_title.lower() in state.title.lower():
            return False
        if not self.capture_windows or not state:
            return True
        signature = (state.title, state.x, state.y, state.width, state.height, state.app)
        if signature != self._last_window_signature:
            self.actions.append(Action("window", delay=self._delay(now), data=state.to_dict()))
            self._last = now
            self._last_window_signature = signature
        return True

    def _flush_move(self) -> None:
        move = self._move
        if not move:
            return
        self.actions.append(
            Action(
                "mouse_move",
                delay=self._delay(move.first),
                duration=self._elapsed(move.first, move.last),
                data={"x": move.x, "y": move.y},
            )
        )
        self._last = move.last
        self._move = None

    def _flush_text(self) -> None:
        if not self._text:
            return
        self.actions.append(
            Action(
                "text",
                delay=self._delay(self._text_first),
                duration=self._elapsed(self._text_first, self._text_last),
                data={"text": self._text},
            )
        )
        self._last = self._text_last
        self._text = ""

    def mouse_move(self, x: int, y: int, now: float | None = None) -> None:
        now = self._timestamp(now)
        with self._lock:
            if self._is_app_window():
                return
            self._flush_text()
            if self._click and not self._click.moved:
                click = self._click
                if not self._window(click.at):
                    self._click = None
                    return
                self.actions.append(
                    Action(
                        "mouse_down",
                        delay=self._delay(click.at),
                        data={"x": click.x, "y": click.y, "button": click.button},
                    )
                )
                self._last = click.at
                click.moved = True
            if self._move is None:
                if not self._window(now):
                    return
                self._move = _Move(now, now, int(x), int(y))
            else:
                self._move.last = now
                self._move.x = int(x)
                self._move.y = int(y)

    def mouse_click(self, x: int, y: int, button: str, pressed: bool, now: float | None = None) -> None:
        now = self._timestamp(now)
        with self._lock:
            if self._is_app_window():
                return
            self._flush_text()
            self._flush_move()
            if pressed:
                if not self._window(now):
                    return
                self._click = _Click(now, int(x), int(y), button)
                return
            click = self._click
            if click and click.button == button:
                if click.moved:
                    self.actions.append(
                        Action(
                            "mouse_up",
                            delay=self._delay(now),
                            data={"x": int(x), "y": int(y), "button": button},
                        )
                    )
                else:
                    self.actions.append(
                        Action(
                            "mouse_click",
                            delay=self._delay(click.at),
                            duration=self._elapsed(click.at, now),
                            data={"x": int(x), "y": int(y), "button": button},
                        )
                    )
                self._last = now
            self._click = None

    def mouse_scroll(self, x: int, y: int, dx: int, dy: int, now: float | None = None) -> None:
        now = self._timestamp(now)
        with self._lock:
            if self._is_app_window():
                return
            self._flush_text()
            self._flush_move()
            if not self._window(now):
                return
            self.actions.append(
                Action(
                    "mouse_scroll",
                    delay=self._delay(now),
                    data={"x": int(x), "y": int(y), "dx": int(dx), "dy": int(dy)},
                )
            )
            self._last = now

    def key_down(self, key: str, char: str | None, now: float | None = None) -> None:
        now = self._timestamp(now)
        with self._lock:
            if self._is_app_window():
                return
            self._flush_move()
            is_modifier = key in {
                "Key.ctrl", "Key.ctrl_l", "Key.ctrl_r", "Key.alt", "Key.alt_l", "Key.alt_r",
                "Key.shift", "Key.shift_l", "Key.shift_r", "Key.cmd", "Key.cmd_l", "Key.cmd_r",
            }
            if char and char.isprintable() and not self._modifiers:
                if not self._text:
                    if not self._window(now):
                        return
                    self._text_first = now
                self._text += char
                self._text_last = now
                return
            self._flush_text()
            if not self._window(now):
                return
            self.actions.append(Action("key_down", delay=self._delay(now), data={"key": key}))
            self._last = now
            if is_modifier:
                self._modifiers.add(key)

    def key_up(self, key: str, char: str | None, now: float | None = None) -> None:
        now = self._timestamp(now)
        with self._lock:
            if self._is_app_window():
                return
            if char and char.isprintable() and not self._modifiers:
                return
            self._flush_text()
            self._flush_move()
            if not self._window(now):
                return
            self.actions.append(Action("key_up", delay=self._delay(now), data={"key": key}))
            self._last = now
            self._modifiers.discard(key)

    def finish(self) -> list[Action]:
        with self._lock:
            self._flush_text()
            self._flush_move()
            if self._click:
                click = self._click
                self.actions.append(
                    Action(
                        "mouse_down",
                        delay=self._delay(click.at),
                        data={"x": click.x, "y": click.y, "button": click.button},
                    )
                )
                self._click = None
            maximum_possible_delay = max(1.0, time.monotonic() - self._started + 1.0)
            for action in self.actions:
                if not math.isfinite(action.delay) or action.delay > maximum_possible_delay:
                    action.delay = 0.0
            return list(self.actions)


class MacroRecorder:
    def __init__(self, *, capture_windows: bool = True) -> None:
        self.builder = EventBuilder(capture_windows=capture_windows)
        self._listeners: list[object] = []
        self.running = False

    def start(self) -> None:
        try:
            from pynput import keyboard, mouse
        except ImportError as exc:
            raise RuntimeError("pynput is required. Run: pip install -r requirements.txt") from exc

        self.builder = EventBuilder(capture_windows=self.builder.capture_windows)

        def key_parts(value: object) -> tuple[str, str | None]:
            return str(value), getattr(value, "char", None)

        mouse_listener = mouse.Listener(
            on_move=self.builder.mouse_move,
            on_click=lambda x, y, button, pressed: self.builder.mouse_click(
                x, y, str(button).removeprefix("Button."), pressed
            ),
            on_scroll=self.builder.mouse_scroll,
        )
        keyboard_listener = keyboard.Listener(
            on_press=lambda key: self.builder.key_down(*key_parts(key)),
            on_release=lambda key: self.builder.key_up(*key_parts(key)),
        )
        self._listeners = [mouse_listener, keyboard_listener]
        for listener in self._listeners:
            listener.start()
        self.running = True

    def stop(self) -> list[Action]:
        for listener in self._listeners:
            listener.stop()
        self._listeners = []
        self.running = False
        return self.builder.finish()

