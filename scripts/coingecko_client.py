import logging
import time

import requests

from config.config import CoinGeckoAPIConf
from scripts.constants import SELECTED_COINS

logger = logging.getLogger(__name__)


class CoinGeckoAPIClient:
    BASE_URL = "https://api.coingecko.com/api/v3"
    ENDPOINT = "/coins/markets"

    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30

    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self):
        self.api_key = CoinGeckoAPIConf.API_KEY

        if not self.api_key:
            raise ValueError("COIN_GECKO_API_KEY is not set")

        self.session = requests.Session()

        self.session.headers.update(
            {
                "x-cg-demo-api-key": self.api_key,
                "Accept": "application/json",
            }
        )

    def fetch_api_data(self):
        url = f"{self.BASE_URL}{self.ENDPOINT}"

        params = {
            "vs_currency": "usd",
            "ids": ",".join(SELECTED_COINS),
            "sparkline": False,
        }

        for attempt in range(1, self.MAX_RETRIES + 1):

            try:
                logger.info(
                    "Fetching market data. Attempt %d/%d",
                    attempt,
                    self.MAX_RETRIES,
                )

                response = self.session.get(
                    url=url,
                    params=params,
                    timeout=self.REQUEST_TIMEOUT,
                )

                if response.status_code in self.RETRYABLE_STATUS_CODES:

                    logger.warning(
                        "CoinGecko returned retryable status %s",
                        response.status_code,
                    )

                    if attempt == self.MAX_RETRIES:
                        response.raise_for_status()

                    sleep_seconds = 2 ** (attempt - 1)

                    time.sleep(sleep_seconds)

                    continue

                response.raise_for_status()

                data = response.json()

                self.__validate_response(data)

                logger.info(
                    "Successfully fetched %d coins",
                    len(data),
                )

                return data

            except requests.Timeout:
                logger.warning(
                    "CoinGecko request timed out. Attempt %d/%d",
                    attempt,
                    self.MAX_RETRIES,
                )

            except requests.ConnectionError:
                logger.warning(
                    "Connection error while calling CoinGecko. " "Attempt %d/%d",
                    attempt,
                    self.MAX_RETRIES,
                )

            except requests.HTTPError:
                logger.exception("CoinGecko API returned an HTTP error")
                raise

            except ValueError:
                logger.exception("CoinGecko returned invalid JSON or invalid data")
                raise

            if attempt < self.MAX_RETRIES:
                sleep_seconds = 2 ** (attempt - 1)

                time.sleep(sleep_seconds)

        raise RuntimeError("CoinGecko API failed after maximum retries")

    def __validate_response(self, data):
        if not isinstance(data, list):
            raise ValueError("CoinGecko response must be a list")

        if not data:
            raise ValueError("CoinGecko API returned empty data")

        for coin in data:
            if not isinstance(coin, dict):
                raise ValueError("CoinGecko response contains invalid coin data")

            required_fields = {
                "id",
                "symbol",
                "name",
                "current_price",
                "market_cap",
                "last_updated",
            }

            missing_fields = required_fields - coin.keys()

            if missing_fields:
                raise ValueError(
                    f"CoinGecko response missing fields: " f"{missing_fields}"
                )
