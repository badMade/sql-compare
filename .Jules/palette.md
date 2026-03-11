## 2024-03-11 - Read-Only Text Widget Selection Fix
**Learning:** In Tkinter, setting a `Text` widget's state to `disabled` makes it read-only but also completely breaks the user's ability to select and copy text natively in some versions.
**Action:** Instead of `state="disabled"`, leave the state as `normal` and bind a custom `<Key>` event handler that allows navigation keys (`Up`, `Down`, etc.) and clipboard shortcuts (`Ctrl+C`, `Ctrl+A`) while returning `"break"` to swallow any typing/modification events.

## 2024-03-11 - Text Widget Empty State Styling
**Learning:** Visual empty states with custom text colors and alignments can be created within standard Tkinter `Text` widgets without custom CSS or complex layout wrappers.
**Action:** Use `Text.tag_configure` to define a style (e.g., `foreground="gray", justify="center"`) and apply this tag specifically to the placeholder text when calling `Text.insert`.
