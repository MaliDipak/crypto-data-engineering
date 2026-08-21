import os
from dotenv import load_dotenv

from utils import get_base_directory

load_dotenv(os.path.join(get_base_directory(), ".env"))


class CoinGeckoAPIConf:
    API_KEY = os.getenv("COIN_GECKO_API_KEY")


class AWSConf:
    AWS_PROFILE_NAME = os.getenv("AWS_PROFILE_NAME")

    S3_RAW_STORAGE_BUCKET_NAME = os.getenv("S3_RAW_STORAGE_BUCKET_NAME")


class DBConf:

    @staticmethod
    def get_credentials(key):
        if key == "DEV_CRYPTO_MARKET_DB_WRITE":
            return {
                "host": os.getenv("DEV_HOST"),
                "user": os.getenv("DEV_USER"),
                "password": os.getenv("DEV_PASSWORD"),
                "database": os.getenv("DEV_DB"),
            }
        elif key == "RDS_CRYPTO_MARKET_DB_WRITE":
            return {
                "host": os.getenv("PROD_HOST"),
                "user": os.getenv("PROD_USER"),
                "password": os.getenv("PROD_PASSWORD"),
                "database": os.getenv("PROD_DB"),
            }
        else:
            raise ValueError("Invalid Key")
