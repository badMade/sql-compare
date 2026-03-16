import sys
import os
import tkinter as tk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from sql_compare import SQLCompareGUI

class TestGUIEmptyState(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("Skipping GUI tests because Tkinter display is not available")
        self.gui = SQLCompareGUI(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except:
            pass

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
