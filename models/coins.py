class Coins:
    TABLE_NAME = "crypto_market.coins"

    @classmethod
    def insert_coins_data(cls, data, rds_crypto_market_db_util):
        query = """
            INSERT INTO {table_name} (
                api_coin_id,
                symbol,
                name,
                image_url
            )    
            VALUES (%s, %s, %s, %s)
        """.format(table_name=cls.TABLE_NAME)
        rds_crypto_market_db_util.executemany(query, args=data, commit=True)
        return True
