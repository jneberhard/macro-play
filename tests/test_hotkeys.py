import tempfile
import unittest
from pathlib import Path

from macro_play.hotkeys import (
    AppSettings,
    DEFAULT_PLAY_HOTKEY,
    MacroHotkeyBinding,
    display_to_binding,
    hotkey_from_keypress,
    prepare_hotkey_assignments,
    reset_settings_for_startup,
)


class HotkeySettingsTests(unittest.TestCase):
    def test_default_binding(self):
        self.assertEqual(display_to_binding(DEFAULT_PLAY_HOTKEY), "<ctrl>+<f9>")

    def test_emergency_stop_is_reserved(self):
        with self.assertRaisesRegex(ValueError, "reserved"):
            display_to_binding("Ctrl + F8")
        with self.assertRaisesRegex(ValueError, "reserved"):
            display_to_binding("F8")

    def test_keypress_builds_custom_shortcut(self):
        self.assertEqual(hotkey_from_keypress({"Shift", "Ctrl"}, "k"), "Ctrl + Shift + K")

    def test_bare_function_key_is_allowed(self):
        self.assertEqual(hotkey_from_keypress(set(), "F10"), "F10")

    def test_bare_letter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Add Ctrl"):
            hotkey_from_keypress(set(), "k")

    def test_selection_round_trip(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "settings.json"
            AppSettings(play_hotkey="Ctrl + Alt + P").save(path)
            restored = AppSettings.load(path)
        self.assertEqual(restored.play_hotkey, "Ctrl + Alt + P")

    def test_multiple_macro_hotkeys_round_trip(self):
        bindings = [
            MacroHotkeyBinding("Ctrl + Alt + A", r"C:\macros\alpha.macro.json", "Alpha", "alpha"),
            MacroHotkeyBinding("F10", r"C:\macros\beta.macro.json", "Beta", "beta"),
        ]
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "settings.json"
            AppSettings(play_hotkey="Disabled", macro_hotkeys=bindings).save(path)
            restored = AppSettings.load(path)
        self.assertEqual(restored.play_hotkey, "Disabled")
        self.assertEqual([(item.id, item.hotkey, item.macro_name) for item in restored.macro_hotkeys], [
            ("alpha", "Ctrl + Alt + A", "Alpha"),
            ("beta", "F10", "Beta"),
        ])

    def test_duplicate_assignments_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "already assigned"):
            prepare_hotkey_assignments({"current": "Ctrl + Alt + A", "saved": "Ctrl + Alt + A"})

    def test_disabled_assignment_is_ignored(self):
        self.assertEqual(
            prepare_hotkey_assignments({"current": "Disabled", "saved": "F10"}),
            {"<f10>": "saved"},
        )

    def test_invalid_and_duplicate_saved_bindings_are_skipped(self):
        payload = """{
          "play_hotkey": "Ctrl + Alt + A",
          "macro_hotkeys": [
            {"id": "duplicate", "hotkey": "Ctrl + Alt + A", "macro_path": "one.json", "macro_name": "One"},
            {"id": "invalid", "hotkey": "Ctrl + F8", "macro_path": "two.json", "macro_name": "Two"},
            {"id": "valid", "hotkey": "F10", "macro_path": "three.json", "macro_name": "Three"}
          ]
        }"""
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "settings.json"
            path.write_text(payload, encoding="utf-8")
            restored = AppSettings.load(path)
        self.assertEqual([item.id for item in restored.macro_hotkeys], ["valid"])

    def test_invalid_saved_selection_uses_default(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "settings.json"
            path.write_text('{"play_hotkey": "Ctrl + F8"}', encoding="utf-8")
            restored = AppSettings.load(path)
        self.assertEqual(restored.play_hotkey, DEFAULT_PLAY_HOTKEY)

    def test_startup_clears_previous_hotkeys_and_macro_assignments(self):
        previous = AppSettings(
            play_hotkey="Ctrl + Alt + P",
            macro_hotkeys=[MacroHotkeyBinding("F10", "old.macro.json", "Old macro", "old")],
        )
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "settings.json"
            previous.save(path)
            active = reset_settings_for_startup(path)
            saved = AppSettings.load(path)
        self.assertEqual(active.play_hotkey, DEFAULT_PLAY_HOTKEY)
        self.assertEqual(active.macro_hotkeys, [])
        self.assertEqual(saved.play_hotkey, DEFAULT_PLAY_HOTKEY)
        self.assertEqual(saved.macro_hotkeys, [])


if __name__ == "__main__":
    unittest.main()
