import csv
from pathlib import Path

import spacy
from speak_to_data.application import (
    config,
    events,
    prepare_for_model,
    query_parser,
    app_data_loader,
)
from speak_to_data.application.query_parser import QueryData
from speak_to_data import communication

nlp = spacy.load("en_core_web_sm")
event_recorder = events.event_recorder
parse_query = query_parser.parse_query
QueryData = QueryData
AppDataLoader = app_data_loader.AppDataLoader


def initial_setup() -> None:
    erp: Path = config.EVENT_RECORDS_PATH
    if not erp.is_file():
        fieldnames = config.FIELD_NAMES
        try:
            with open(erp, "w", newline="") as event_record:
                w = csv.DictWriter(event_record, fieldnames=fieldnames, dialect="unix")
                w.writeheader()
        except OSError:
            pass


def generate_request_object(query_data: QueryData, events_path: Path) -> dict:
    altered_query = query_data.crux
    dataset = communication.read_dataset(events_path)
    altered_dataset = prepare_for_model.generate_model_ready_dataset(
        dataset, query_data
    )

    return {
        "inputs": {
            "query": altered_query,
            "table": altered_dataset,
        },
        "options": {
            "wait_for_model": "true",
        },
    }


def call_tapas_on_hf(request_object: dict) -> dict:
    tapas_interface = communication.TapasInterface(
        config.SECRETS["huggingface_api_token"]
    )
    return tapas_interface.call_model_api(request_object)
