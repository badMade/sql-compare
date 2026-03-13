import unittest
import tkinter as tk
import sys
import os

# Ensure the parent directory is in the path to import sql_compare
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sql_compare import SQLCompareGUI

class TestSQLCompareGUI(unittest.TestCase):
    def setUp(self):
        # Create a real Tkinter root window
        self.root = tk.Tk()
        # Initialize the GUI with the root window
        self.app = SQLCompareGUI(self.root)

    def tearDown(self):
        # Destroy the root window after each test
        self.root.destroy()
        self.root.update()

    def test_initial_button_states_are_disabled(self):
        """Test that the action buttons are disabled when the app starts."""
        self.assertIn('disabled', self.app.btn_copy.state())
        self.assertIn('disabled', self.app.btn_clear.state())
        self.assertIn('disabled', self.app.btn_save.state())

    def test_initial_output_placeholder_text(self):
        """Test that the output text area contains the empty state placeholder on startup."""
        content = self.app.txt.get("1.0", "end-1c")
        self.assertEqual(content, "Select files and click Compare to see results here.")

    def test_clear_output_resets_state(self):
        """Test that clearing the output resets the text and disables buttons."""
        # Simulate an active state
        self.app.txt.delete("1.0", "end")
        self.app.txt.insert("1.0", "Some comparison results...")
        self.app.btn_copy.state(['!disabled'])
        self.app.btn_clear.state(['!disabled'])
        self.app.btn_save.state(['!disabled'])
        self.app.last_result = {"dummy": "data"}

        # Call clear_output
        self.app.clear_output()

        # Verify state is reset
        content = self.app.txt.get("1.0", "end-1c")
        self.assertEqual(content, "Select files and click Compare to see results here.")
        self.assertIn('disabled', self.app.btn_copy.state())
        self.assertIn('disabled', self.app.btn_clear.state())
        self.assertIn('disabled', self.app.btn_save.state())
        self.assertIsNone(self.app.last_result)

    def test_render_result_updates_state(self):
        """Test that rendering a result updates the text and enables buttons."""
        dummy_result = {
            "ws_equal": True,
            "exact_equal": True,
            "canonical_equal": True,
            "summary": ["Dummy summary line"],
            "diff_ws": "",
            "diff_norm": "",
            "diff_can": ""
        }

        self.app.render_result(dummy_result, "both", False)

        # Verify state is updated
        content = self.app.txt.get("1.0", "end-1c")
        self.assertIn("=== SQL Compare ===", content)
        self.assertIn("- Dummy summary line", content)
        self.assertNotIn('disabled', self.app.btn_copy.state())
        self.assertNotIn('disabled', self.app.btn_clear.state())
        self.assertNotIn('disabled', self.app.btn_save.state())

if __name__ == '__main__':
    unittest.main()
