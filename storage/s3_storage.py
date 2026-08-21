import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class S3StorageError(Exception):
    """Raised when an S3 storage operation fails."""


class S3Storage:
    """
    Handles storage of raw pipeline data in Amazon S3.

    The class is intentionally independent of the data source.
    It only knows how to construct S3 keys and upload objects.
    """

    def __init__(
        self,
        bucket_name: str,
        profile_name: str | None = None,
        region_name: str = "ap-south-1",
        base_prefix: str = "raw/market",
    ) -> None:
        self.bucket_name = bucket_name
        self.base_prefix = base_prefix.rstrip("/")
        self.region_name = region_name

        if profile_name:
            session = boto3.Session(
                profile_name=profile_name,
                region_name=region_name,
            )
        else:
            session = boto3.Session(
                region_name=region_name,
            )

        self.s3_client = session.client("s3")

    def build_object_key(
        self,
        ingestion_time: datetime,
        filename: str,
    ) -> str:
        """
        Build a partitioned S3 object key using UTC ingestion time.

        Example:
        raw/market/year=2026/month=08/day=20/hour=13/market_20260820_135000.json
        """

        if ingestion_time.tzinfo is None:
            raise ValueError("ingestion_time must be timezone-aware.")

        ingestion_time = ingestion_time.astimezone(timezone.utc)

        return (
            f"{self.base_prefix}/"
            f"year={ingestion_time:%Y}/"
            f"month={ingestion_time:%m}/"
            f"day={ingestion_time:%d}/"
            f"hour={ingestion_time:%H}/"
            f"{filename}"
        )

    def upload_json(
        self,
        data: Any,
        object_key: str,
    ) -> str:
        """
        Upload JSON-serializable data to S3.

        Returns:
            Full S3 URI of the uploaded object.
        """

        try:
            payload = json.dumps(
                data,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=payload,
                ContentType="application/json",
            )

            s3_uri = f"s3://{self.bucket_name}/{object_key}"

            logger.info(
                "Successfully uploaded object to %s",
                s3_uri,
            )

            return s3_uri

        except (ClientError, BotoCoreError) as exc:
            logger.exception(
                "Failed to upload object to s3://%s/%s",
                self.bucket_name,
                object_key,
            )
            raise S3StorageError(
                f"Failed to upload object to S3: {object_key}"
            ) from exc

    def list_objects_for_hour(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
    ) -> list[dict[str, Any]]:
        """List raw market objects stored for a specific UTC hour."""

        prefix = (
            f"{self.base_prefix}/"
            f"year={year:04d}/"
            f"month={month:02d}/"
            f"day={day:02d}/"
            f"hour={hour:02d}/"
        )

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
            )

            return response.get("Contents", [])

        except (ClientError, BotoCoreError) as exc:
            logger.exception(
                "Failed to list S3 objects for prefix: %s",
                prefix,
            )
            raise S3StorageError(f"Failed to list S3 objects: {prefix}") from exc

    def get_latest_object_for_hour(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
    ) -> Optional[dict[str, Any]]:
        """
        Return the latest raw market JSON object for a specific UTC hour.
        """

        objects = self.list_objects_for_hour(
            year=year,
            month=month,
            day=day,
            hour=hour,
        )

        if not objects:
            logger.info(
                "No raw objects found for %04d-%02d-%02d %02d:00 UTC",
                year,
                month,
                day,
                hour,
            )
            return None

        latest_object = max(
            objects,
            key=lambda obj: obj["LastModified"],
        )

        logger.info(
            "Latest raw object: s3://%s/%s",
            self.bucket_name,
            latest_object["Key"],
        )

        return latest_object

    def get_json_object(self, object_key: str) -> Any:
        """Download and deserialize a JSON object from S3."""

        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )

            body = response["Body"].read()

            return json.loads(body)

        except (ClientError, BotoCoreError, json.JSONDecodeError) as exc:
            logger.exception(
                "Failed to read JSON object: s3://%s/%s",
                self.bucket_name,
                object_key,
            )
            raise S3StorageError(f"Failed to read JSON object: {object_key}") from exc
