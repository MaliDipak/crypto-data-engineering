import os
from dotenv import load_dotenv

from utils import get_base_directory

load_dotenv(os.path.join(get_base_directory(), ".env"))


class CoinGeckoAPIConf:
    API_KEY = os.getenv("COIN_GECKO_API_KEY")


class AWSConf:
    AWSProfileName = os.getenv("AWSProfileName")

    S3RawStorageBucketName = os.getenv("S3RawStorageBucketName")
