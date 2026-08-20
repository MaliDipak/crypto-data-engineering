import os
from dotenv import load_dotenv

from utils import get_base_directory

load_dotenv(os.path.join(get_base_directory(), ".env"))


class CoinGeckoAPIConf:
    API_KEY = os.getenv("COIN_GECKO_API_KEY")


class AWSConf:
    AWS_PROFILE_NAME = os.getenv("AWS_PROFILE_NAME")

    S3_RAW_STORAGE_BUCKET_NAME = os.getenv("S3_RAW_STORAGE_BUCKET_NAME")
