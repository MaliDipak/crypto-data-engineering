import logging

import pandas as pd

from config.config import AWSConf
from database.rds_crypto_market_db_util import RdsCryptoMarketDbUtil
from models.coin_market_snapshots import CoinMarketSnapshots
from storage.s3_storage import S3Storage

logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s | " "%(levelname)s | " "%(name)s | " "%(message)s"),
)


logger = logging.getLogger(__name__)


RAW_COLUMNS = [
    "id",
    "current_price",
    "market_cap",
    "market_cap_rank",
    "total_volume",
    "high_24h",
    "low_24h",
    "price_change_24h",
    "price_change_percentage_24h",
    "market_cap_change_24h",
    "market_cap_change_percentage_24h",
    "circulating_supply",
    "total_supply",
]

OUTPUT_COLUMNS = [
    "coin_id",
    "snapshot_datetime",
    "current_price_usd",
    "market_cap_usd",
    "market_cap_rank",
    "total_volume_usd",
    "high_24h_usd",
    "low_24h_usd",
    "price_change_24h_usd",
    "price_change_24h_pct",
    "market_cap_change_24h_usd",
    "market_cap_change_24h_pct",
    "circulating_supply",
    "total_supply",
]


def get_coins_mapping(db_util):
    """
    Fetch coin_id and api_coin_id mapping from the coins table.
    """
    query = """
        SELECT
            coin_id,
            api_coin_id
        FROM coins
    """

    coins_df = db_util.fetchall_df(query)

    if coins_df.empty:
        raise ValueError("No coins found in the coins table.")

    logger.info(
        "Loaded %d coins from coins table.",
        len(coins_df),
    )

    return coins_df


def get_latest_snapshot(storage, year, month, day, hour):
    """
    Fetch the latest raw coin snapshot from S3 for the given hour.
    """
    recent_object = storage.get_latest_object_for_hour(
        year=year,
        month=month,
        day=day,
        hour=hour,
    )

    if not recent_object or "Key" not in recent_object:
        raise FileNotFoundError(
            f"No S3 object found for " f"{year}-{month:02d}-{day:02d} {hour:02d}:00"
        )

    object_key = recent_object["Key"]

    logger.info(
        "Reading raw snapshot from S3: %s",
        object_key,
    )

    data_obj = storage.get_json_object(object_key=object_key)

    if not data_obj or "data" not in data_obj:
        raise ValueError(f"Invalid snapshot data received from S3: {object_key}")

    return data_obj


def transform_snapshot_data(data_obj, coins_df):
    """
    Transform raw CoinGecko snapshot data into the
    coin_market_snapshots table format.
    """
    snapshot_datetime = data_obj.get("snapshot_datetime")
    raw_data = data_obj.get("data")

    if not snapshot_datetime:
        raise ValueError("snapshot_datetime is missing from S3 data.")

    if not raw_data:
        logger.warning(
            "No coin snapshot data found for %s.",
            snapshot_datetime,
        )
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    snapshot_df = pd.DataFrame(raw_data)

    missing_columns = [
        column for column in RAW_COLUMNS if column not in snapshot_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns in raw snapshot data: " f"{missing_columns}"
        )

    snapshot_df = snapshot_df[RAW_COLUMNS].copy()

    snapshot_df["snapshot_datetime"] = snapshot_datetime

    # Map CoinGecko API coin ID to internal database coin_id.
    snapshot_df = snapshot_df.merge(
        coins_df,
        how="left",
        left_on="id",
        right_on="api_coin_id",
    )

    # Check for coins that are present in S3 but missing from DB.
    missing_coin_mapping = snapshot_df[snapshot_df["coin_id"].isna()]

    if not missing_coin_mapping.empty:
        logger.warning(
            "%d coins from snapshot could not be mapped to " "the coins table.",
            len(missing_coin_mapping),
        )

        logger.warning(
            "Unmapped API coin IDs: %s",
            missing_coin_mapping["id"].tolist(),
        )

    # Keep only coins that exist in the coins table.
    snapshot_df = snapshot_df[snapshot_df["coin_id"].notna()].copy()

    report_df = snapshot_df[
        [
            "coin_id",
            "snapshot_datetime",
            "current_price",
            "market_cap",
            "market_cap_rank",
            "total_volume",
            "high_24h",
            "low_24h",
            "price_change_24h",
            "price_change_percentage_24h",
            "market_cap_change_24h",
            "market_cap_change_percentage_24h",
            "circulating_supply",
            "total_supply",
        ]
    ].copy()

    report_df.columns = OUTPUT_COLUMNS

    logger.info(
        "Transformed %d snapshot records.",
        len(report_df),
    )

    return report_df


def load_snapshot_data(report_df, db_util):
    """
    Insert transformed snapshot records into the database.
    """
    if report_df.empty:
        logger.info("No snapshot records to insert.")
        return

    record_list = list(
        report_df.itertuples(
            index=False,
            name=None,
        )
    )

    CoinMarketSnapshots.insert_coin_market_snapshots_data(
        record_list,
        db_util,
    )

    logger.info(
        "Successfully inserted %d snapshot records.",
        len(record_list),
    )


def run_coin_snapshot_etl(
    db_util,
    storage,
    year,
    month,
    day,
    hour,
):
    """
    Execute the complete S3 → Transform → RDS pipeline.
    """
    logger.info(
        "Coin snapshot ETL started for " "%04d-%02d-%02d %02d:00.",
        year,
        month,
        day,
        hour,
    )

    # Extract
    data_obj = get_latest_snapshot(
        storage=storage,
        year=year,
        month=month,
        day=day,
        hour=hour,
    )

    # Load reference/master data
    coins_df = get_coins_mapping(db_util)

    # Transform
    report_df = transform_snapshot_data(
        data_obj=data_obj,
        coins_df=coins_df,
    )

    # Load
    load_snapshot_data(
        report_df=report_df,
        db_util=db_util,
    )

    logger.info("Coin snapshot ETL completed successfully.")


def main():
    logger.info("Coin snapshot ETL job started.")

    db_util = None

    try:
        db_util = RdsCryptoMarketDbUtil()

        storage = S3Storage(
            bucket_name=AWSConf.S3_RAW_STORAGE_BUCKET_NAME,
            profile_name=AWSConf.AWS_PROFILE_NAME,
        )

        run_coin_snapshot_etl(
            db_util=db_util,
            storage=storage,
            year=2026,
            month=8,
            day=20,
            hour=9,
        )

    except Exception:
        logger.exception("Coin snapshot ETL job failed.")
        raise

    finally:
        db_util.close()

        logger.info("Coin snapshot ETL job finished.")


if __name__ == "__main__":

    main()
