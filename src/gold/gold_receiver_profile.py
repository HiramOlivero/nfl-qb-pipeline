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


def build_receiver_overview(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('receiver_player_name').is_not_null())
        .filter(pl.col('down').is_not_null())
        .group_by('receiver_player_name')
        .agg([

            # Métricas avanzadas
            pl.col('epa').mean().round(2),
            pl.col('cpoe').mean().round(2),

            # Pase
            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('passing_yards').sum(),
            pl.col('air_yards').sum(),
            pl.col('yards_after_catch').sum(),

            pl.len().alias('n_targets'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),
            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
                .round(2).fill_nan(0.0).alias('completion_pct'),
            (pl.col('air_yards') / pl.col('pass_attempt'))
                .round(2).fill_nan(0.0).alias('air_yards_per_target'),
            (pl.col('yards_after_catch') / pl.col('complete_pass'))
                .round(2).fill_nan(0.0).alias('yac_per_reception'),
            (pl.col('passing_yards') / pl.col('complete_pass'))
                .round(2).fill_nan(0.0).alias('yards_per_reception'),
            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
        .sort('epa', descending=True)
    )


def build_receiver_by_down(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('receiver_player_name').is_not_null())
        .filter(pl.col('down').is_not_null())
        .group_by(['receiver_player_name', 'down'])
        .agg([
            pl.col('epa').mean().round(2),
            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('passing_yards').sum(),
            pl.col('air_yards').sum(),
            pl.len().alias('n_targets'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),
            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
                .round(2).fill_nan(0.0).alias('completion_pct'),
            (pl.col('air_yards') / pl.col('pass_attempt'))
                .round(2).fill_nan(0.0).alias('air_yards_per_target'),
            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
        .sort(['receiver_player_name', 'down'])
    )


def build_receiver_by_situation(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('receiver_player_name').is_not_null())
        .filter(pl.col('down').is_not_null())
        .with_columns([
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
        ])
        .group_by(['receiver_player_name', 'score_bucket'])
        .agg([
            pl.col('epa').mean().round(2),
            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('passing_yards').sum(),
            pl.len().alias('n_targets'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),
            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
                .round(2).fill_nan(0.0).alias('completion_pct'),
            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
        .sort(['receiver_player_name', 'score_bucket'])
    )


def build_receiver_redzone(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('receiver_player_name').is_not_null())
        .filter(pl.col('down').is_not_null())
        .filter(pl.col('is_redzone') == 1)
        .group_by('receiver_player_name')
        .agg([
            pl.col('epa').mean().round(2),
            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('passing_yards').sum(),
            pl.len().alias('n_targets'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),
            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
                .round(2).fill_nan(0.0).alias('completion_pct'),
            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
        .sort('pass_touchdown', descending=True)
    )


def run_gold():
    load_dotenv()
    logger = setup_logger('receiver_profile_gold')

    db_url = os.getenv('DB_URL')
    if not db_url:
        raise EnvironmentError('Missing DB_URL in env')

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

    logger.info('Building receiver tables')

    df_overview = build_receiver_overview(df_silver)
    df_by_down = build_receiver_by_down(df_silver)
    df_by_situation = build_receiver_by_situation(df_silver)
    df_redzone = build_receiver_redzone(df_silver)

    logger.info('Saving to postgres')

    df_overview.write_database(
        table_name='gold_receiver_overview',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )
    df_by_down.write_database(
        table_name='gold_receiver_by_down',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )
    df_by_situation.write_database(
        table_name='gold_receiver_by_situation',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )
    df_redzone.write_database(
        table_name='gold_receiver_redzone',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )

    logger.info('Gold finished — receiver profile tables processed')


if __name__ == '__main__':
    run_gold()