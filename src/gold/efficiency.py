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


def build_efficiency_gold(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .filter(pl.col('pass_attempt') == 1)
        .filter(pl.col('pass_length').is_not_null())

        .group_by(['game_id', 'pass_length', 'pass_location'])
        .agg([
            pl.col('pass_attempt').filter(OFFICIAL_PASS).sum(),
            pl.col('complete_pass').sum(),
            pl.col('air_yards').sum(),
            pl.col('yards_after_catch').sum(),
            pl.col('pass_touchdown').sum(),
            pl.col('interception').sum(),
            pl.col('epa').mean().round(2),
            pl.col('cpoe').mean().round(2),
            pl.len().alias('n_plays')
        ])
        .with_columns([
            (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
            .round(2)
            .fill_nan(0.0)
            .alias('completion_pct'),

            (pl.col('air_yards') / pl.col('pass_attempt'))
            .round(2)
            .fill_nan(0.0)
            .alias('air_yards_per_attempt'),

            (pl.col('yards_after_catch') / pl.col('complete_pass'))
            .round(2)
            .fill_nan(0.0)
            .alias('yac_per_reception'),

            pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at')

        ]) .sort('game_id')
    )


def run_gold():
    load_dotenv()
    logger = setup_logger("gold_efficiency_profile")

    db_url = os.getenv("DB_URL")
    if not db_url:
        raise EnvironmentError("Missing DB_URL in env")

    engine = create_engine(db_url)
    logger.info('reading silver layer')

    df_silver = pl.read_database(
        "SELECT * FROM silver_maye_plays",
        connection=engine,
        infer_schema_length=None
    )

    if df_silver.is_empty():
        logger.warning('Silver is empty, nothing to process')
        return

    df_efficiency = build_efficiency_gold(df_silver)

    logger.info('Saving to postgres')
    df_efficiency.write_database(
        table_name="gold_efficiency_profile",
        connection=os.getenv("DB_URL"),
        if_table_exists="replace",

    )

    logger.info(f' Gold finished - {df_efficiency.height} passing style combinations processed')


if __name__ == "__main__":
    run_gold()
