import json
import tempfile
import unittest
from pathlib import Path

from macro_play.models import Action, Macro, MacroSlot


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

    def test_set_wait_time_updates_only_selected_actions(self):
        first = Action("mouse_click", delay=0.1)
        second = Action("text", delay=0.2)
        third = Action("wait", delay=0.3)
        macro = Macro(actions=[first, second, third])

        changed = macro.set_wait_time({first.id, third.id}, 1.25)

        self.assertEqual(changed, 2)
        self.assertEqual([action.delay for action in macro.actions], [1.25, 0.2, 1.25])

    def test_set_wait_time_rejects_invalid_value(self):
        macro = Macro(actions=[Action("wait")])
        with self.assertRaisesRegex(ValueError, "between 0"):
            macro.set_wait_time({macro.actions[0].id}, -1)

    def test_set_length_updates_only_selected_actions(self):
        first = Action("mouse_move", duration=0.1)
        second = Action("mouse_click", duration=0.2)
        third = Action("wait", duration=0.3)
        macro = Macro(actions=[first, second, third])

        changed = macro.set_length({first.id, third.id}, 2.5)

        self.assertEqual(changed, 2)
        self.assertEqual([action.duration for action in macro.actions], [2.5, 0.2, 2.5])

    def test_set_length_rejects_invalid_value(self):
        macro = Macro(actions=[Action("wait")])
        with self.assertRaisesRegex(ValueError, "non-negative"):
            macro.set_length({macro.actions[0].id}, float("inf"))

    def test_macro_slots_have_independent_timelines(self):
        first = MacroSlot(1)
        second = MacroSlot(2)
        first.macro.actions.append(Action("text", data={"text": "first"}))
        first.hotkey = "Ctrl + Alt + A"

        self.assertEqual(len(first.macro.actions), 1)
        self.assertEqual(second.macro.actions, [])
        self.assertEqual(second.hotkey, "Disabled")


if __name__ == "__main__":
    unittest.main()

