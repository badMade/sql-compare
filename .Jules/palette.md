## 2024-05-18 - Explicit Tkinter Button States
**Learning:** In Tkinter, explicitly managing `ttk.Button` interactive states using `.state(['disabled'])` and `.state(['!disabled'])` paired with helpful UI cues (like empty-state placeholder text) significantly improves user feedback and prevents invalid actions.
**Action:** Always implement empty-state placeholders and disable action buttons when the required data (like `self.last_result`) is not available to the GUI yet.
