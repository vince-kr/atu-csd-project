import datetime
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Type, Union
from speak_to_data import application, presentation
from speak_to_data.presentation.forms import ActionForm
import unittest


"""
Unique per test:
- Route to get the source for
- Collection of patterns that should appear in the source
"""


@dataclass
class RouteFormFields:
    route: str
    patterns: tuple[str, ...]


class Test_REF1_DisplayFormFields(unittest.TestCase):
    """
    Epic: Record Events (RE)
    Functional requirement: the system must present a browser UI displaying a form with
    fields pertaining to the event that the user wishes to record (RE-F1)
    """

    def setUp(self):
        self.client = presentation.flask_app.test_client()

    def test_correctFormFieldsAppearAtRecordRoutes(self):
        """Confirm that form fields with the expected attributes exist at each route"""
        patterns = {
            "input_with_date_attr": r"\<input[^\>]*type=\"date\"",
            "select_with_name_crop": r"\<select[^\>]*name=\"crop\"",
            "select_with_name_location": r"\<select[^\>]*name=\"location\"",
            "select_with_name_location_type": r"\<select[^\>]*name=\"location_type\"",
            "input_with_radio_attr": r"\<input[^\>]*type=\"radio\"",
            "input_with_text_attr": r"\<input[^\>]*type=\"text\"",
        }

        route_form_tests = (
            RouteFormFields(
                route="/sow",
                patterns=(
                    "input_with_date_attr",
                    "select_with_name_crop",
                    "input_with_text_attr",
                    "select_with_name_location",
                    "select_with_name_location_type",
                ),
            ),
            RouteFormFields(
                route="/plant",
                patterns=(
                    "input_with_date_attr",
                    "select_with_name_crop",
                    "input_with_text_attr",
                    "select_with_name_location",
                    "select_with_name_location_type",
                ),
            ),
            RouteFormFields(
                route="/maintain",
                patterns=(
                    "input_with_date_attr",
                    "input_with_radio_attr",
                    "select_with_name_location",
                    "select_with_name_location_type",
                ),
            ),
            RouteFormFields(
                route="/harvest",
                patterns=(
                    "input_with_date_attr",
                    "select_with_name_crop",
                    "input_with_text_attr",
                    "select_with_name_location",
                    "select_with_name_location_type",
                ),
            ),
        )

        for test in route_form_tests:
            with self.subTest(msg=f"Checking form fields at route: {test.route}"):
                route_html = self.client.get(test.route).text
                self.assertTrue(
                    all(
                        re.search(patterns[pattern], route_html)
                        for pattern in test.patterns
                    )
                )


@dataclass
class FormInputValidation:
    route: str
    form: Type[ActionForm]
    form_data: dict[str, Union[datetime.date, str]]


@dataclass
class FormWarningTrigger:
    pass


class Test_REF2_ValidateInputs(unittest.TestCase):
    """
    Epic: Record Events (RE)
    Functional requirement: the system must validate -- both at the client side and the
    server side -- that data entered by the user is valid. (RE-F2)
    """

    def setUp(self):
        self.app = presentation.flask_app
        self.app.config["WTF_CSRF_ENABLED"] = False

    def test_givenValidInputsPerForm_thenFormValidatesSuccessfully(self):
        valid_input_tests = (
            FormInputValidation(
                route="/sow",
                form=presentation.SowForm,
                form_data={
                    "date": datetime.date.today(),
                    "crop": "cress",
                    "location": "kitchen",
                    "location_type": "indoor-window-box",
                },
            ),
            FormInputValidation(
                route="/maintain",
                form=presentation.MaintainForm,
                form_data={
                    "date": datetime.date.today(),
                    "duration": "1",
                    "location": "kitchen",
                    "location_type": "indoor-window-box",
                },
            ),
            FormInputValidation(
                route="/harvest",
                form=presentation.HarvestForm,
                form_data={
                    "date": datetime.date.today(),
                    "crop": "cress",
                    "weight": "40gr",
                    "location": "kitchen",
                    "location_type": "indoor-window-box",
                },
            ),
        )

        for test in valid_input_tests:
            with self.subTest(msg=f"Testing valid inputs for route: {test.route}"):
                with self.app.test_request_context(
                    path=test.route, method="POST", data=test.form_data
                ):
                    inputs_are_valid = test.form().validate()
                self.assertTrue(inputs_are_valid)

    def test_givenInvalidInputsPerForm_thenFormDoesNotValidate(self):
        invalid_input_tests = (
            FormInputValidation(
                route="/sow",
                form=presentation.SowForm,
                form_data={
                    "date": datetime.date(2038, 1, 20),
                    "crop": "not a crop!",
                    "quantity": "42gr",
                    "location": "not a location!",
                    "location_type": "not a location type!",
                },
            ),
            FormInputValidation(
                route="/maintain",
                form=presentation.MaintainForm,
                form_data={
                    "date": datetime.date(2038, 1, 20),
                    "duration": "not a duration!",
                    "location": "not a location!",
                    "location_type": "not a location type!",
                },
            ),
            FormInputValidation(
                route="/harvest",
                form=presentation.HarvestForm,
                form_data={
                    "date": datetime.date(2038, 1, 20),
                    "crop": "not a crop!",
                    "quantity": "42gr",
                    "location": "not a location!",
                    "location_type": "not a location type!",
                },
            ),
        )

        for test in invalid_input_tests:
            with self.subTest(msg=f"Testing invalid inputs for route: {test.route}"):
                with self.app.test_request_context(
                    path=test.route, method="POST", data=test.form_data
                ):
                    form = test.form()
                    inputs_are_invalid = not form.validate()
                self.assertTrue(inputs_are_invalid)


class Test_REF3_PersistEventRecords(unittest.TestCase):
    """
    Epic: Record Events (RE)
    Functional requirement: for valid input, the system must persist the data entered
    by the user such that it may be recalled later, including between restarts of the
    application. (RE-F3)
    """

    def setUp(self):
        secs_since_epoch = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.test_path = Path(f"./{secs_since_epoch}_test_events.csv")
        with open(self.test_path, "w") as tp:
            tp.write(
                '"date","action","crop","quantity","duration","location","location_type"\n'
            )

    def tearDown(self):
        self.test_path.unlink()

    def test_givenValidEventData_thenWriteRecordToCsv(self):
        # Call a system function that takes event data plus a path
        # Read the string value of the same path
        # Verify it matches expected value
        sow_data = {
            "date": "2024-5-12",
            "action": "sow",
            "crop": "cress",
            "quantity": "1sqft",
            "location": "kitchen",
            "location_type": "indoor-window-box",
        }
        application.event_recorder(sow_data, self.test_path)
        expected = '"date","action","crop","quantity","duration","location","location_type"\n\
"2024-5-12","sow","cress","1sqft","","kitchen","indoor-window-box"\n'
        with open(self.test_path) as f:
            actual = f.read()
        self.assertEqual(expected, actual)


class Test_REF4_InformUserDataNotSaved(unittest.TestCase):
    """
    Epic: Record Events (RE)
    Functional requirement: for invalid input, the system must inform the user that
    their input will not be saved. (RE-F4)
    """

    def setUp(self):
        self.app = presentation.flask_app
        self.app.config["WTF_CSRF_ENABLED"] = False

    def test_givenDateInFuture_thenFormWarnsDateCannotBeFuture(self):
        sow_form_data = {
            "date": datetime.date(2038, 1, 20),
            "crop": "cress",
            "quantity": "42gr",
            "location": "kitchen",
            "location_type": "indoor-window-box",
        }
        with self.app.test_request_context(
            path="/sow", method="POST", data=sow_form_data
        ):
            form = presentation.SowForm()
            form.validate()
            expected = "Event date cannot be in the future.\nYour data was not saved!"
            actual = form.errors["date"][0]
            self.assertEqual(expected, actual)

    def test_givenInvalidCropChoice_thenFormWarnsInvalidSelection(self):
        sow_form_data = {
            "date": datetime.date.today(),
            "crop": "not a crop!",
            "quantity": "42gr",
            "location": "kitchen",
            "location_type": "indoor-window-box",
        }
        with self.app.test_request_context(
            path="/sow", method="POST", data=sow_form_data
        ):
            form = presentation.SowForm()
            form.validate()
            expected = "Not a valid choice.\nYour data was not saved!"
            actual = form.errors["crop"][0]
            self.assertEqual(expected, actual)

    def test_givenInvalidDuration_thenFormWarnsInvalidSelection(self):
        maintain_form_data = {
            "date": datetime.date.today(),
            "duration": "not valid!",
            "location": "kitchen",
            "location_type": "indoor-window-box",
        }
        with self.app.test_request_context(
            path="/maintain", method="POST", data=maintain_form_data
        ):
            form = presentation.MaintainForm()
            form.validate()
            expected = "Not a valid choice.\nYour data was not saved!"
            actual = form.errors["duration"][0]
            self.assertEqual(expected, actual)
