import sys
import os
import tkinter as tk
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sql_compare import SQLCompareGUI

class TestGUIEmptyState(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("Skipping GUI tests because Tkinter display is not available")
        self.gui = SQLCompareGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_text_widget_readonly_typing_blocked(self):
        initial_text = "Hello World"
        self.gui.txt.delete("1.0", "end")
        self.gui.txt.insert("1.0", initial_text)
        self.root.update_idletasks() # Ensure text is rendered

        # Simulate typing a character 'a'
        self.gui.txt.event_generate("<Key-a>")
        self.root.update_idletasks() # Process event

        # Assert that the text has not changed
        self.assertEqual(self.gui.txt.get("1.0", "end-1c"), initial_text)

        # Simulate typing a character 'b' with Shift (capital B)
        self.gui.txt.event_generate("<Key-B>", state=0x1) # 0x1 for Shift
        self.root.update_idletasks()

        self.assertEqual(self.gui.txt.get("1.0", "end-1c"), initial_text)

        # Simulate typing a number '1'
        self.gui.txt.event_generate("<Key-1>")
        self.root.update_idletasks()

        self.assertEqual(self.gui.txt.get("1.0", "end-1c"), initial_text)

    def test_initial_empty_state(self):
        # Assert tag exists and has correct config
        self.assertEqual(self.gui.txt.tag_cget("empty", "foreground"), "gray")
        self.assertEqual(self.gui.txt.tag_cget("empty", "justify"), "center")

        # Check that the inserted text has the 'empty' tag
        tags = self.gui.txt.tag_names("1.0")
        self.assertIn("empty", tags)

    def test_clear_output_empty_state(self):
        # Insert some dummy non-empty text
        self.gui.txt.delete("1.0", "end")
        self.gui.txt.insert("1.0", "Some query result")

        # Clear output
        self.gui.clear_output()

        # Check that the placeholder text is restored with the 'empty' tag
        tags = self.gui.txt.tag_names("1.0")
        self.assertIn("empty", tags)

if __name__ == '__main__':
    unittest.main()
