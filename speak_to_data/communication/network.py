from collections import namedtuple
import requests


class TapasInterface:
    Url = namedtuple("Url", ("base_url", "owner", "model"))
    tapas_large = Url(
        "https://api-inference.huggingface.co/models",
        "google",
        "tapas-large-finetuned-wtq",
    )

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.full_url = "/".join(TapasInterface.tapas_large)

    def call_model_api(self, payload: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        response = requests.post(self.full_url, headers=headers, json=payload)
        return response.json()
