from __future__ import annotations

import threading
import time
from typing import Callable

from .models import Action
from .windowing import restore_window


class MacroPlayer:
    def __init__(self) -> None:
        self.running = False
        self.paused = False
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._thread: threading.Thread | None = None

    def play(
        self,
        actions: list[Action],
        *,
        repeats: int = 1,
        speed: float = 1.0,
        restore_windows: bool = True,
        on_progress: Callable[[int, int, int], None] | None = None,
        on_done: Callable[[str | None], None] | None = None,
    ) -> None:
        if self.running:
            return
        self._stop.clear()
        self._pause.clear()
        self.running = True
        self.paused = False
        self._thread = threading.Thread(
            target=self._run,
            args=(list(actions), max(0, repeats), max(0.1, speed), restore_windows, on_progress, on_done),
            daemon=True,
        )
        self._thread.start()

    def toggle_pause(self) -> bool:
        if not self.running:
            return False
        self.paused = not self.paused
        if self.paused:
            self._pause.set()
        else:
            self._pause.clear()
        return self.paused

    def stop(self) -> None:
        self._stop.set()
        self._pause.clear()

    def _wait(self, seconds: float) -> bool:
        remaining = max(0.0, seconds)
        while remaining > 0 and not self._stop.is_set():
            if self._pause.is_set():
                time.sleep(0.03)
                continue
            step = min(0.02, remaining)
            time.sleep(step)
            remaining -= step
        return not self._stop.is_set()

    def _run(
        self,
        actions: list[Action],
        repeats: int,
        speed: float,
        restore_windows: bool,
        on_progress: Callable[[int, int, int], None] | None,
        on_done: Callable[[str | None], None] | None,
    ) -> None:
        error: str | None = None
        emergency_listener = None
        try:
            from pynput import keyboard, mouse

            emergency_listener = keyboard.GlobalHotKeys({"<ctrl>+<f8>": self.stop})
            emergency_listener.start()
            pointer = mouse.Controller()
            keys = keyboard.Controller()
            enabled = [action for action in actions if action.enabled]
            if not enabled:
                return
            total = len(enabled)
            loop = 0
            while repeats == 0 or loop < repeats:
                for index, action in enumerate(enabled):
                    if not self._wait(action.delay / speed):
                        return
                    if on_progress:
                        on_progress(index, total, loop)
                    self._execute(action, pointer, keys, keyboard, mouse, speed, restore_windows)
                    if self._stop.is_set():
                        return
                loop += 1
        except Exception as exc:  # UI boundary: surface platform/input errors cleanly
            error = str(exc)
        finally:
            if emergency_listener:
                emergency_listener.stop()
            self.running = False
            self.paused = False
            if on_done:
                on_done(error)

    def _execute(self, action, pointer, keys, keyboard, mouse, speed, restore_windows) -> None:
        data = action.data
        if action.kind == "window":
            if restore_windows:
                restore_window(data)
            return
        if action.kind == "mouse_move":
            start_x, start_y = pointer.position
            end_x, end_y = int(data["x"]), int(data["y"])
            duration = action.duration / speed
            steps = max(1, int(duration * 60))
            for step in range(1, steps + 1):
                if self._stop.is_set():
                    return
                while self._pause.is_set() and not self._stop.is_set():
                    time.sleep(0.03)
                ratio = step / steps
                smooth = ratio * ratio * (3 - 2 * ratio)
                pointer.position = (
                    round(start_x + (end_x - start_x) * smooth),
                    round(start_y + (end_y - start_y) * smooth),
                )
                if duration:
                    time.sleep(duration / steps)
            return
        if action.kind in {"mouse_click", "mouse_down", "mouse_up"}:
            pointer.position = (int(data.get("x", 0)), int(data.get("y", 0)))
            button = getattr(mouse.Button, str(data.get("button", "left")), mouse.Button.left)
            if action.kind == "mouse_click":
                pointer.press(button)
                if action.duration:
                    self._wait(action.duration / speed)
                pointer.release(button)
            elif action.kind == "mouse_down":
                pointer.press(button)
            else:
                pointer.release(button)
            return
        if action.kind == "mouse_scroll":
            pointer.position = (int(data.get("x", 0)), int(data.get("y", 0)))
            pointer.scroll(int(data.get("dx", 0)), int(data.get("dy", 0)))
            return
        if action.kind in {"key_down", "key_up"}:
            key_name = str(data.get("key", ""))
            key = self._parse_key(key_name, keyboard)
            (keys.press if action.kind == "key_down" else keys.release)(key)
            return
        if action.kind == "text":
            keys.type(str(data.get("text", "")))
            return
        if action.kind == "wait":
            self._wait(action.duration / speed)

    @staticmethod
    def _parse_key(name: str, keyboard):
        if name.startswith("Key."):
            return getattr(keyboard.Key, name[4:])
        if len(name) >= 3 and name[0] == name[-1] and name[0] in "'\"":
            return name[1:-1]
        return name

