import re

with open('tests/test_gui.py', 'r') as f:
    content = f.read()

# Replace test_initial_button_states_are_disabled
old_test1 = """    def test_initial_button_states_are_disabled(self):
        \"\"\"Test that the action buttons are disabled when the app starts.\"\"\"
        self.assertIn('disabled', self.app.btn_copy.state())
        self.assertIn('disabled', self.app.btn_clear.state())
        self.assertIn('disabled', self.app.btn_save.state())"""

new_test1 = """    def test_initial_button_states_are_disabled(self):
        \"\"\"Test that the action buttons are disabled when the app starts.\"\"\"
        buttons = {
            "copy": self.app.btn_copy,
            "clear": self.app.btn_clear,
            "save": self.app.btn_save,
        }
        for name, btn in buttons.items():
            with self.subTest(button=name):
                self.assertIn('disabled', btn.state())"""

content = content.replace(old_test1, new_test1)

# Replace the assertions in test_clear_output_resets_state
old_test2_assertions = """        self.assertIn('disabled', self.app.btn_copy.state())
        self.assertIn('disabled', self.app.btn_clear.state())
        self.assertIn('disabled', self.app.btn_save.state())"""

new_test2_assertions = """        buttons = {
            "copy": self.app.btn_copy,
            "clear": self.app.btn_clear,
            "save": self.app.btn_save,
        }
        for name, btn in buttons.items():
            with self.subTest(button=name):
                self.assertIn('disabled', btn.state())"""

content = content.replace(old_test2_assertions, new_test2_assertions)

# Replace the assertions in test_render_result_updates_state
old_test3_assertions = """        self.assertNotIn('disabled', self.app.btn_copy.state())
        self.assertNotIn('disabled', self.app.btn_clear.state())
        self.assertNotIn('disabled', self.app.btn_save.state())"""

new_test3_assertions = """        buttons = {
            "copy": self.app.btn_copy,
            "clear": self.app.btn_clear,
            "save": self.app.btn_save,
        }
        for name, btn in buttons.items():
            with self.subTest(button=name):
                self.assertNotIn('disabled', btn.state())"""

content = content.replace(old_test3_assertions, new_test3_assertions)


with open('tests/test_gui.py', 'w') as f:
    f.write(content)
