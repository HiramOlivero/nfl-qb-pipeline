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

# Build function
def build_qb_performance(df: pl.DataFrame) -> pl.DataFrame:
    df_gold = (
        df.group_by('game_id').agg([

        # Game context
        pl.col('season').first(),
        pl.col('week').first(),
        pl.col('season_type').first(),
        pl.col('home_team').first(),
        pl.col('away_team').first(),
        pl.col('opponent_team').first(),

        # Sums
        pl.col('pass_attempt')
        .filter(OFFICIAL_PASS)
        .sum()
        .alias('pass_attempt'),

        pl.col('complete_pass')
        .filter(OFFICIAL_PASS)
        .sum()
        .alias('complete_pass'),

        pl.col('passing_yards')
        .filter(OFFICIAL_PASS)
        .sum()
        .alias('passing_yards'),

        pl.col('rushing_yards').sum(),
        pl.col('rush_touchdown').sum(),
        pl.col('pass_touchdown').sum(),
        pl.col('interception').sum(),

        pl.col('sack').sum(),
        pl.col('rush_attempt').sum(),
        pl.col('fumble').sum(),
        pl.col('fumble_lost').sum(),
        pl.col('air_yards').sum(),
        pl.col('fumble_forced').sum(),
        pl.col('fumble_not_forced').sum(),

        # Averages
        pl.col('epa').mean().round(2),
        pl.col('cpoe').mean().round(2),

    ]).with_columns([
        # Paser rating components
        ((pl.col('complete_pass') / pl.col('pass_attempt') - 0.3) * 5)
        .clip(0, 2.375).alias('_a'),

        ((pl.col('passing_yards') / pl.col('pass_attempt') - 3) * 0.25)
        .clip(0, 2.375).alias('_b'),

        ((pl.col('pass_touchdown') / pl.col('pass_attempt')) * 20)
        .clip(0, 2.375).alias('_c'),

        (2.375 - (pl.col('interception') / pl.col('pass_attempt')) * 25)
        .clip(0, 2.375).alias('_d'),

    ]).with_columns([
            # passer rating
        ((pl.col('_a') + pl.col('_b') + pl.col('_c') + pl.col('_d')) / 6 * 100)
        .round(1).alias('passer_rating'),

    ]).with_columns([
            # Calculated columns
        pl.lit(QB_NAME).alias('player_name'),
        pl.lit(TEAM).alias('team'),

        (pl.col('complete_pass') / pl.col('pass_attempt') * 100)
        .round(2)
        .alias('completion_pct'),

        (pl.col('passing_yards') / pl.col('pass_attempt'))
        .round(2)
        .alias('yards_per_attempt'),

        (pl.col('passing_yards') + pl.col('rushing_yards')).alias('total_yards'),

        pl.when(pl.col('home_team') == TEAM)
        .then(pl.lit('Home'))
        .otherwise(pl.lit('Away'))
        .alias('home_or_away'),

        pl.lit(datetime.now(timezone.utc)).alias('gold_loaded_at'),

    ]).drop(['_a', '_b', '_c', '_d']).sort('week'))

    df_gold = df_gold.select([

        # Id's
        'game_id',
        'player_name',
        'team',

        # Game context
        'season',
        'week',
        'season_type',
        'home_team',
        'away_team',
        'opponent_team',
        'home_or_away',

        # yards
        'passing_yards',
        'rushing_yards',
        'total_yards',

        # Passing
        'pass_attempt',
        'complete_pass',
        'completion_pct',
        'air_yards',

        # Touchdowns & interceptions
        'pass_touchdown',
        'rush_touchdown',
        'interception',

        # Pressure
        'sack',
        'fumble',
        'fumble_forced',
        'fumble_not_forced',
        'fumble_lost',

        # Advanced metrics
        'epa',
        'cpoe',
        'passer_rating',
        'yards_per_attempt',

        # Audit
        'gold_loaded_at',

    ])

    return df_gold

# Main pipeline
def run_gold():
    load_dotenv()
    logger = setup_logger('performance_gold')

    db_url = os.getenv("DB_URL")
    if not db_url:
        raise EnvironmentError("Missing DB_URL in env")

    engine = create_engine(db_url)
    logger.info('Reading silver layer')
    df_silver = pl.read_database(
        "SELECT * FROM silver_maye_plays",
        connection=engine,
        infer_schema_length=None

    )

    if df_silver.is_empty():
        logger.warning('Silver is empty, nothing to process')
        return

    df_qb = build_qb_performance(df_silver)

    logger.info('saving to postgres')
    df_qb.write_database(
        table_name='gold_qb_performance',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )

    logger.info(f'Gold finished - {df_qb.height} games processed')


if __name__ == '__main__':
    run_gold()
