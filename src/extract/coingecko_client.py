import sys
from pathlib import Path

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))


import json
import logging
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from utils import get_base_directory

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

API_KEY = os.getenv("COIN_GECKO_API_KEY")

BASE_URL = "https://api.coingecko.com/api/v3"

SELECTED_COINS = ["bitcoin", "ethereum", "tether", "binancecoin", "solana", "ripple", "usd-coin", "cardano", "dogecoin", "avalanche-2"]


def fetch_api_data():
    if not API_KEY:
        raise ValueError("COIN_GECKO_API_KEY is not set")

    url = f"{BASE_URL}/coins/markets"

    params = {
        "vs_currency": "usd",
        "ids": ",".join(SELECTED_COINS),
        "sparkline": False
    }

    headers = {
        "x-cg-pro-api-key": API_KEY,
        "Accept": "application/json"
    }

    response = requests.get(
        url=url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise ValueError("CoinGecko API returned empty data")

    return data


def save_raw_data(data):
    date_time = datetime.now().strftime(format='%Y-%m-%d %H:%M:%S')

    snapshot = {
        "snapshot_datetime": date_time,
        "data": data
    }

    base_dir = get_base_directory()
    file_name = f"crypto_{date_time}.json"
    file_path = os.path.join(base_dir, "data", "raw", file_name)

    with open(file_path, 'w') as file:
        file.write(json.dumps(snapshot))
    

    logger.info("Successfully saved %s", file_name)


def main():
    try:
        data = fetch_api_data()

        logger.info(
            "Successfully fetched %d records from CoinGecko API",
            len(data)
        )

        save_raw_data(data)

    except requests.exceptions.RequestException:
        logger.exception("CoinGecko API request failed")

    except ValueError as e:
        logger.exception("Data validation failed: %s", e)

    except Exception:
        logger.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()