import unittest

from macro_play.help_content import HELP_SECTIONS


class HelpContentTests(unittest.TestCase):
    def test_manual_has_unique_named_sections(self):
        titles = [title for title, _body in HELP_SECTIONS]
        self.assertGreaterEqual(len(titles), 10)
        self.assertEqual(len(titles), len(set(titles)))

    def test_manual_covers_core_workflows(self):
        manual = "\n".join(f"{title}\n{body}" for title, body in HELP_SECTIONS)
        for required in (
            "Record a macro",
            "Numbered macro selector",
            "Edit actions",
            "Set wait times and lengths",
            "Saved macro hotkeys",
            "Ctrl+F8",
            ".macro.json",
            "Troubleshooting",
            "Safety",
        ):
            self.assertIn(required, manual)


if __name__ == "__main__":
    unittest.main()

