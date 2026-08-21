from typing import Any, Dict

from pymysql import connect
from pymysql.cursors import DictCursor

from config.config import DBConf
from database.database_util import DatabaseUtil


class RdsCryptoMarketDbUtil(DatabaseUtil):
    def __init__(self) -> None:
        """
        Initializes an AWS RdsUtil instance.

        Args:
            is_read (bool): Indicates whether the connection is for read-only purposes. Default is True.
        """

        credentials: Dict[str, Any] = DBConf.get_credentials(
            "DEV_CRYPTO_MARKET_DB_WRITE"
        )
        cursor_param: Dict[str, Any] = {"cursor": DictCursor}
        super().__init__("AWS RDS crypto_market DB", credentials, connect, cursor_param)
