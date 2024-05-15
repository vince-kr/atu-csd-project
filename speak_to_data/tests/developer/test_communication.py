import csv
import datetime
from pathlib import Path
from speak_to_data import application, communication
import unittest


# Create test files
fieldnames = ["date", "action", "crop", "quantity", "location", "location_type"]
mock_data = [
    {
        "date": "2023-04-28",
        "action": "sow",
        "crop": "cress",
        "quantity": "1sqft",
        "location": "kitchen",
        "location_type": "indoor-window-box",
    },
    {
        "date": "2023-04-29",
        "action": "sow",
        "crop": "cress",
        "quantity": "2sqft",
        "location": "kitchen",
        "location_type": "indoor-window-box",
    },
]
with open(application.config.MOCK_DATA_ONELINE, "w", newline="") as ol:
    w = csv.DictWriter(ol, fieldnames=fieldnames, dialect="unix")
    w.writeheader()
    w.writerow(mock_data[0])
with open(application.config.MOCK_DATA_SMALL, "w", newline="") as s:
    w = csv.DictWriter(s, fieldnames=fieldnames, dialect="unix")
    w.writeheader()
    w.writerows(mock_data)


class TestPersistenceErrors(unittest.TestCase):
    def setUp(self):
        pass

    def test_givenInvalidPath_thenRaiseError(self):
        invalid_path = Path("not a path")
        with self.assertRaises(FileNotFoundError):
            communication.persist_event(
                {"mock": "dict"},
                invalid_path,
                fieldnames=application.config.FIELD_NAMES,
            )

    def test_givenValidPathButNoAuthorisation_thenRaiseError(self):
        forbidden_path = Path("/usr/bin/cat")
        with self.assertRaises(PermissionError):
            communication.persist_event(
                {"mock": "dict"}, forbidden_path, application.config.FIELD_NAMES
            )


class TestDatasetReader(unittest.TestCase):
    def test_givenPathToMockData_thenReturnDict(self):
        mock_data_path = application.config.MOCK_DATA_SMALL
        expected = mock_data
        for row in expected:
            row["date"] = datetime.date.fromisoformat(row["date"])
        actual = communication.persistence.read_dataset(mock_data_path)
        self.assertEqual(expected, actual)
