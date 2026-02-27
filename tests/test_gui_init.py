import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import sql_compare
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to mock tkinter before importing sql_compare if we want to avoid side effects,
# but since sql_compare uses "try-except" for tkinter import, we can proceed.
# However, we need to ensure sql_compare.SQLCompareGUI is importable even if tkinter is missing on the system.
# The original code guards tkinter import. But we want to test the GUI class which depends on it.
# So we mock it in sys.modules first.

sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

import tkinter as tk
from tkinter import ttk

# Now import the module under test
import sql_compare

class TestSQLCompareGUIInit(unittest.TestCase):
    def setUp(self):
        # Create a mock root
        self.root = MagicMock()
        # Mock Tkinter variables at the module level used by sql_compare
        # We need to make sure tk.StringVar etc return mocks that act like variables
        pass

    def test_init_creates_widgets(self):
        # We need to ensure that when SQLCompareGUI is instantiated, it uses our mocks.
        # Since we mocked sys.modules['tkinter'], sql_compare should be using that.

        # Instantiate GUI
        gui = sql_compare.SQLCompareGUI(self.root)

        # Check root setup
        self.root.title.assert_called_with("SQL Compare")
        self.root.geometry.assert_called_with("980x780")

        # Check variables initialized
        # sql_compare does: self.sql1_path = tk.StringVar()
        # So we check if our mocked tk.StringVar was called.
        self.assertEqual(tk.StringVar.call_count, 3)
        self.assertEqual(tk.BooleanVar.call_count, 4)

        # Check if frames were created
        self.assertTrue(ttk.Frame.called)

        # Check if core widgets were created
        self.assertTrue(ttk.Entry.called)
        self.assertTrue(ttk.Button.called)
        self.assertTrue(ttk.Radiobutton.called)
        self.assertTrue(ttk.Checkbutton.called)
        self.assertTrue(tk.Text.called)
        self.assertTrue(ttk.Scrollbar.called)

        # Verify instance attributes
        self.assertTrue(hasattr(gui, 'sql1_path'))
        self.assertTrue(hasattr(gui, 'sql2_path'))
        self.assertTrue(hasattr(gui, 'mode'))
        self.assertTrue(hasattr(gui, 'ignore_ws'))
        self.assertTrue(hasattr(gui, 'enable_join'))
        self.assertTrue(hasattr(gui, 'allow_full'))
        self.assertTrue(hasattr(gui, 'allow_left'))

        self.assertTrue(hasattr(gui, 'chk_enable_join'))
        self.assertTrue(hasattr(gui, 'chk_full'))
        self.assertTrue(hasattr(gui, 'chk_left'))

        self.assertTrue(hasattr(gui, 'txt'))

if __name__ == '__main__':
    unittest.main()
