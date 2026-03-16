import unittest
import tkinter as tk
from sql_compare import SQLCompareGUI

class TestGUIEmptyState(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.gui = SQLCompareGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_initial_empty_state(self):
        # Assert tag exists and has correct config
        with self.subTest(msg="Check foreground color"):
            self.assertEqual(self.gui.txt.tag_cget("empty", "foreground"), "gray")
        with self.subTest(msg="Check justification"):
            self.assertEqual(self.gui.txt.tag_cget("empty", "justify"), "center")

        # Check that the inserted text has the 'empty' tag
        with self.subTest(msg="Check tag is applied"):
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
