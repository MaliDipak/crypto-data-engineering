CREATE DATABASE IF NOT EXISTS crypto_market;
USE crypto_market;


CREATE TABLE IF NOT EXISTS coins (
  coin_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  api_coin_id VARCHAR(50) NOT NULL UNIQUE,
  symbol VARCHAR(20) NOT NULL,
  name VARCHAR(100) NOT NULL,
  image_url VARCHAR(500),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS coin_market_snapshots (
  snapshot_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  coin_id BIGINT NOT NULL,
  snapshot_datetime DATETIME NOT NULL,
  current_price_usd DECIMAL(20, 8) NOT NULL,
  market_cap_usd DECIMAL(25, 2) NOT NULL,
  market_cap_rank INT NOT NULL,
  total_volume_usd DECIMAL(25, 2) NOT NULL,
  high_24h_usd DECIMAL(20, 8),
  low_24h_usd DECIMAL(20, 8),
  price_change_24h_usd DECIMAL(20, 8),
  price_change_24h_pct DECIMAL(10, 4),
  market_cap_change_24h_usd DECIMAL(25, 2),
  market_cap_change_24h_pct DECIMAL(10, 4),
  circulating_supply DECIMAL(30, 8),
  total_supply DECIMAL(30, 8),
  FOREIGN KEY (coin_id) REFERENCES coins (coin_id),
  UNIQUE (coin_id, snapshot_datetime)
);

CREATE INDEX idx_market_snapshot_datetime ON coin_market_snapshots (snapshot_datetime);

CREATE INDEX idx_market_snapshot_coin ON coin_market_snapshots (coin_id);