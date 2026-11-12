"""Smoke tests: both app pages load and show results without errors (Streamlit's built-in test runner)."""
import unittest

from streamlit.testing.v1 import AppTest


class TestApp(unittest.TestCase):
    def test_part2_page_shows_both_test_suggestions(self):
        at = AppTest.from_file("app.py", default_timeout=120).run()
        self.assertEqual(len(at.exception), 0)
        shown = " ".join(e.value for e in list(at.error) + list(at.success) + list(at.info))
        self.assertIn("HbA1c", shown)
        self.assertIn("kidney panel", shown)

    def test_part1_page_loads(self):
        at = AppTest.from_file("app.py", default_timeout=120).run()
        at.switch_page("app_pages/part1.py").run()
        self.assertEqual(len(at.exception), 0)


if __name__ == "__main__":
    unittest.main()
