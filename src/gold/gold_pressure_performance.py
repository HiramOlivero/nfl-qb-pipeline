from __future__ import annotations

import os
from datetime import datetime, timezone

import polars as pl
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.utils import setup_logger, OFFICIAL_PASS, PRESSURE_TYPE

QB_NAME = 'D.Maye'
TEAM = 'NE'
SEASON = 2025


def build_pressure_overview(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('down').is_not_null())
        .with_columns([PRESSURE_TYPE])

        .group_by('pressure_type')
        .agg([

            pl.col('epa').mean().round(2),
            pl.col('cpoe').mean().round(2),
            pl.col('yards_gained').mean().round(2).alias('avg_yards_gained'),


            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('interception').sum(),
            pl.col('passing_yards').sum(),
            pl.col('air_yards').sum(),
            pl.col('yards_after_catch').sum(),

            pl.col('rush_attempt').sum(),
            pl.col('rushing_yards').sum(),
            pl.col('rush_touchdown').sum(),

            pl.col('qb_dropback').sum().alias('total_dropbacks'),
            pl.col('qb_scramble').sum(),
            pl.col('sack').sum(),

            pl.len().alias('n_plays'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),

            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
            .round(2).fill_nan(0.0).alias('completion_pct'),

            (pl.col('passing_yards')/ pl.col('pass_attempt'))
            .round(2).fill_nan(0.0).alias('yards_per_attempt'),

            (pl.col('air_yards') / pl.col('pass_attempt'))
            .round(2).fill_nan(0.0).alias('air_yards_per_attempt'),

            (pl.col('rushing_yards') / pl.col('rush_attempt'))
            .round(2).fill_nan(0.0).alias('yards_per_carry'),

            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),


        ])
    )


def build_pressure_by_down(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('down').is_not_null())

        .with_columns([PRESSURE_TYPE])

        .group_by(['pressure_type', 'down'])
        .agg([

            pl.col('epa').mean().round(2),
            pl.col('cpoe').mean().round(2),
            pl.col('yards_gained').mean().round(2).alias('avg_yards_gained'),

            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('interception').sum(),
            pl.col('passing_yards').sum(),
            pl.col('air_yards').sum(),
            pl.col('yards_after_catch').sum(),

            pl.col('rush_attempt').sum(),
            pl.col('rushing_yards').sum(),
            pl.col('rush_touchdown').sum(),

            pl.col('qb_dropback').sum().alias('total_dropbacks'),
            pl.col('qb_scramble').sum(),
            pl.col('sack').sum(),

            pl.len().alias('n_plays'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),

            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
            .round(2).fill_nan(0.0).alias('completion_pct'),

            (pl.col('rushing_yards') / pl.col('rush_attempt'))
            .round(2).fill_nan(0.0).alias('yards_per_carry'),

            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
        .sort(['down', 'pressure_type'])
    )


def build_pressure_by_quarter(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('down').is_not_null())

        .with_columns([PRESSURE_TYPE])

        .group_by(['pressure_type', 'quarter'])
        .agg([


            pl.col('epa').mean().round(2),
            pl.col('cpoe').mean().round(2),


            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('interception').sum(),
            pl.col('passing_yards').sum(),


            pl.col('rush_attempt').sum(),
            pl.col('rushing_yards').sum(),
            pl.col('rush_touchdown').sum(),

            pl.col('qb_dropback').sum().alias('total_dropbacks'),
            pl.col('qb_scramble').sum(),
            pl.col('sack').sum(),


            pl.len().alias('n_plays'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),

            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
            .round(2).fill_nan(0.0).alias('completion_pct'),

            (pl.col('rushing_yards') / pl.col('rush_attempt'))
            .round(2).fill_nan(0.0).alias('yards_per_carry'),


            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
        .sort(['quarter', 'pressure_type'])
    )


def build_pressure_by_opponent(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('down').is_not_null())

        .with_columns([PRESSURE_TYPE])

        .group_by(['game_id', 'pressure_type', 'opponent_team'])
        .agg([

            pl.col('week').first(),

            pl.col('epa').mean().round(2),
            pl.col('cpoe').mean().round(2),


            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('interception').sum(),
            pl.col('passing_yards').sum(),
            pl.col('air_yards').sum(),
            pl.col('yards_after_catch').sum(),

            pl.col('rush_attempt').sum(),
            pl.col('rushing_yards').sum(),
            pl.col('rush_touchdown').sum(),


            pl.col('qb_dropback').sum().alias('total_dropbacks'),
            pl.col('qb_scramble').sum(),
            pl.col('sack').sum(),

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
        .sort(['week', 'opponent_team', 'pressure_type'])
    )


def build_pressure_air_yards(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('down').is_not_null())
        .filter(pl.col('pass_attempt') == 1)

        .with_columns([PRESSURE_TYPE])

        .group_by('pressure_type')
        .agg([

            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('air_yards').mean().round(2).alias('avg_air_yards'),

            pl.col('yards_after_catch').mean().round(2).alias('avg_yac'),

            pl.col('qb_dropback').sum().alias('total_dropbacks'),

            pl.len().alias('n_plays'),
        ])
        .with_columns([
            pl.lit(QB_NAME).alias('player_name'),

            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),
        ])
    )


def run_gold():
    load_dotenv()
    logger = setup_logger('pressure_performance_gold')

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

    logger.info('Building pressure tables')

    df_overview = build_pressure_overview(df_silver)
    df_by_down = build_pressure_by_down(df_silver)
    df_by_quarter = build_pressure_by_quarter(df_silver)
    df_by_opponent = build_pressure_by_opponent(df_silver)
    df_air_yards = build_pressure_air_yards(df_silver)

    logger.info('Saving to postgres')

    df_overview.write_database(
        table_name='gold_pressure_overview',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )
    df_by_down.write_database(
        table_name='gold_pressure_by_down',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )
    df_by_quarter.write_database(
        table_name='gold_pressure_by_quarter',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )
    df_by_opponent.write_database(
        table_name='gold_pressure_by_opponent',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )
    df_air_yards.write_database(
        table_name='gold_pressure_air_yards',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )

    logger.info(f'Gold finished - pressure tables processed')


if __name__ == '__main__':
    run_gold()
