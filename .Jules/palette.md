## 2024-05-24 - Empty States and Disabled Buttons
**Learning:** In Tkinter (and GUIs generally), leaving functional buttons active when there is no data to act upon can lead to confusing empty interactions or errors. Pairing disabled buttons (`.state(['disabled'])`) with helpful placeholder text in the empty state guides users on what actions to take to enable them.
**Action:** Explicitly manage `ttk.Button` interactive states to prevent invalid user actions, and provide empty-state placeholder text to explain the disabled state to the user.
