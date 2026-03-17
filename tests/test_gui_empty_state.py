from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

TK_AVAILABLE = False
try:
    import tkinter as tk
    TK_AVAILABLE = True
except ImportError:
    pass


@unittest.skipUnless(TK_AVAILABLE, "Tkinter not available")
class TestGUIEmptyState(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("Skipping GUI tests because Tkinter display is not available")
        from sql_compare import SQLCompareGUI
        self.gui = SQLCompareGUI(self.root)

    def tearDown(self) -> None:
        try:
            self.root.destroy()
        except (tk.TclError, AttributeError):
            pass

    def test_text_widget_readonly_typing_blocked(self) -> None:
        """Regular key presses must not insert text into the read-only widget."""
        initial_text = "Hello World"
        self.gui.txt.delete("1.0", "end")
        self.gui.txt.insert("1.0", initial_text)
        self.gui.txt.focus_set()
        self.root.update_idletasks()

        for keysym, state in [("<Key-a>", 0), ("<Key-B>", 0x1), ("<Key-1>", 0)]:  # 0x1 = Shift modifier
            self.gui.txt.event_generate(keysym, state=state)
            self.root.update_idletasks()
            self.assertEqual(
                self.gui.txt.get("1.0", "end-1c"),
                initial_text,
                f"Text changed after generating event {keysym}",
            )

    def test_navigation_keys_not_blocked(self) -> None:
        """Arrow/navigation keys must move the cursor (not blocked by read-only handler)."""
        self.gui.txt.delete("1.0", "end")
        self.gui.txt.insert("1.0", "Hello World")
        self.gui.txt.mark_set(tk.INSERT, "1.0")
        self.gui.txt.focus_set()
        self.root.update_idletasks()

        self.gui.txt.event_generate("<Right>")
        self.root.update_idletasks()

        # Cursor must have moved one character to the right
        self.assertEqual(self.gui.txt.index(tk.INSERT), "1.1")
        # Text content must be unchanged
        self.assertEqual(self.gui.txt.get("1.0", "end-1c"), "Hello World")

    def test_ctrl_a_not_blocked(self) -> None:
        """Ctrl+A (select-all shortcut) must not be blocked by the read-only handler."""
        content = "Hello World"
        self.gui.txt.delete("1.0", "end")
        self.gui.txt.insert("1.0", content)
        self.gui.txt.focus_set()
        self.root.update_idletasks()

        self.gui.txt.event_generate("<Control-a>")
        self.root.update_idletasks()

        # Text content must remain unchanged
        self.assertEqual(self.gui.txt.get("1.0", "end-1c"), content)

    def test_ctrl_c_not_blocked(self) -> None:
        """Ctrl+C (copy shortcut) must not be blocked by the read-only handler."""
        content = "Hello World"
        self.gui.txt.delete("1.0", "end")
        self.gui.txt.insert("1.0", content)
        self.gui.txt.tag_add(tk.SEL, "1.0", "end-1c")
        self.gui.txt.focus_set()
        self.root.update_idletasks()

        self.gui.txt.event_generate("<Control-c>")
        self.root.update_idletasks()

        # Text content must remain unchanged after copy
        self.assertEqual(self.gui.txt.get("1.0", "end-1c"), content)

    def test_initial_empty_state(self) -> None:
        # Assert tag exists and has correct config
        self.assertEqual(self.gui.txt.tag_cget("empty", "foreground"), "gray")
        self.assertEqual(self.gui.txt.tag_cget("empty", "justify"), "center")

        # Check that the inserted text has the 'empty' tag
        tags = self.gui.txt.tag_names("1.0")
        self.assertIn("empty", tags)

    def test_clear_output_empty_state(self) -> None:
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
