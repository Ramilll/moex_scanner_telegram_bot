from typing import Dict

import requests


class CoinmarketcapPriceFetcher:
    def __init__(self, api_key, num_fetch_coins=200):
        self.api_key = api_key
        self.num_fetch_coins = num_fetch_coins

    def fetch_top_coins_prices(self) -> Dict[str, float]:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        parameters = {"start": "1", "limit": self.num_fetch_coins, "convert": "USD"}
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.api_key,
        }

        response = requests.get(url, headers=headers, params=parameters)
        response_json = response.json()

        # Check for a successful response
        if response.status_code == 200:
            data = response_json["data"]
            formatted_data = {}
            for token_data in data:
                symbol = token_data["symbol"]
                price = token_data["quote"]["USD"]["price"]
                formatted_data[symbol] = price
            return formatted_data
        else:
            print("Failed to retrieve data:", response_json.status_code)
            return None
