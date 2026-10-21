from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid


ACTION_LABELS = {
    "window": "Focus window",
    "mouse_move": "Move mouse",
    "mouse_click": "Mouse click",
    "mouse_down": "Mouse button down",
    "mouse_up": "Mouse button up",
    "mouse_scroll": "Scroll",
    "key_down": "Key down",
    "key_up": "Key up",
    "text": "Type text",
    "wait": "Wait",
}


@dataclass(slots=True)
class Action:
    kind: str
    delay: float = 0.0
    duration: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    enabled: bool = True

    @property
    def label(self) -> str:
        return ACTION_LABELS.get(self.kind, self.kind.replace("_", " ").title())

    def details(self) -> str:
        data = self.data
        if self.kind == "window":
            return str(data.get("title", "Unknown window"))
        if self.kind == "mouse_move":
            return f"to ({data.get('x', 0)}, {data.get('y', 0)})"
        if self.kind in {"mouse_click", "mouse_down", "mouse_up"}:
            button = str(data.get("button", "left")).title()
            return f"{button} at ({data.get('x', 0)}, {data.get('y', 0)})"
        if self.kind == "mouse_scroll":
            return f"vertical {data.get('dy', 0):+}, horizontal {data.get('dx', 0):+}"
        if self.kind in {"key_down", "key_up"}:
            return str(data.get("key", ""))
        if self.kind == "text":
            text = str(data.get("text", "")).replace("\n", "\\n")
            return repr(text[:52] + ("…" if len(text) > 52 else ""))
        if self.kind == "wait":
            return f"{self.duration:.2f} seconds"
        return ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Action":
        return cls(
            kind=str(raw["kind"]),
            delay=max(0.0, float(raw.get("delay", 0.0))),
            duration=max(0.0, float(raw.get("duration", 0.0))),
            data=dict(raw.get("data", {})),
            id=str(raw.get("id") or uuid.uuid4().hex[:10]),
            enabled=bool(raw.get("enabled", True)),
        )


@dataclass(slots=True)
class Macro:
    name: str = "Untitled macro"
    actions: list[Action] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = 1

    @property
    def estimated_duration(self) -> float:
        return sum(a.delay + a.duration for a in self.actions if a.enabled)

    def to_dict(self) -> dict[str, Any]:
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return {
            "format": "macro-play",
            "version": self.version,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "actions": [a.to_dict() for a in self.actions],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Macro":
        if raw.get("format") not in (None, "macro-play"):
            raise ValueError("This file is not a Macro Play recording.")
        return cls(
            name=str(raw.get("name", "Untitled macro")),
            actions=[Action.from_dict(item) for item in raw.get("actions", [])],
            created_at=str(raw.get("created_at", datetime.now(timezone.utc).isoformat())),
            updated_at=str(raw.get("updated_at", datetime.now(timezone.utc).isoformat())),
            version=int(raw.get("version", 1)),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Macro":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

