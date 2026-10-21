import unittest
from unittest.mock import patch

from macro_play.recorder import EventBuilder


class EventBuilderTests(unittest.TestCase):
    def setUp(self):
        self.window_patch = patch("macro_play.recorder.foreground_window", return_value=None)
        self.window_patch.start()

    def tearDown(self):
        self.window_patch.stop()

    def test_many_moves_become_one_action(self):
        builder = EventBuilder(capture_windows=False)
        base = builder._started
        builder.mouse_move(10, 20, base + 0.1)
        builder.mouse_move(50, 80, base + 0.3)
        builder.mouse_move(90, 120, base + 0.5)
        actions = builder.finish()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].kind, "mouse_move")
        self.assertEqual(actions[0].data, {"x": 90, "y": 120})
        self.assertAlmostEqual(actions[0].duration, 0.4)

    def test_click_press_release_becomes_one_action(self):
        builder = EventBuilder(capture_windows=False)
        base = builder._started
        builder.mouse_click(20, 30, "left", True, base + 0.2)
        builder.mouse_click(20, 30, "left", False, base + 0.3)
        actions = builder.finish()
        self.assertEqual([item.kind for item in actions], ["mouse_click"])
        self.assertAlmostEqual(actions[0].duration, 0.1)

    def test_drag_remains_down_move_up(self):
        builder = EventBuilder(capture_windows=False)
        base = builder._started
        builder.mouse_click(20, 30, "left", True, base + 0.1)
        builder.mouse_move(40, 50, base + 0.2)
        builder.mouse_move(80, 90, base + 0.4)
        builder.mouse_click(80, 90, "left", False, base + 0.5)
        actions = builder.finish()
        self.assertEqual([item.kind for item in actions], ["mouse_down", "mouse_move", "mouse_up"])

    def test_plain_typing_becomes_one_text_action(self):
        builder = EventBuilder(capture_windows=False)
        base = builder._started
        for index, char in enumerate("hello"):
            builder.key_down(repr(char), char, base + 0.1 * (index + 1))
            builder.key_up(repr(char), char, base + 0.1 * (index + 1) + 0.03)
        actions = builder.finish()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].kind, "text")
        self.assertEqual(actions[0].data["text"], "hello")


if __name__ == "__main__":
    unittest.main()

