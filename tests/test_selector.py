import unittest

from macro_play.ui import MacroPlayApp


class MacroSelectorTests(unittest.TestCase):
    def test_visible_slot_count_shrinks_with_available_width(self):
        self.assertEqual(MacroPlayApp._calculate_visible_macro_slots(200), 2)
        self.assertEqual(MacroPlayApp._calculate_visible_macro_slots(304), 4)
        self.assertEqual(MacroPlayApp._calculate_visible_macro_slots(532), 7)

    def test_visible_slot_count_is_capped_at_ten(self):
        self.assertEqual(MacroPlayApp._calculate_visible_macro_slots(760), 10)
        self.assertEqual(MacroPlayApp._calculate_visible_macro_slots(1400), 10)


if __name__ == "__main__":
    unittest.main()

