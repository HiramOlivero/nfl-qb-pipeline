from __future__ import annotations

import os

import polars as pl
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.utils import setup_logger

QB_NAME = 'D.Maye'
TEAM = 'NE'
SEASON = 2025


def build_game_momentum(df: pl.DataFrame) -> pl.DataFrame:
    return (
    df
    .sort('week')
    .with_columns([
        pl.col('epa').rolling_mean(window_size=4, min_samples=1).round(2).alias('epa_rolling4'),
        pl.col('cpoe').rolling_mean(window_size=4, min_samples=1).round(2).alias('cpoe_rolling4'),
        pl.col('complete_pass').rolling_mean(window_size=4, min_samples=1).round(2).alias('complete_pass_rolling4'),

        pl.col('completion_pct').rolling_mean(window_size=4, min_samples=1).round(2).alias('completion_pct_rolling4'),
        pl.col('pass_touchdown').rolling_mean(window_size=4, min_samples=1).round(2).alias('pass_touchdown_rolling4'),
        pl.col('passer_rating').rolling_mean(window_size=4, min_samples=1).round(2).alias('passer_rating_rolling4'),

        pl.col('yards_per_attempt').rolling_mean(window_size=4, min_samples=1).round(2).alias('yards_per_attempt_rolling4'),
        pl.col('interception').rolling_mean(window_size=4, min_samples=1).round(2).alias('interception_rolling4'),
        pl.col('rushing_yards').rolling_mean(window_size=4, min_samples=1).round(2).alias('rushing_yards_rolling4'),

        pl.col('rush_touchdown').rolling_mean(window_size=4, min_samples=1).round(2).alias('rush_touchdown_rolling4'),
        pl.col('sack').rolling_mean(window_size=4, min_samples=1).round(2).alias('sack_rolling4'),
        pl.col('fumble').rolling_mean(window_size=4, min_samples=1).round(2).alias('fumble_rolling4'),
    ])
    .select([
        #Id's
        'game_id',
        'week',
        'opponent_team',
        'home_or_away',

        # Game metrics
        'epa',
        'passer_rating',
        'completion_pct',
        'passing_yards',
        'rushing_yards',
        'pass_touchdown',
        'rush_touchdown',
        'interception',
        'sack',

        # Rolling averages
        'epa_rolling4',
        'passer_rating_rolling4',
        'completion_pct_rolling4',
        'rushing_yards_rolling4',
        'pass_touchdown_rolling4',
        'rush_touchdown_rolling4',
        'interception_rolling4',
        'sack_rolling4',

        # Audit
        'gold_loaded_at'

    ])

    )


def run_gold():
    load_dotenv()
    logger = setup_logger('game_momentum_gold')

    db_url = os.getenv('DB_URL')
    if not db_url:
        raise EnvironmentError('Missing DB_URL in env')

    engine = create_engine(db_url)
    logger.info('reading gold_qb_performance')
    df_gold_qb_performance = pl.read_database(
        'SELECT * FROM gold_qb_performance',
        connection=engine,
        infer_schema_length=None
    )

    if df_gold_qb_performance.is_empty():
        logger.warning('gold_qb_performance is empty, nothing to process')
        return

    df_gm = build_game_momentum(df_gold_qb_performance)

    logger.info('saving to postgres')
    df_gm.write_database(
        table_name='gold_game_momentum',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )

    logger.info(f'Gold finished {df_gm.height} games processed')


if __name__ == '__main__':
    run_gold()
