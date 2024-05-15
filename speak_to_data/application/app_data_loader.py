from pathlib import Path
from speak_to_data import communication


class AppDataLoader:
    def __init__(self, app_data_path: Path) -> None:
        self.app_data_path = app_data_path

    @staticmethod
    def _format(name: str) -> str:
        return name.capitalize().replace("-", " ")

    def _load_app_data(self, data_type: str) -> tuple[tuple[str, str], ...]:
        app_data = communication.read_json(self.app_data_path)
        category = app_data[data_type]
        return tuple((name, self._format(name)) for name in category)

    def load_actions(self) -> tuple[tuple[str, str], ...]:
        return self._load_app_data("actions")

    def load_crops(self) -> tuple[tuple[str, str], ...]:
        return self._load_app_data("crops")

    def load_locations(self) -> tuple[tuple[str, str], ...]:
        return self._load_app_data("locations")

    def load_location_types(self) -> tuple[tuple[str, str], ...]:
        return self._load_app_data("location-types")
