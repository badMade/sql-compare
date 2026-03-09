import unittest
import html
import tempfile
import os
from sql_compare import generate_report

class TestSecurity(unittest.TestCase):
    def test_xss_escaped_in_html_report(self):
        xss_payload = "<script>alert('xss')</script>"
        escaped_payload = html.escape(xss_payload)

        # Craft a fake result containing the payload
        fake_result = {
            "ws_equal": True,
            "exact_equal": True,
            "canonical_equal": True,
            "ws_a": "a",
            "ws_b": "b",
            "norm_a": "a",
            "norm_b": "b",
            "can_a": "a",
            "can_b": "b",
            "summary": [f"Malicious summary: {xss_payload}"]
        }

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            # Generate the HTML report
            generate_report(fake_result, mode="both", fmt="html", out_path=temp_path, ignore_ws=True)

            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify the unescaped payload is NOT in the content
            self.assertNotIn(xss_payload, content)

            # Verify the escaped payload IS in the content
            self.assertIn(escaped_payload, content)
        finally:
            os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()