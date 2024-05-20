

def generate_model_ready_dataset(
    dataset: list[dict], query_data) -> dict[str, list[str]]:
    if not query_data or not query_data.columns:
        return dict()

    crops: set[str] = query_data.crops
    actions: set[str] = query_data.actions
    locations: set[str] = query_data.locations
    start_date, end_date = query_data.parsed_date.date_range

    filtered = dataset

    if crops:
        filtered = [row for row in filtered if row["crop"] in crops]
    if actions:
        filtered = [row for row in filtered if row["action"] in actions]
    if locations:
        filtered = [row for row in filtered if row["location"] in locations]
    if start_date and end_date:
        filtered = [row for row in filtered if start_date <= row["date"] <= end_date]

    if not filtered:
        return dict()

    filter_columns = [
        {key: row[key] for key in row.keys() if key in query_data.columns}
        for row in filtered
    ]

    transform = _list_of_dicts_to_one_dict(filter_columns)
    return transform


def _list_of_dicts_to_one_dict(dataset: list[dict[str, str]]) -> dict[str, list[str]]:
    """Transform output of csv.DictWriter to correct format for TaPas"""
    if not dataset:
        return dict()

    # Create dict_keys and dict_values objects
    key_view = dataset[0].keys()
    # dict.values() is cast as list to enable indexing in the dict comprehension
    value_views = tuple(list(row.values()) for row in dataset)
    # Construct a dict by enumerating the keys and selecting the matching value
    # from each member of value_views
    one_dict = {
        key: [value[idx] for value in value_views] for idx, key in enumerate(key_view)
    }
    return one_dict
