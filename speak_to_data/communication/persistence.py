import csv
import datetime
import json
from pathlib import Path


def persist_event(
    event_data: dict[str, str], persistence_path: Path, fieldnames: list[str]
) -> None:
    if not persistence_path.is_file():
        raise FileNotFoundError(
            f"Trying to store the record at {persistence_path} "
            f"but this is not a valid path."
        )
    try:
        with open(persistence_path, "a", newline="") as events_store:
            w = csv.DictWriter(events_store, fieldnames=fieldnames, dialect="unix")
            w.writerow(event_data)
    except PermissionError as pe:
        raise PermissionError(f"Not allowed to write to file {pe.filename}")


def read_dataset(persistence_path: Path) -> list[dict]:
    if not persistence_path.is_file():
        raise FileNotFoundError(
            f"Trying to read from {persistence_path} but this is not a valid path."
        )
    full_dataset = []
    try:
        with open(persistence_path, newline="") as events_store:
            dr = csv.DictReader(events_store, dialect="unix")
            for row in dr:
                date_object = datetime.date.fromisoformat(row["date"])
                row["date"] = date_object
                full_dataset.append(row)
    except PermissionError as pe:
        raise PermissionError(f"Not allowed to read from file at:\n{pe.filename}")
    return full_dataset


def read_json(path: Path) -> dict[str, str]:
    if not path.is_file():
        return dict()
    with open(path) as jp:
        return json.load(jp)
