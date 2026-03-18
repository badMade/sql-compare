## 2024-05-15 - Read-only selectable Tkinter text
**Learning:** Setting Tkinter `Text` widget to `state=disabled` breaks native copy functionality and selection on many platforms. A superior UX is to bind `<Key>` to a custom event handler that returns `"break"` to block typing while allowing navigation (Up, Down, Home, End) and selection/copy commands (Ctrl+C, Ctrl+A), preserving expected user flows.
**Action:** Use the custom `<Key>` event binding approach instead of `state=disabled` for "read-only but selectable" `Text` widgets.
