import unittest

import datetime
from pathlib import Path

from speak_to_data.application import config, events, prepare_for_model, query_parser, response_parser
from speak_to_data.communication import read_dataset
import spacy

nlp = spacy.load("en_core_web_sm")


class TestEventRecorder(unittest.TestCase):
    def setUp(self):
        secs_since_epoch = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.test_path = Path(f"./{secs_since_epoch}_test_events.csv")
        self.test_path.touch()

    def tearDown(self):
        self.test_path.unlink()

    def test_givenValidDict_eventRecorderReturnsEmptyString(self):
        expected = ""
        actual = events.event_recorder(
            {
                "crop": "cress",
                "location": "kitchen",
                "location_type": "indoors-window-box",
            },
            self.test_path,
        )
        self.assertEqual(expected, actual)


class TestQueryParserCropsAndActions(unittest.TestCase):
    """Extract crop and action data from a user query"""

    # Test retrieving crops from query
    # Logic for retrieving ACTIONS is identical
    def test_givenSetOfValidCrops_whenQueryContainsOneCrop_returnCrop(self):
        one_crop = "How much cress did I sow last year?"
        expected = {"cress"}
        actual = query_parser.QueryData(one_crop).crops
        self.assertEqual(expected, actual)

    def test_givenSetOfValidCrops_whenQueryContainsTwoCrops_returnBoth(self):
        two_crops = "How many beds have potatoes or broadbeans?"
        expected = {"potato", "broadbean"}
        actual = query_parser.QueryData(two_crops).crops
        self.assertEqual(expected, actual)

    def test_givenSetOfValidCrops_whenQueryContainsNoCrops_returnEmptySet(self):
        no_crops = "How much time did I spend on maintenance last month?"
        actual = query_parser.QueryData(no_crops).crops
        self.assertTrue(len(actual) == 0)

    def test_givenQueryWithAction_thenDataContainsOneAction(self):
        one_action = "How much cress did I sow last year?"
        expected = {"sow"}
        actual = query_parser.QueryData(one_action).actions
        self.assertEqual(expected, actual)

    def test_givenQueryWithLocation_thenDataContainsOneLocation(self):
        one_location = "How much maintenance for the kitchen?"
        expected = {"kitchen"}
        actual = query_parser.QueryData(one_location).locations
        self.assertEqual(expected, actual)


class TestQueryParserDateRange(unittest.TestCase):
    """Extract date objects from user query"""

    def setUp(self):
        self.today = datetime.date.today()

    # Valid cases: one or two mentions of a date, all of which can be parsed
    # QueryDate.date_range exposes a valid tuple of start date, end date
    def test_givenQueryWithValidDate_thenQueryDateObjectIsTrue(self):
        valid_date_indication = "How much cress did I sow last year?"
        query_date = query_parser.QueryData(valid_date_indication).parsed_date
        self.assertTrue(query_date)

    def test_givenLastYear_thenReturnDateRangeOneOneToTwelveThirtyOne(self):
        last_year = "How much cress did I sow last year?"
        year = self.today.year - 1
        expected = (
            datetime.date(year, 1, 1),
            datetime.date(year, 12, 31),
        )
        query_date = query_parser.QueryData(last_year).parsed_date
        actual = query_date.date_range
        self.assertEqual(expected, actual)

    def test_givenLastMonth_thenReturnDateRangeYearMonthOneToYearMonthEnd(self):
        date_last_month = "How much time did I spend on maintenance last month?"
        year = self.today.year
        month = self.today.month
        last_month = month - 1
        last_day = (datetime.date(year, month, 1) - datetime.timedelta(days=1)).day
        expected = (
            datetime.date(year, last_month, 1),
            datetime.date(year, last_month, last_day),
        )
        query_date = query_parser.QueryData(date_last_month).parsed_date
        actual = query_date.date_range
        self.assertEqual(expected, actual)

    def test_givenNamedMonth_thenReturnDateRangeYearMonthOnetoYearMonthEnd(self):
        february = "Did I plant pumpkins in February?"
        expected = (
            datetime.date(self.today.year, 2, 1),
            datetime.date(self.today.year, 2, 29),
        )
        query_date = query_parser.QueryData(february).parsed_date
        actual = query_date.date_range
        self.assertEqual(expected, actual)

    def test_givenLastWeek_thenReturnDateRangeLastWeek(self):
        last_week = "How many courgettes did I harvest last week?"
        year = self.today.year
        week = self.today.isocalendar().week - 1
        expected = (
            datetime.date.fromisocalendar(year, week, 1),
            datetime.date.fromisocalendar(year, week, 7),
        )
        query_date = query_parser.QueryData(last_week).parsed_date
        actual = query_date.date_range
        self.assertEqual(expected, actual)

    # Not valid cases: no date entities, or existing entities cannot be parsed
    # QueryDate.warning exposes a description of the issue
    def test_givenQueryWithoutDates_thenQueryDateObjectIsFalse(self):
        no_dates = "How many beds have potatoes or broadbeans?"
        query_date = query_parser.QueryData(no_dates).parsed_date
        self.assertFalse(query_date)
        expected = (
            "This query does not contain any dates. "
            "Please specify a date or date range."
        )
        actual = query_date.warning
        self.assertEqual(expected, actual)

    def test_givenQueryWithFutureDate_thenQueryDateObjectIsFalse(self):
        future_date = "How many eggs are gathered next Thursday?"
        query_date = query_parser.QueryData(future_date).parsed_date
        self.assertFalse(query_date)
        expected = (
            'Date reference "next Thursday" cannot be parsed as a date, '
            "or represents a future date."
        )
        actual = query_date.warning
        self.assertEqual(expected, actual)

    def test_givenQueryWithTrickyDate_thenQueryDateObjectIsFalse(self):
        tricky_date = "How many eggs were gathered on May Day?"
        query_date = query_parser.QueryData(tricky_date).parsed_date
        self.assertFalse(query_date)
        expected = (
            'Date reference "May Day" cannot be parsed as a date, '
            "or represents a future date."
        )
        actual = query_date.warning
        self.assertEqual(expected, actual)


class TestCrux(unittest.TestCase):
    def test_givenHowMuchCrop_thenCruxIsSumOfQuantityFields(self):
        query = "How much cress did I sow last year?"
        expected = "what is sum of quantity?"
        actual = query_parser.QueryData(query).crux
        self.assertEqual(expected, actual)

    def test_givenMaintainingOrMaintenanceOrMaintain_thenCruxIsSumOfDuration(self):
        queries = [
            "How much time did I spend on maintenance in January?",
            "How much time did I spend maintaining carrot beds last year?",
            "How long did I take to maintain cress in March?"
        ]
        for query in queries:
            with self.subTest(msg=f"Testing maintenance query:\n{query}"):
                expected = "what is sum of duration?"
                actual = query_parser.QueryData(query).crux
                self.assertEqual(expected, actual)


class TestDatasetFilter(unittest.TestCase):
    def setUp(self):
        self.query_data = query_parser.QueryData(
            "How much cress did I sow last year?"
        )
        self.dataset = read_dataset(config.MOCK_DATA_SMALL)

    def test_givenQueryDataWithCrop_thenSelectColumnsContainsCrop(self):
        self.assertTrue("crop" in self.query_data.columns)

    def test_givenQueryDataWithAction_thenSelectColumnsContainsAction(self):
        self.assertTrue("action" in self.query_data.columns)

    def test_givenCruxContainsQuantity_thenSelectColumnsContainsQuantity(self):
        self.assertTrue("quantity" in self.query_data.columns)

    def test_givenListOfOneDict_thenTransformToDictWithKeysValues(self):
        mock_input = [
            {"action": "sow", "crop": "cress", "quantity": "1sqft"},
        ]
        expected = {
            "action": [
                "sow",
            ],
            "crop": [
                "cress",
            ],
            "quantity": [
                "1sqft",
            ],
        }
        actual = prepare_for_model._list_of_dicts_to_one_dict(mock_input)
        self.assertEqual(expected, actual)

    def test_givenListOfTwoDicts_thenTransformToDictWithListValues(self):
        mock_input = [
            {"action": "sow", "crop": "cress", "quantity": "1sqft"},
            {"action": "sow", "crop": "cress", "quantity": "2sqft"},
        ]
        expected = {
            "action": [
                "sow",
                "sow",
            ],
            "crop": [
                "cress",
                "cress",
            ],
            "quantity": [
                "1sqft",
                "2sqft",
            ],
        }
        actual = prepare_for_model._list_of_dicts_to_one_dict(mock_input)
        self.assertEqual(expected, actual)


class TestModelResponse(unittest.TestCase):
    """Parse responses from TaPas model"""
    responses = {
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
        """response object does not need to set a string value"""
        model_response = TestModelResponse.responses["loading"]
        actual = response_parser.Response(model_response).is_loading
        self.assertTrue(actual)

    def test_givenModelError_whenTableIsEmpty_thenResponseStringIsWarning(self):
        model_response = TestModelResponse.responses["empty_table"]
        expected = "No data was found based on the previous query."
        actual = str(response_parser.Response(model_response))
        self.assertEqual(expected, actual)

    def test_givenModelAnswer_thenResponseStringIsAnswer(self):
        model_response = TestModelResponse.responses["valid"]
        expected = "SUM > 1sqft, 2sqft"
        actual = str(response_parser.Response(model_response))
        self.assertEqual(expected, actual)