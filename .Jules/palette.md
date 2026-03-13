## 2023-10-27 - Tkinter Visual Empty States
**Learning:** In Tkinter, you can create visual empty states without custom CSS by using `tag_configure` to style placeholder text (e.g., `foreground='gray'`, `justify='center'`). You must remember to remove this placeholder or clear the text appropriately before inserting real data.
**Action:** When asked to create empty states in Tkinter GUIs, use `tag_configure` and apply it to a placeholder string upon initialization and within `clear_output` methods.
