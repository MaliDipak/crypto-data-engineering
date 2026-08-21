import logging

import pandas as pd

from config.config import AWSConf
from database.rds_crypto_market_db_util import RdsCryptoMarketDbUtil
from models.coins import Coins
from storage.s3_storage import S3Storage

logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s | " "%(levelname)s | " "%(name)s | " "%(message)s"),
)

logger = logging.getLogger(__name__)


def get_existing_coin_ids(db_util):
    query = "SELECT api_coin_id FROM coins"
    result = db_util.fetchall(query)

    return {row["api_coin_id"] for row in result}


def load_coins_from_s3(storage, db_util, year, month, day, hour):
    logger.info(
        "Starting coin ingestion for %04d-%02d-%02d %02d:00",
        year,
        month,
        day,
        hour,
    )

    # Get latest S3 object
    recent_object = storage.get_latest_object_for_hour(
        year=year,
        month=month,
        day=day,
        hour=hour,
    )

    if not recent_object or "Key" not in recent_object:
        raise FileNotFoundError(
            f"No S3 object found for {year}-{month:02d}-{day:02d} {hour:02d}:00"
        )

    object_key = recent_object["Key"]
    logger.info("Reading coin data from S3 object: %s", object_key)

    # Read JSON from S3
    data_obj = storage.get_json_object(object_key=object_key)

    if not data_obj or "data" not in data_obj:
        raise ValueError(f"Invalid S3 data format for object: {object_key}")

    snapshot_datetime = data_obj.get("snapshot_datetime")
    logger.info("Snapshot datetime: %s", snapshot_datetime)

    # Convert API response to DataFrame
    coin_df = pd.DataFrame(data_obj["data"])

    if coin_df.empty:
        logger.warning("No coin data found in S3 object: %s", object_key)
        return

    required_columns = ["id", "symbol", "name", "image"]
    missing_columns = [
        column for column in required_columns if column not in coin_df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns in S3 data: {missing_columns}")

    # Select and clean required fields
    coin_df = coin_df[required_columns].copy()
    coin_df = coin_df.drop_duplicates(subset=["id"])

    coin_df = coin_df.rename(
        columns={
            "id": "api_coin_id",
            "image": "image_url",
        }
    )

    logger.info("Total unique coins received: %d", len(coin_df))

    # Get existing coins from DB
    existing_coin_ids = get_existing_coin_ids(db_util)

    logger.info("Existing coins in DB: %d", len(existing_coin_ids))

    # Keep only new coins
    new_coins_df = coin_df[~coin_df["api_coin_id"].isin(existing_coin_ids)]

    if new_coins_df.empty:
        logger.info("No new coins to insert.")
        return

    logger.info("New coins to insert: %d", len(new_coins_df))

    # Convert DataFrame to records
    record_list = list(new_coins_df.itertuples(index=False, name=None))

    # Insert new coins
    Coins.insert_coins_data(
        record_list,
        db_util,
    )

    logger.info(
        "Successfully inserted %d new coins.",
        len(record_list),
    )


def main():
    logger.info("Coin ingestion job started.")

    db_util = None

    try:
        db_util = RdsCryptoMarketDbUtil()

        storage = S3Storage(
            bucket_name=AWSConf.S3_RAW_STORAGE_BUCKET_NAME,
            profile_name=AWSConf.AWS_PROFILE_NAME,
        )

        load_coins_from_s3(
            storage=storage,
            db_util=db_util,
            year=2026,
            month=8,
            day=20,
            hour=9,
        )

        logger.info("Coin ingestion job completed successfully.")

    except Exception:
        logger.exception("Coin ingestion job failed.")
        raise

    finally:
        db_util.close()


if __name__ == "__main__":

    main()
