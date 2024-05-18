import datetime
import unittest

from speak_to_data import application
from speak_to_data import communication


class Test_INLF2_ExtractParameters(unittest.TestCase):
    def test_givenHowManyHowMuchCrop_thenQueryDataHasCorrectSelection(self):
        query = "How much cress did I sow last year?"
        parameters = application.query_parser.QueryData(query)
        for attr, val in (
                ("columns", {"crop", "action", "quantity"}),
                ("crops", {"cress"}),
                ("actions", {"sow"}),
                ("crux", "what is sum of quantity?"),
        ):
            with self.subTest(msg=f"Testing attr: {attr}"):
                self.assertEqual(getattr(parameters, attr), val)
        with self.subTest(msg="Testing attr: dates"):
            expected = (datetime.date(2023, 1, 1), datetime.date(2023, 12, 31))
            actual = parameters.parsed_date.date_range
            self.assertEqual(expected, actual)

    def test_givenHowMuchTimeOrMaint_thenQueryDataHasCorrectSelection(self):
        query = "How much time to maintain beds in the kitchen?"
        parameters = application.query_parser.QueryData(query)
        for attr, val in (
                ("columns", {"action", "duration", "location"}),
                ("actions", {"maintain"}),
                ("crux", "what is sum of duration?"),
        ):
            with self.subTest(msg=f"Testing attr: {attr}"):
                self.assertEqual(getattr(parameters, attr), val)


class Test_INLF4_GenerateFilteredTable(unittest.TestCase):
    def setUp(self):
        self.mock_data = communication.read_dataset(application.config.MOCK_DATA_SMALL)
        self.sow_cress = application.query_parser.QueryData("How much cress did I sow last year?")
        self.maintain_kitchen = application.query_parser.QueryData("How much time last year to maintain beds in the kitchen?")

    def test_givenSowCress_thenProduceFilteredTable(self):
        expected = {
            "action": [
                "sow",
                "sow"
            ],
            "crop": [
                "cress",
                "cress"
            ],
            "quantity": [
                "1sqft",
                "2sqft"
            ],
        }
        actual = application.prepare_for_model.generate_model_ready_dataset(self.mock_data, self.sow_cress)
        self.assertEqual(expected, actual)

    def test_givenMaintainKitchen_thenProduceFilteredTable(self):
        expected = {
            "action": ["maintain"],
            "duration": ["30"],
            "location": ["kitchen"]
        }
        actual = application.prepare_for_model.generate_model_ready_dataset(self.mock_data, self.maintain_kitchen)
        self.assertEqual(expected, actual)