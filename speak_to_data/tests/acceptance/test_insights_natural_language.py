import re
from speak_to_data import application, presentation
import unittest

class Test_INLF1_DisplayFormFields(unittest.TestCase):
    def setUp(self):
        self.client = presentation.flask_app.test_client()

    def test_correctFormFieldsAppearAtIndex(self):
        patterns = {
            "input_field_pattern": r"<input[^>]*type=\"text\"",
            "submit_button": r"<input[^>]*type=\"submit\""
        }
        route_html = self.client.get("/").text
        for pattern in patterns:
            with self.subTest(msg=f"Checking element exists: {pattern}"):
                self.assertTrue(re.search(patterns[pattern], route_html))