import json
import tempfile
import unittest
from pathlib import Path

from macro_play.models import Action, Macro


class MacroModelTests(unittest.TestCase):
    def test_round_trip_preserves_actions(self):
        macro = Macro(
            name="Morning setup",
            actions=[
                Action("mouse_move", delay=0.4, duration=0.8, data={"x": 320, "y": 180}),
                Action("text", delay=0.2, data={"text": "hello"}, enabled=False),
            ],
        )
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "test.macro.json"
            macro.save(path)
            restored = Macro.load(path)
        self.assertEqual(restored.name, "Morning setup")
        self.assertEqual(restored.actions[0].data, {"x": 320, "y": 180})
        self.assertFalse(restored.actions[1].enabled)

    def test_rejects_foreign_format(self):
        with self.assertRaises(ValueError):
            Macro.from_dict({"format": "something-else", "actions": []})

    def test_estimated_duration_ignores_disabled_actions(self):
        macro = Macro(actions=[Action("wait", delay=1, duration=2), Action("wait", duration=20, enabled=False)])
        self.assertEqual(macro.estimated_duration, 3)

    def test_legacy_uptime_delay_is_repaired(self):
        action = Action.from_dict({"kind": "mouse_click", "delay": 636652.77, "data": {}})
        self.assertEqual(action.delay, 0.0)

    def test_mouse_action_exposes_cursor_position(self):
        action = Action("mouse_click", data={"x": "420", "y": 315, "button": "left"})
        self.assertEqual(action.cursor_position(), (420, 315))

    def test_keyboard_action_has_no_cursor_position(self):
        self.assertIsNone(Action("text", data={"text": "hello"}).cursor_position())


if __name__ == "__main__":
    unittest.main()

