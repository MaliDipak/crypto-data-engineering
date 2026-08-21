class CoinMarketSnapshots:
    TABLE_NAME = "crypto_market.coin_market_snapshots"

    @classmethod
    def insert_coin_market_snapshots_data(cls, data, rds_crypto_market_db_util):
        query = """
            INSERT INTO {table_name} (
                coin_id,
                snapshot_datetime,
                current_price_usd,
                market_cap_usd,
                market_cap_rank,
                total_volume_usd,
                high_24h_usd,
                low_24h_usd,
                price_change_24h_usd,
                price_change_24h_pct,
                market_cap_change_24h_usd,
                market_cap_change_24h_pct,
                circulating_supply,
                total_supply
            )    
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """.format(table_name=cls.TABLE_NAME)
        rds_crypto_market_db_util.executemany(query, args=data, commit=True)
        return True
