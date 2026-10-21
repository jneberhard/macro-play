from __future__ import annotations

import json
from pathlib import Path
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable

from .models import ACTION_LABELS, Action, Macro
from .hotkeys import AppSettings, GlobalPlayHotkey, MODIFIER_KEYSYMS, MODIFIER_ORDER, hotkey_from_keypress
from .player import MacroPlayer
from .recorder import MacroRecorder


BG = "#0c111d"
PANEL = "#131a29"
PANEL_2 = "#182235"
BORDER = "#263349"
TEXT = "#ecf2ff"
MUTED = "#91a0b8"
ACCENT = "#7c5cff"
ACCENT_HOVER = "#9278ff"
RED = "#ff5c72"
GREEN = "#37d49b"


class ActionDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, action: Action | None = None) -> None:
        super().__init__(parent)
        self.title("Edit action" if action else "Add action")
        self.configure(bg=PANEL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result: Action | None = None
        self.action = action
        self.kind_by_label = {label: kind for kind, label in ACTION_LABELS.items()}
        self.kind_var = tk.StringVar(value=(action.label if action else "Wait"))
        self.delay_var = tk.StringVar(value=f"{action.delay:.3f}" if action else "0.000")
        self.duration_var = tk.StringVar(value=f"{action.duration:.3f}" if action else "1.000")
        self.enabled_var = tk.BooleanVar(value=action.enabled if action else True)
        self.data_vars: dict[str, tk.StringVar] = {}

        body = tk.Frame(self, bg=PANEL, padx=24, pady=20)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="Action type", bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        kinds = list(self.kind_by_label)
        combo = ttk.Combobox(body, textvariable=self.kind_var, values=kinds, state="readonly", width=31)
        combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 14))
        combo.bind("<<ComboboxSelected>>", lambda _e: self._rebuild_fields())

        tk.Label(body, text="Wait before (seconds)", bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w")
        ttk.Entry(body, textvariable=self.delay_var, width=16).grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(4, 14))
        tk.Label(body, text="Duration (seconds)", bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).grid(row=2, column=1, sticky="w")
        ttk.Entry(body, textvariable=self.duration_var, width=16).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(4, 14))

        self.fields = tk.Frame(body, bg=PANEL)
        self.fields.grid(row=4, column=0, columnspan=2, sticky="ew")
        ttk.Checkbutton(body, text="Include this action during playback", variable=self.enabled_var).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(14, 18)
        )
        buttons = tk.Frame(body, bg=PANEL)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Save action", style="Accent.TButton", command=self._save).pack(side="left")
        self._rebuild_fields()
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx()+140}+{parent.winfo_rooty()+90}")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window()

    def _rebuild_fields(self) -> None:
        for child in self.fields.winfo_children():
            child.destroy()
        self.data_vars = {}
        kind = self.kind_by_label[self.kind_var.get()]
        old = self.action.data if self.action and self.action.kind == kind else {}
        schemas: dict[str, list[tuple[str, str, str]]] = {
            "mouse_move": [("x", "X position", "0"), ("y", "Y position", "0")],
            "mouse_click": [("x", "X position", "0"), ("y", "Y position", "0"), ("button", "Button", "left")],
            "mouse_down": [("x", "X position", "0"), ("y", "Y position", "0"), ("button", "Button", "left")],
            "mouse_up": [("x", "X position", "0"), ("y", "Y position", "0"), ("button", "Button", "left")],
            "mouse_scroll": [("x", "X position", "0"), ("y", "Y position", "0"), ("dx", "Horizontal", "0"), ("dy", "Vertical", "-2")],
            "key_down": [("key", "Key (for example Key.enter)", "Key.enter")],
            "key_up": [("key", "Key (for example Key.enter)", "Key.enter")],
            "text": [("text", "Text to type", "")],
            "window": [
                ("title", "Window title", ""), ("app", "Application (macOS)", ""),
                ("x", "X position", "0"), ("y", "Y position", "0"),
                ("width", "Width", "1000"), ("height", "Height", "700"),
            ],
            "wait": [],
        }
        for row, (key, label, default) in enumerate(schemas[kind]):
            tk.Label(self.fields, text=label, bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).grid(
                row=row, column=0, sticky="w", pady=5
            )
            value = old.get(key, default)
            var = tk.StringVar(value=str(value))
            self.data_vars[key] = var
            if key == "button":
                widget = ttk.Combobox(self.fields, textvariable=var, values=("left", "right", "middle"), state="readonly", width=20)
            else:
                widget = ttk.Entry(self.fields, textvariable=var, width=25)
            widget.grid(row=row, column=1, sticky="ew", padx=(16, 0), pady=5)
        self.fields.columnconfigure(1, weight=1)

    def _save(self) -> None:
        try:
            delay = max(0.0, float(self.delay_var.get()))
            duration = max(0.0, float(self.duration_var.get()))
            data: dict[str, object] = {}
            for key, var in self.data_vars.items():
                value: object = var.get()
                if key in {"x", "y", "dx", "dy", "width", "height"}:
                    value = int(value)
                data[key] = value
            kind = self.kind_by_label[self.kind_var.get()]
            if kind == "text" and not data.get("text"):
                raise ValueError("Text cannot be empty.")
            self.result = Action(
                kind=kind,
                delay=delay,
                duration=duration,
                data=data,
                id=self.action.id if self.action else Action(kind).id,
                enabled=self.enabled_var.get(),
            )
            self.destroy()
        except ValueError as exc:
            messagebox.showerror("Check the action", str(exc), parent=self)


class HotkeyCaptureDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Choose Play hotkey")
        self.configure(bg=PANEL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result: str | None = None
        self.modifiers: set[str] = set()
        self.preview_var = tk.StringVar(value="Press your shortcut…")
        self.error_var = tk.StringVar(value="")

        body = tk.Frame(self, bg=PANEL, padx=28, pady=24)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="Press the Play shortcut", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 15)).pack()
        tk.Label(
            body,
            text="Hold any modifiers, then press a letter, number, function, or navigation key.",
            bg=PANEL, fg=MUTED, wraplength=390, justify="center", font=("Segoe UI", 9),
        ).pack(pady=(7, 18))
        tk.Label(
            body, textvariable=self.preview_var, bg=PANEL_2, fg="white",
            width=31, padx=16, pady=18, font=("Segoe UI Semibold", 14),
        ).pack(fill="x")
        tk.Label(body, textvariable=self.error_var, bg=PANEL, fg=RED, wraplength=390, font=("Segoe UI", 9)).pack(pady=(10, 3))
        tk.Label(body, text="Esc cancels  •  Ctrl+F8 is reserved for emergency stop", bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack()
        ttk.Button(body, text="Cancel", command=self.destroy).pack(pady=(18, 0))

        self.bind("<KeyPress>", self._key_down)
        self.bind("<KeyRelease>", self._key_up)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx()+270}+{parent.winfo_rooty()+150}")
        self.after(100, self.focus_force)
        self.wait_window()

    def _key_down(self, event: tk.Event) -> str:
        keysym = str(event.keysym)
        modifier = MODIFIER_KEYSYMS.get(keysym)
        if modifier:
            self.modifiers.add(modifier)
            self.preview_var.set(" + ".join(item for item in MODIFIER_ORDER if item in self.modifiers) + " + …")
            self.error_var.set("")
            return "break"
        if keysym == "Escape" and not self.modifiers:
            self.destroy()
            return "break"
        try:
            self.result = hotkey_from_keypress(self.modifiers, keysym)
            self.destroy()
        except ValueError as exc:
            self.error_var.set(str(exc))
        return "break"

    def _key_up(self, event: tk.Event) -> str:
        modifier = MODIFIER_KEYSYMS.get(str(event.keysym))
        if modifier:
            self.modifiers.discard(modifier)
            if self.modifiers:
                self.preview_var.set(" + ".join(item for item in MODIFIER_ORDER if item in self.modifiers) + " + …")
            else:
                self.preview_var.set("Press your shortcut…")
        return "break"


class MacroPlayApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Macro Play")
        self.root.geometry("1180x760")
        self.root.minsize(980, 650)
        self.root.configure(bg=BG)
        self.macro = Macro()
        self.file_path: Path | None = None
        self.dirty = False
        self.recorder: MacroRecorder | None = None
        self.player = MacroPlayer()
        self.settings = AppSettings.load()
        self._hotkey_events: queue.SimpleQueue[str] = queue.SimpleQueue()
        self.hotkey_manager = GlobalPlayHotkey(lambda: self._hotkey_events.put("play"))
        self._hotkey_after: str | None = None
        self._configure_styles()
        self._build_ui()
        self._bind_shortcuts()
        self._register_play_hotkey(show_error=False, persist=False)
        self._hotkey_after = self.root.after(75, self._poll_hotkeys)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._refresh()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=PANEL, foreground=TEXT, fieldbackground=PANEL_2, bordercolor=BORDER, font=("Segoe UI", 10))
        style.configure("TButton", background=PANEL_2, foreground=TEXT, borderwidth=1, padding=(13, 8))
        style.map("TButton", background=[("active", "#22304a"), ("disabled", PANEL)], foreground=[("disabled", "#526078")])
        style.configure("Accent.TButton", background=ACCENT, foreground="white", borderwidth=0, padding=(16, 9), font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER), ("disabled", "#42377b")])
        style.configure("Record.TButton", background=RED, foreground="white", borderwidth=0, padding=(16, 9), font=("Segoe UI Semibold", 10))
        style.map("Record.TButton", background=[("active", "#ff7184")])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, borderwidth=0, rowheight=38)
        style.configure("Treeview.Heading", background=PANEL_2, foreground=MUTED, borderwidth=0, padding=(8, 10), font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", "#312a62")], foreground=[("selected", "white")])
        style.configure("TEntry", padding=7, insertcolor=TEXT)
        style.configure("TCombobox", padding=6, arrowsize=14)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL_2)], selectbackground=[("readonly", PANEL_2)], selectforeground=[("readonly", TEXT)])
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT)
        style.map("TCheckbutton", background=[("active", PANEL)])
        style.configure("TProgressbar", troughcolor=PANEL_2, background=ACCENT, bordercolor=PANEL_2, lightcolor=ACCENT, darkcolor=ACCENT)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=BG, padx=28, pady=20)
        header.pack(fill="x")
        mark = tk.Canvas(header, width=38, height=38, bg=BG, highlightthickness=0)
        mark.pack(side="left", padx=(0, 12))
        mark.create_rectangle(2, 2, 36, 36, fill=ACCENT, outline="", width=0)
        mark.create_oval(12, 12, 26, 26, fill="white", outline="")
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")
        tk.Label(title_box, text="Macro Play", bg=BG, fg=TEXT, font=("Segoe UI Semibold", 19)).pack(anchor="w")
        tk.Label(title_box, text="Record once. Repeat effortlessly.", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        self.status_badge = tk.Label(header, text="●  READY", bg="#152a27", fg=GREEN, padx=12, pady=6, font=("Segoe UI Semibold", 9))
        self.status_badge.pack(side="right")

        controls = tk.Frame(self.root, bg=PANEL, padx=24, pady=16, highlightbackground=BORDER, highlightthickness=1)
        controls.pack(fill="x", padx=28, pady=(0, 16))
        self.record_btn = ttk.Button(controls, text="●  Record", style="Record.TButton", command=self._record)
        self.record_btn.pack(side="left", padx=(0, 8))
        self.play_btn = ttk.Button(controls, text="▶  Play", style="Accent.TButton", command=self._play)
        self.play_btn.pack(side="left", padx=8)
        self.pause_btn = ttk.Button(controls, text="Ⅱ  Pause", command=self._pause, state="disabled")
        self.pause_btn.pack(side="left", padx=8)
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(controls, text="New", command=self._new).pack(side="left", padx=4)
        ttk.Button(controls, text="Open", command=self._open).pack(side="left", padx=4)
        ttk.Button(controls, text="Save", command=self._save).pack(side="left", padx=4)
        self.control_hint = tk.Label(controls, text="Record your workflow, then refine it below", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.control_hint.pack(side="right")

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=28)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        editor = tk.Frame(content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        editor.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        editor.rowconfigure(2, weight=1)
        editor.columnconfigure(0, weight=1)
        heading = tk.Frame(editor, bg=PANEL, padx=18, pady=14)
        heading.grid(row=0, column=0, sticky="ew")
        tk.Label(heading, text="Action timeline", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 13)).pack(side="left")
        self.summary_label = tk.Label(heading, text="", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.summary_label.pack(side="right")

        tools = tk.Frame(editor, bg=PANEL_2, padx=10, pady=8)
        tools.grid(row=1, column=0, sticky="ew")
        for text, command in [
            ("＋ Add", self._add), ("Edit", self._edit), ("Duplicate", self._duplicate),
            ("↑", lambda: self._move(-1)), ("↓", lambda: self._move(1)), ("Delete", self._delete),
        ]:
            ttk.Button(tools, text=text, command=command).pack(side="left", padx=3)
        ttk.Button(tools, text="Enable / disable", command=self._toggle_enabled).pack(side="right", padx=3)

        tree_wrap = tk.Frame(editor, bg=PANEL)
        tree_wrap.grid(row=2, column=0, sticky="nsew")
        tree_wrap.rowconfigure(0, weight=1)
        tree_wrap.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_wrap, columns=("num", "action", "detail", "wait", "duration"), show="headings", selectmode="extended")
        columns = {
            "num": ("#", 46, "center"), "action": ("ACTION", 145, "w"), "detail": ("DETAILS", 315, "w"),
            "wait": ("WAIT", 75, "e"), "duration": ("LENGTH", 75, "e"),
        }
        for key, (label, width, anchor) in columns.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=40, anchor=anchor, stretch=(key == "detail"))
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.tag_configure("disabled", foreground="#59677d")
        self.tree.tag_configure("active", background="#27214f")
        self.tree.bind("<Double-1>", lambda _e: self._edit())
        self.tree.bind("<Delete>", lambda _e: self._delete())

        side = tk.Frame(content, bg=PANEL, width=260, padx=20, pady=18, highlightbackground=BORDER, highlightthickness=1)
        side.grid(row=0, column=1, sticky="ns")
        side.grid_propagate(False)
        tk.Label(side, text="Playback settings", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 13)).pack(anchor="w", pady=(0, 18))
        self.name_var = tk.StringVar(value=self.macro.name)
        self.name_var.trace_add("write", lambda *_: self._name_changed())
        self._field_label(side, "Macro name")
        ttk.Entry(side, textvariable=self.name_var).pack(fill="x", pady=(4, 16))
        self._field_label(side, "Repeat")
        self.repeat_var = tk.IntVar(value=1)
        ttk.Spinbox(side, from_=1, to=999, textvariable=self.repeat_var).pack(fill="x", pady=(4, 16))
        self.loop_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(side, text="Loop until stopped", variable=self.loop_var).pack(anchor="w", pady=(0, 16))
        self._field_label(side, "Playback speed")
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_row = tk.Frame(side, bg=PANEL)
        speed_row.pack(fill="x", pady=(4, 14))
        ttk.Scale(speed_row, from_=0.25, to=3.0, variable=self.speed_var, command=lambda _v: self._update_speed()).pack(side="left", fill="x", expand=True)
        self.speed_label = tk.Label(speed_row, text="1.0×", width=5, bg=PANEL, fg=TEXT)
        self.speed_label.pack(side="right", padx=(8, 0))
        self.restore_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(side, text="Restore window positions", variable=self.restore_var).pack(anchor="w", pady=(4, 8))
        tk.Label(side, text="Re-focuses and resizes recorded windows before their actions run.", wraplength=215, justify="left", bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self._field_label(side, "Play hotkey")
        self.play_hotkey_var = tk.StringVar(value=self.settings.play_hotkey)
        hotkey_row = tk.Frame(side, bg=PANEL)
        hotkey_row.pack(fill="x", pady=(4, 4))
        ttk.Entry(hotkey_row, textvariable=self.play_hotkey_var, state="readonly", width=17).pack(side="left", fill="x", expand=True)
        ttk.Button(hotkey_row, text="Change", command=self._choose_play_hotkey).pack(side="left", padx=(6, 0))
        disable_link = tk.Label(side, text="Disable hotkey", bg=PANEL, fg="#a99aff", cursor="hand2", font=("Segoe UI", 8, "underline"))
        disable_link.pack(anchor="w")
        disable_link.bind("<Button-1>", lambda _e: self._disable_play_hotkey())
        tk.Label(side, text="Press the combination you want. It works from any application.", wraplength=215, justify="left", bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
        ttk.Separator(side).pack(fill="x", pady=20)
        self._field_label(side, "Progress")
        self.progress = ttk.Progressbar(side, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(8, 6))
        self.progress_label = tk.Label(side, text="Ready to play", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.progress_label.pack(anchor="w")

        footer = tk.Frame(self.root, bg=BG, padx=30, pady=14)
        footer.pack(fill="x")
        self.footer_label = tk.Label(footer, text="Tip: double-click any action to edit it. Press Ctrl+F8 for emergency stop.", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.footer_label.pack(side="left")
        tk.Label(footer, text="Ctrl+O Open   Ctrl+S Save   Delete Remove", bg=BG, fg="#617089", font=("Segoe UI", 8)).pack(side="right")

    @staticmethod
    def _field_label(parent: tk.Misc, text: str) -> None:
        tk.Label(parent, text=text.upper(), bg=PANEL, fg=MUTED, font=("Segoe UI Semibold", 8)).pack(anchor="w")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-s>", lambda _e: self._save())
        self.root.bind("<Control-o>", lambda _e: self._open())
        self.root.bind("<Control-n>", lambda _e: self._new())
        self.root.bind("<Control-r>", lambda _e: self._record())
        self.root.bind("<F5>", lambda _e: self._play())

    def _name_changed(self) -> None:
        if self.name_var.get() != self.macro.name:
            self.macro.name = self.name_var.get()
            self._set_dirty(True)

    def _update_speed(self) -> None:
        self.speed_label.configure(text=f"{self.speed_var.get():.1f}×")

    def _register_play_hotkey(self, *, show_error: bool, persist: bool = True) -> None:
        selection = self.play_hotkey_var.get()
        previous = self.hotkey_manager.selection
        try:
            self.hotkey_manager.configure(selection)
            self.settings.play_hotkey = selection
            if persist:
                self.settings.save()
            self.control_hint.configure(text=f"Global Play hotkey: {selection}")
        except (OSError, RuntimeError, ValueError) as exc:
            self.play_hotkey_var.set(previous)
            try:
                self.hotkey_manager.configure(previous)
            except (RuntimeError, ValueError):
                self.hotkey_manager.stop()
            if show_error:
                messagebox.showerror("Hotkey unavailable", str(exc))

    def _choose_play_hotkey(self) -> None:
        dialog = HotkeyCaptureDialog(self.root)
        if dialog.result:
            self.play_hotkey_var.set(dialog.result)
            self._register_play_hotkey(show_error=True)

    def _disable_play_hotkey(self) -> None:
        self.play_hotkey_var.set("Disabled")
        self._register_play_hotkey(show_error=True)

    def _poll_hotkeys(self) -> None:
        try:
            while True:
                event = self._hotkey_events.get_nowait()
                if event == "play" and not self.player.running and not (self.recorder and self.recorder.running):
                    self._play()
        except queue.Empty:
            pass
        self._hotkey_after = self.root.after(75, self._poll_hotkeys)

    def _set_dirty(self, dirty: bool) -> None:
        self.dirty = dirty
        name = self.file_path.name if self.file_path else self.macro.name
        self.root.title(f"{'*' if dirty else ''}{name} — Macro Play")

    def _refresh(self, select: str | None = None) -> None:
        current = select or (self.tree.selection()[0] if hasattr(self, "tree") and self.tree.selection() else None)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, action in enumerate(self.macro.actions, 1):
            self.tree.insert(
                "", "end", iid=action.id,
                values=(index, action.label, action.details(), f"{action.delay:.2f}s", f"{action.duration:.2f}s" if action.duration else "—"),
                tags=(() if action.enabled else ("disabled",)),
            )
        if current and self.tree.exists(current):
            self.tree.selection_set(current)
            self.tree.see(current)
        count = len(self.macro.actions)
        self.summary_label.configure(text=f"{count} action{'s' if count != 1 else ''}  •  {self.macro.estimated_duration:.1f}s")
        self.play_btn.configure(state="normal" if count and not self.player.running else "disabled")

    def _record(self) -> None:
        if self.recorder and self.recorder.running:
            self._stop_recording()
            return
        if self.player.running:
            return
        if self.macro.actions and not messagebox.askyesno("Start a new recording?", "Recording will replace the current action timeline. Save it first if you want to keep it."):
            return
        try:
            self.recorder = MacroRecorder(capture_windows=self.restore_var.get())
            self.recorder.start()
        except RuntimeError as exc:
            messagebox.showerror("Recording unavailable", str(exc))
            return
        self.record_btn.configure(text="■  Stop", style="Record.TButton")
        self.play_btn.configure(state="disabled")
        self.status_badge.configure(text="●  RECORDING", bg="#3a1720", fg=RED)
        self.control_hint.configure(text="Recording globally — return here and press Stop when finished")
        self.footer_label.configure(text="Macro Play ignores clicks inside its own window while recording.")

    def _stop_recording(self) -> None:
        if not self.recorder:
            return
        actions = self.recorder.stop()
        self.macro.actions = actions
        self.recorder = None
        self.record_btn.configure(text="●  Record", style="Record.TButton")
        self.status_badge.configure(text="●  READY", bg="#152a27", fg=GREEN)
        self.control_hint.configure(text="Recording captured — review and edit the timeline")
        self.footer_label.configure(text="Tip: double-click any action to edit it. Press Ctrl+F8 for emergency stop.")
        self._set_dirty(True)
        self._refresh()

    def _play(self) -> None:
        if self.player.running or not self.macro.actions:
            return
        self._set_controls_playing(True)
        self.player.play(
            self.macro.actions,
            repeats=0 if self.loop_var.get() else self.repeat_var.get(),
            speed=self.speed_var.get(),
            restore_windows=self.restore_var.get(),
            on_progress=lambda index, total, loop: self.root.after(0, self._play_progress, index, total, loop),
            on_done=lambda error: self.root.after(0, self._play_done, error),
        )

    def _set_controls_playing(self, playing: bool) -> None:
        self.play_btn.configure(text="■  Stop" if playing else "▶  Play", state="normal")
        self.play_btn.configure(command=self._stop_playback if playing else self._play)
        self.pause_btn.configure(state="normal" if playing else "disabled", text="Ⅱ  Pause")
        self.record_btn.configure(state="disabled" if playing else "normal")
        if playing:
            self.status_badge.configure(text="▶  PLAYING", bg="#24204a", fg="#b9aaff")

    def _stop_playback(self) -> None:
        self.player.stop()
        self.progress_label.configure(text="Stopping…")

    def _pause(self) -> None:
        paused = self.player.toggle_pause()
        self.pause_btn.configure(text="▶  Resume" if paused else "Ⅱ  Pause")
        self.status_badge.configure(text="Ⅱ  PAUSED" if paused else "▶  PLAYING")

    def _play_progress(self, index: int, total: int, loop: int) -> None:
        self.progress["value"] = ((index + 1) / max(1, total)) * 100
        self.progress_label.configure(text=f"Repeat {loop + 1}  •  Action {index + 1} of {total}")
        for item in self.tree.get_children():
            tags = tuple(tag for tag in self.tree.item(item, "tags") if tag != "active")
            self.tree.item(item, tags=tags)
        enabled = [a for a in self.macro.actions if a.enabled]
        if 0 <= index < len(enabled) and self.tree.exists(enabled[index].id):
            tags = tuple(self.tree.item(enabled[index].id, "tags")) + ("active",)
            self.tree.item(enabled[index].id, tags=tags)
            self.tree.see(enabled[index].id)

    def _play_done(self, error: str | None) -> None:
        self._set_controls_playing(False)
        self.status_badge.configure(text="●  READY", bg="#152a27", fg=GREEN)
        self.progress["value"] = 0
        self.progress_label.configure(text="Ready to play")
        self._refresh()
        if error:
            messagebox.showerror("Playback stopped", error)

    def _selected_indices(self) -> list[int]:
        ids = set(self.tree.selection())
        return [i for i, action in enumerate(self.macro.actions) if action.id in ids]

    def _add(self) -> None:
        dialog = ActionDialog(self.root)
        if dialog.result:
            selected = self._selected_indices()
            at = selected[-1] + 1 if selected else len(self.macro.actions)
            self.macro.actions.insert(at, dialog.result)
            self._set_dirty(True)
            self._refresh(dialog.result.id)

    def _edit(self) -> None:
        selected = self._selected_indices()
        if not selected:
            return
        index = selected[0]
        dialog = ActionDialog(self.root, self.macro.actions[index])
        if dialog.result:
            self.macro.actions[index] = dialog.result
            self._set_dirty(True)
            self._refresh(dialog.result.id)

    def _duplicate(self) -> None:
        selected = self._selected_indices()
        if not selected:
            return
        source = self.macro.actions[selected[-1]]
        copy = Action.from_dict(source.to_dict() | {"id": ""})
        self.macro.actions.insert(selected[-1] + 1, copy)
        self._set_dirty(True)
        self._refresh(copy.id)

    def _delete(self) -> None:
        selected = self._selected_indices()
        if not selected:
            return
        for index in reversed(selected):
            self.macro.actions.pop(index)
        self._set_dirty(True)
        self._refresh()

    def _move(self, delta: int) -> None:
        selected = self._selected_indices()
        if len(selected) != 1:
            return
        old = selected[0]
        new = old + delta
        if not 0 <= new < len(self.macro.actions):
            return
        action = self.macro.actions.pop(old)
        self.macro.actions.insert(new, action)
        self._set_dirty(True)
        self._refresh(action.id)

    def _toggle_enabled(self) -> None:
        selected = self._selected_indices()
        for index in selected:
            self.macro.actions[index].enabled = not self.macro.actions[index].enabled
        if selected:
            self._set_dirty(True)
            self._refresh(self.macro.actions[selected[0]].id)

    def _maybe_discard(self) -> bool:
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved macro", "Save your changes before continuing?")
        if answer is None:
            return False
        if answer:
            return self._save()
        return True

    def _new(self) -> None:
        if not self._maybe_discard():
            return
        self.macro = Macro()
        self.file_path = None
        self.name_var.set(self.macro.name)
        self._set_dirty(False)
        self._refresh()

    def _open(self) -> None:
        if not self._maybe_discard():
            return
        path = filedialog.askopenfilename(title="Open macro", filetypes=[("Macro Play files", "*.macro.json"), ("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.macro = Macro.load(path)
            self.file_path = Path(path)
            self.name_var.set(self.macro.name)
            self._set_dirty(False)
            self._refresh()
        except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
            messagebox.showerror("Could not open macro", str(exc))

    def _save(self) -> bool:
        path = self.file_path
        if not path:
            chosen = filedialog.asksaveasfilename(
                title="Save macro", defaultextension=".macro.json",
                filetypes=[("Macro Play files", "*.macro.json"), ("JSON files", "*.json")],
                initialfile=f"{self.macro.name.replace(' ', '-').lower()}.macro.json",
            )
            if not chosen:
                return False
            path = Path(chosen)
        try:
            self.macro.name = self.name_var.get().strip() or "Untitled macro"
            self.macro.save(path)
            self.file_path = path
            self._set_dirty(False)
            self.control_hint.configure(text=f"Saved {path.name}")
            return True
        except OSError as exc:
            messagebox.showerror("Could not save macro", str(exc))
            return False

    def _close(self) -> None:
        if self.recorder and self.recorder.running:
            self.recorder.stop()
        if self.player.running:
            self.player.stop()
        if self._maybe_discard():
            self.hotkey_manager.stop()
            if self._hotkey_after:
                self.root.after_cancel(self._hotkey_after)
            self.root.destroy()


def run() -> None:
    root = tk.Tk()
    MacroPlayApp(root)
    root.mainloop()

