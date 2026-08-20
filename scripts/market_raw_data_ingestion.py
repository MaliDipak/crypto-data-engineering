import logging
from datetime import datetime, timezone

from config.config import AWSConf
from scripts.coingecko_client import CoinGeckoAPIClient
from storage.s3_storage import S3Storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_snapshot(data, ingestion_time):
    return {
        "snapshot_datetime": ingestion_time.isoformat(),
        "data": data,
    }


def save_raw_data(storage, data, ingestion_time):
    snapshot = create_snapshot(
        data=data,
        ingestion_time=ingestion_time,
    )

    object_key = storage.build_object_key(
        ingestion_time=ingestion_time,
        filename=f"market_{ingestion_time:%Y%m%d_%H%M%S}.json",
    )

    s3_uri = storage.upload_json(
        data=snapshot,
        object_key=object_key,
    )

    logger.info(
        "Raw market data uploaded successfully: %s",
        s3_uri,
    )


def main():
    try:
        client = CoinGeckoAPIClient()

        storage = S3Storage(
            bucket_name=AWSConf.S3_RAW_STORAGE_BUCKET_NAME,
            profile_name=AWSConf.AWS_PROFILE_NAME,
        )

        logger.info("Starting market data ingestion")

        data = client.fetch_api_data()

        ingestion_time = datetime.now(timezone.utc)

        save_raw_data(
            storage=storage,
            data=data,
            ingestion_time=ingestion_time,
        )

        logger.info("Market data ingestion completed successfully")

    except Exception:
        logger.exception("Market data ingestion failed")
        raise


if __name__ == "__main__":
    main()
