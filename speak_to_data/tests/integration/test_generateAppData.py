from pathlib import Path
import unittest

from speak_to_data import application


class TestGenerateAppData(unittest.TestCase):
    def setUp(self):
        mock_path = Path(__file__).parent.parent / "test_data" / "mock_app_data.json"
        self.app_data_loader = application.AppDataLoader(mock_path)

    def test_givenMockCropData_thenApplicationGeneratesTuples(self):
        expected = (
            ("cress", "Cress"),
            ("potato", "Potato"),
            ("french-bean", "French bean"),
            ("carrot", "Carrot"),
        )
        actual = self.app_data_loader.load_crops()
        self.assertEqual(expected, actual)

    def test_givenMockLocData_thenApplicationGeneratesTuples(self):
        expected = (
            ("kitchen", "Kitchen"),
            ("living-room", "Living room"),
            ("east-hoop-house", "East hoop house"),
        )
        actual = self.app_data_loader.load_locations()
        self.assertEqual(expected, actual)

    def test_givenMockLocTypeData_thenApplicationGeneratesTuples(self):
        expected = (
            ("indoor-window-box", "Indoor window box"),
            ("hoop-house-raised-bed", "Hoop house raised bed"),
            ("outside-raised-bed", "Outside raised bed"),
        )
        actual = self.app_data_loader.load_location_types()
        self.assertEqual(expected, actual)
