import tempfile
import unittest
from pathlib import Path

from macro_play.hotkeys import AppSettings, DEFAULT_PLAY_HOTKEY, HOTKEY_OPTIONS


class HotkeySettingsTests(unittest.TestCase):
    def test_options_reserve_emergency_stop(self):
        self.assertNotIn("Ctrl + F8", HOTKEY_OPTIONS)
        self.assertIn(DEFAULT_PLAY_HOTKEY, HOTKEY_OPTIONS)

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
