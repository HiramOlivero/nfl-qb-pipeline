from __future__ import annotations

import os
from datetime import datetime, timezone

import polars as pl
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.utils import setup_logger, OFFICIAL_PASS

QB_NAME = 'D.Maye'
TEAM = 'NE'
SEASON = 2025

def build_situational_splits(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('down').is_not_null())
        .with_columns([
            # Score bucket
            pl.when(pl.col('score_diff') <= -14)
                .then(pl.lit('Losing big'))
            .when(pl.col('score_diff') < 0)
                .then(pl.lit('Losing'))
            .when(pl.col('score_diff') == 0)
                .then(pl.lit('Tied'))
            .when(pl.col('score_diff') <= 14)
                .then(pl.lit('Winning'))
            .otherwise(pl.lit('Winning big'))
            .alias('score_bucket'),

            # Home or away
            pl.when(pl.col('home_team') == TEAM)
                .then(pl.lit('Home'))
                .otherwise(pl.lit('Away'))
            .alias('home_or_away'),
        ])
        .group_by(['down', 'score_bucket', 'quarter', 'home_or_away'])
        .agg([
            # Advanced metrics
            pl.col('epa').mean().round(2),

            # Passing
            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('passing_yards').filter(OFFICIAL_PASS).sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('interception').sum(),
            pl.col('sack').sum(),

            # Rushing
            pl.col('rush_attempt').sum(),
            pl.col('rushing_yards').sum(),
            pl.col('rush_touchdown').sum(),

            pl.len().alias('n_plays'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),
            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
                .round(2).fill_nan(0.0).alias('completion_pct'),
            (pl.col('passing_yards') / pl.col('pass_attempt'))
                .round(2).fill_nan(0.0).alias('yards_per_attempt'),
            (pl.col('rushing_yards') / pl.col('rush_attempt'))
                .round(2).fill_nan(0.0).alias('yards_per_carry'),
            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
    )



def run_gold():
    load_dotenv()
    logger = setup_logger('situational_splits_gold')

    db_url = os.getenv('DB_URL')
    if not db_url:
        raise EnvironmentError('Missing DB_URL in .env')

    engine = create_engine(db_url)

    logger.info('Reading silver layer')
    df_silver = pl.read_database(
        'SELECT * FROM silver_maye_plays',
        connection=engine,
        infer_schema_length=None
    )

    if df_silver.is_empty():
        logger.warning('Silver is empty, nothing to process')
        return

    df_splits = build_situational_splits(df_silver)

    logger.info('Saving to postgres')
    df_splits.write_database(
        table_name='gold_situational_splits',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )

    logger.info(f'Gold finished — {df_splits.height} situational combinations processed')

if __name__ == '__main__':
    run_gold()
