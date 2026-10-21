import tempfile
import unittest
from pathlib import Path

from macro_play.hotkeys import AppSettings, DEFAULT_PLAY_HOTKEY, display_to_binding, hotkey_from_keypress


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

    def test_invalid_saved_selection_uses_default(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "settings.json"
            path.write_text('{"play_hotkey": "Ctrl + F8"}', encoding="utf-8")
            restored = AppSettings.load(path)
        self.assertEqual(restored.play_hotkey, DEFAULT_PLAY_HOTKEY)


if __name__ == "__main__":
    unittest.main()
