import requests

def exchange(f: str, t: str, a: float) -> float:
    params = {
        "from": f,
        "to": t,
        "amount": a,
    }

    headers = {
        "Authorization": "FREE",
    }

    response = requests.get(
        "https://exchange.nanoapi.dev/api/exchange",
        params=params,
        headers=headers,
        timeout=10
    )

    if response.status_code != requests.codes.ok:
        raise Exception(f"Invalid API return code {response.status_code}")

    return response.json()["nanoapi"]

class ExchangeRate:
    def __init__(self, currency):
        self.foreignto_sgd = exchange(currency, "SGD", 1)
