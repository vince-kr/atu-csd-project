import datetime
import re
import requests
from speak_to_data import application, communication, presentation
import unittest

from speak_to_data.application import query_parser, response_parser


class Test_INLF1_DisplayFormFields(unittest.TestCase):
    def setUp(self):
        self.client = presentation.flask_app.test_client()

    def test_correctFormFieldsAppearAtIndex(self):
        patterns = {
            "input_field_pattern": r"<input[^>]*type=\"text\"",
            "submit_button": r"<input[^>]*type=\"submit\"",
        }
        route_html = self.client.get("/").text
        for pattern in patterns:
            with self.subTest(msg=f"Checking element exists: {pattern}"):
                self.assertTrue(re.search(patterns[pattern], route_html))


class Test_INLF2_ExtractParameters(unittest.TestCase):
    def test_givenCropActionDate_thenQueryDataHasCorrectSelection(self):
        query = "How much cress did I sow last year?"
        parameters = application.query_parser.QueryData(query)
        for attr, val in (
            ("columns", {"crop", "action", "quantity"}),
            ("crops", {"cress"}),
            ("actions", {"sow"}),
        ):
            with self.subTest(msg=f"Testing attr: {attr}"):
                self.assertEqual(getattr(parameters, attr), val)
        with self.subTest(msg="Testing attr: dates"):
            expected = (datetime.date(2023, 1, 1), datetime.date(2023, 12, 31))
            actual = parameters.parsed_date.date_range
            self.assertEqual(expected, actual)

    def test_givenMaintenance_thenQueryDataHasCorrectSelection(self):
        query = "How much time to maintain beds in the kitchen?"
        parameters = application.query_parser.QueryData(query)
        for attr, val in (
            ("columns", {"action", "duration", "location"}),
            ("actions", {"maintain"}),
        ):
            with self.subTest(msg=f"Testing attr: {attr}"):
                self.assertEqual(getattr(parameters, attr), val)


class Test_INLF3_GenerateFilteredTable(unittest.TestCase):
    def setUp(self):
        self.mock_data = communication.read_dataset(application.config.MOCK_DATA_SMALL)
        self.sow_cress = application.query_parser.QueryData(
            "How much cress did I sow last year?"
        )
        self.maintain_kitchen = application.query_parser.QueryData(
            "How much time last year to maintain beds in the kitchen?"
        )

    def test_givenSowCress_thenProduceFilteredTable(self):
        expected = {
            "action": ["sow", "sow"],
            "crop": ["cress", "cress"],
            "quantity": ["1sqft", "2sqft"],
        }
        actual = application.prepare_for_model.generate_model_ready_dataset(
            self.mock_data, self.sow_cress
        )
        self.assertEqual(expected, actual)

    def test_givenMaintainKitchen_thenProduceFilteredTable(self):
        expected = {"action": ["maintain"], "duration": ["30"], "location": ["kitchen"]}
        actual = application.prepare_for_model.generate_model_ready_dataset(
            self.mock_data, self.maintain_kitchen
        )
        self.assertEqual(expected, actual)


class Test_INLF4_RetrieveCruxFromQuery(unittest.TestCase):
    def test_givenHowMuchCrop_thenQueryDataHasCorrectCrux(self):
        query = "How much cress did I sow last year?"
        parameters = application.query_parser.QueryData(query)
        expected = "what is sum of quantity?"
        actual = parameters.crux
        self.assertEqual(expected, actual)

    def test_givenHowMuchTimeMaintenance_thenQueryDataHasCorrectCrux(self):
        query = "How much time to maintain beds in the kitchen?"
        parameters = application.query_parser.QueryData(query)
        expected = "what is sum of duration?"
        actual = parameters.crux
        self.assertEqual(expected, actual)


class Test_INLF5_GenerateAndSendRequestObject(unittest.TestCase):
    def setUp(self):
        self.query_data = query_parser.QueryData("How much cress did I sow last year?")
        self.valid_request_object = {
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

    def test_givenTestQueryData_thenRequestObjectHasExpectedValue(self):
        expected = self.valid_request_object
        actual = application.generate_request_object(
            self.query_data, application.config.MOCK_DATA_SMALL
        )
        self.assertEqual(expected, actual)

    def test_givenValidRequestObject_thenTapasModelResponds(self):
        url = "https://api-inference.huggingface.co/models/google/tapas-large-finetuned-wtq"
        api_token = application.config.SECRETS["huggingface_api_token"]
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.post(url, headers=headers, json=self.valid_request_object)
        self.assertTrue(response.status_code)


class Test_INLF6_PresentModelResponseToUser(unittest.TestCase):
    """Parse responses from TaPas model"""
    def setUp(self):
        self.responses = {
            "loading": {
                "error": "Model google/tapas-large-finetuned-wtq is currently loading",
                "estimated_time": 53.877471923828125
            },
            "empty_table": {
                "error": "table is empty",
                "warnings": ["There was an inference error: table is empty"]
            },
            "valid": {
                "answer": "SUM > 1sqft, 2sqft",
                "coordinates": [[0, 2], [1, 2]],
                "cells": [
                    "1sqft",
                    "2sqft"
                ],
                "aggregator": "SUM"
            }
        }

    def test_givenModelError_whenCurrentlyLoading_thenResponseIsLoading(self):
        model_response = self.responses["loading"]
        actual = response_parser.Response(model_response).is_loading
        self.assertTrue(actual)

    def test_givenModelError_whenTableIsEmpty_thenResponseStringIsWarning(self):
        model_response = self.responses["empty_table"]
        expected = "No data was found based on the previous query."
        actual = str(response_parser.Response(model_response))
        self.assertEqual(expected, actual)

    def test_givenModelAnswer_thenResponseStringIsAnswer(self):
        model_response = self.responses["valid"]
        expected = "SUM > 1sqft, 2sqft"
        actual = str(response_parser.Response(model_response))
        self.assertEqual(expected, actual)
