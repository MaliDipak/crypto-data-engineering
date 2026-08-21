import logging
from typing import Any, List, Optional

import pandas as pd


class DatabaseUtil:
    def __init__(
        self,
        dbname: str,
        credentials: dict,
        connect_fn: Any,
        cursor_param: dict,
        connect: bool = True,
    ):
        """
        Initializes a DatabaseUtil instance.

        Args:
            dbname (str): Name of the database.
            credentials (dict): Database connection credentials.
            connect_fn (callable): Function for establishing a database connection.
            cursor_param (dict): Parameters for configuring the database cursor.
            connect (bool): Flag indicating whether to establish a connection during initialization.

        Returns:
            None
        """
        self.dbname = dbname
        self.__credentials = credentials
        self.__connect_fn = connect_fn
        self.__cursor_param = cursor_param
        self.logger = logging.getLogger(f"{self.dbname}")
        if connect:
            self.connect()

    def connect(self) -> None:
        """
        Establishes a connection to the database.

        Returns:
            None
        """
        try:
            self.conn = self.__connect_fn(**self.__credentials)
            self.cursor = self.conn.cursor(**self.__cursor_param)
            msg = f"Connected to {self.dbname} server"
            self.logger.info(msg)
        except Exception as e:
            msg = f"Error connecting to {self.dbname} server"
            self.logger.error(msg, e)
            raise e

    def is_table(self, db: str, table: str) -> bool:
        """
        Checks if a table exists in the database.

        Args:
            db (str): Name of the database.
            table (str): Name of the table.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        query = f"""
                    SELECT
                        EXISTS(
                            SELECT
                                1
                            FROM
                                information_schema.tables
                            WHERE
                                table_catalog = '{db}'
                                AND table_schema = 'public'
                                AND table_name = '{table}'
                        );
            """
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def drop_table(self, table: str) -> bool:
        """
        Drops a table if it exists.

        Args:
            table (str): Name of the table.

        Returns:
            bool: True if the table is dropped successfully, False otherwise.
        """
        query = f"DROP TABLE IF EXISTS {table};"
        try:
            self.execute(query, log_query=True, commit=True)
            return True
        except Exception as e:
            self.logger.error(e)
            raise e

    def execute(
        self,
        query: str,
        args: Optional[Any] = None,
        log_query: bool = False,
        commit: bool = False,
    ) -> bool:
        """
        Executes a SQL query.

        Args:
            query (str): SQL query to execute.
            args (Optional[Any]): Parameters for the SQL query.
            log_query (bool): Flag indicating whether to log the query.
            commit (bool): Flag indicating whether to commit the transaction.

        Returns:
            bool: True if the query is executed successfully, False otherwise.
        """
        if log_query:
            self.logger.info(query)
        try:
            if args is not None:
                self.cursor.execute(query, args)
            else:
                self.cursor.execute(query)
            if commit:
                self.commit()
            return True
        except Exception as e:
            if commit:
                self.rollback()
            self.logger.error(e)
            raise e

    def fetchall(self, query: str, log_query: bool = False) -> List[Any]:
        """
        Fetches all rows from a query result.

        Args:
            query (str): SQL query to execute.
            log_query (bool): Flag indicating whether to log the query.

        Returns:
            List[Any]: List of tuples representing the query result.
        """
        if log_query:
            self.logger.info(query)
        try:
            self.cursor.execute(query)
            result_set = self.cursor.fetchall()
            return result_set
        except Exception as e:
            self.logger.error(e)
            raise e

    def executemany(
        self,
        query: str,
        args: List[Any],
        batch_size: int = 10000,
        log_query: bool = False,
        commit: bool = True,
    ) -> bool:
        """
        Executes a SQL query with multiple sets of parameters.

        Args:
            query (str): SQL query to execute.
            args (List[Any]): List of parameter sets.
            batch_size (int): Number of parameter sets to execute in each batch.
            log_query (bool): Flag indicating whether to log the query.
            commit (bool): Flag indicating whether to commit the transaction.

        Returns:
            bool: True if the query is executed successfully, False otherwise.
        """
        if log_query:
            self.logger.info(query)
        try:
            if len(args) > 0:
                self.logger.info(
                    "Inserting {data_size} rows with batch size {batch_size}".format(
                        data_size=len(args), batch_size=batch_size
                    )
                )
                for i in range(0, len(args), batch_size):
                    commit_buffer = args[i : i + batch_size]
                    self.cursor.executemany(query, commit_buffer)
            else:
                self.logger.info("No data to insert")
            if commit:
                self.commit()
            return True
        except Exception as e:
            self.rollback()
            self.logger.error(e)
            raise e

    def fetchall_df(self, query: str, log_query: bool = False) -> pd.DataFrame:
        """
        Fetches all rows from a query result and returns a pandas DataFrame.

        Args:
            query (str): SQL query to execute.
            log_query (bool): Flag indicating whether to log the query.

        Returns:
            pd.DataFrame: DataFrame representing the query result.
        """
        if log_query:
            self.logger.info(query)
        try:
            df = pd.read_sql_query(query, self.conn)  # type: ignore
            return df
        except Exception as e:
            self.logger.error(e)
            raise e

    def rollback(self) -> None:
        """
        Rolls back all uncommitted transactions.
        """
        self.conn.rollback()
        msg = f"Rolled back all uncommitted transactions to {self.dbname} server"
        self.logger.info(msg)

    def commit(self) -> None:
        """
        Commits transactions.
        """
        self.conn.commit()
        msg = f"Committed transactions to {self.dbname} server"
        self.logger.info(msg)

    def close(self) -> None:
        """
        Closes the database connection.
        """
        self.conn.close()
        msg = f"Closed connection to {self.dbname} server"
        self.logger.info(msg)

    def get_logger(self) -> logging.Logger:
        """
        Getter for the logger object

        Returns:
            logging.Logger: Instance logger object
        """
        return self.logger
