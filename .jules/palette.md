## 2025-03-30 - Replace disruptive Messagebox with inline text feedback
**Learning:** In Tkinter applications, system-level messageboxes for simple actions (like "Copy") are highly disruptive and modal, halting user flow. Inline visual feedback (like momentarily changing a button text) is much smoother.
**Action:** Replaced `messagebox.showinfo` with `self.root.after(2000, lambda: ...)` logic on the "Copy Output" button text for non-blocking feedback.
