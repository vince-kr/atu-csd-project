from pathlib import Path
from speak_to_data import application, communication


def event_recorder(
    event_data: dict[str, str],
    persistence_path: Path = application.config.EVENT_RECORDS_PATH,
):
    try:
        communication.persist_event(
            event_data, persistence_path, application.config.FIELD_NAMES
        )
        return ""
    except FileNotFoundError as fe:
        return str(fe)
    except PermissionError as pe:
        return str(pe)
