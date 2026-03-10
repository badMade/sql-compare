# Palette's Journal

## 2025-03-10 - Disable actions during empty states
**Learning:** In Tkinter apps without explicit disabled states, users can click "Copy", "Save", or "Clear" before running any operation, leading to errors, confusion, or saving blank files. Leaving a blank white screen as the initial state also lacks user direction.
**Action:** Always set `ttk.Button` instances to `state(['disabled'])` when their associated data is not yet available, and provide instructional placeholder text (e.g., "Select files and click Compare to see results here.") in empty text areas. Toggle them to `state(['!disabled'])` only when valid content is present.