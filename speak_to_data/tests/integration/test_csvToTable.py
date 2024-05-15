import json
from speak_to_data import application
from speak_to_data.application import config, prepare_for_model, query_parser
from speak_to_data.communication import read_dataset
import unittest


class TestCsvReaderToTableGenerator(unittest.TestCase):
    def setUp(self):
        self.query_data = query_parser.parse_query(
            "How much cress did I sow last year?"
        )

    def test_givenMockDataFromCsv_thenTransformToDictWithKeysValues(self):
        data_from_csv = read_dataset(config.MOCK_DATA_SMALL)
        expected = {
            "action": ["sow", "sow"],
            "crop": ["cress", "cress"],
            "quantity": ["1sqft", "2sqft"],
        }
        actual = prepare_for_model.generate_model_ready_dataset(
            data_from_csv, self.query_data
        )
        self.assertEqual(expected, actual)

    def test_lookAtGenerateRequestObject(self):
        expected = {
            "inputs": {
                "query": "what is sum of quantity?",
                "table": {
                    "action": ["sow", "sow"],
                    "crop": ["cress", "cress"],
                    "quantity": ["1sqft", "2sqft"],
                },
            },
            "options": {
                "wait_for_model": "true",
            },
        }
        actual = application.generate_request_object(
            self.query_data, application.config.MOCK_DATA_SMALL
        )
        self.assertEqual(expected, actual)
