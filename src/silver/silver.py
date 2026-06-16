from __future__ import annotations

import os
from datetime import datetime, timezone

import polars as pl
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.utils import setup_logger

EXPECTED_COLUMNS = [
    'game_id', 'play_id', 'season',
    'season_type', 'game_date',
    'week', 'home_team', 'away_team',
    'defteam', 'drive','qtr',
    'down', 'yrdln', 'desc',
    'play_type', 'yards_gained','epa',
    'qb_epa', 'air_epa', 'yac_epa',
    'xyac_epa','pass_attempt', 'complete_pass',
    'passing_yards', 'air_yards','pass_touchdown',
    'interception', 'sack', 'qb_hit',
    'qb_scramble', 'qb_dropback', 'cpoe',
    'pass_location','td_team', 'receiver_player_name',
    'td_player_name','rush_attempt', 'rushing_yards',
    'rush_touchdown','fumble', 'fumble_forced',
    'fumble_not_forced','fumble_lost', 'fumble_out_of_bounds',
    'two_point_conv_result','score_differential', 'posteam_score',
    'defteam_score','yards_after_catch', 'pass_length',
]

SCHEMA_CAST: dict[str, pl.DataType] = {
# Strings
    'game_id':               pl.Utf8,
    'season_type':           pl.Utf8,
    'home_team':             pl.Utf8,
    'away_team':             pl.Utf8,
    'defteam':               pl.Utf8,
    'yrdln':                 pl.Utf8,
    'desc':                  pl.Utf8,
    'play_type':             pl.Utf8,
    'pass_location':         pl.Utf8,
    'pass_length':           pl.Utf8,
    'td_team':               pl.Utf8,
    'receiver_player_name':  pl.Utf8,
    'td_player_name':        pl.Utf8,
    'two_point_conv_result': pl.Utf8,

    # Integers
    'play_id':          pl.Int32,
    'season':           pl.Int32,
    'week':             pl.Int32,
    'drive':            pl.Int32,
    'qtr':              pl.Int32,
    'down':             pl.Int32,
    'yards_gained':     pl.Int32,
    'passing_yards':    pl.Int32,
    'rushing_yards':    pl.Int32,
    'air_yards':        pl.Int32,
    'score_differential': pl.Int32,
    'posteam_score':    pl.Int32,
    'defteam_score':    pl.Int32,

    # Floats
    'epa':              pl.Float64,
    'qb_epa':           pl.Float64,
    'air_epa':          pl.Float64,
    'yac_epa':          pl.Float64,
    'xyac_epa':         pl.Float64,
    'cpoe':             pl.Float64,
    'yards_after_catch': pl.Float64,

    # Flags
    'pass_attempt':        pl.Int8,
    'complete_pass':       pl.Int8,
    'pass_touchdown':      pl.Int8,
    'interception':        pl.Int8,
    'sack':                pl.Int8,
    'qb_hit':              pl.Int8,
    'qb_scramble':         pl.Int8,
    'qb_dropback':         pl.Int8,
    'rush_attempt':        pl.Int8,
    'rush_touchdown':      pl.Int8,
    'fumble':              pl.Int8,
    'fumble_forced':       pl.Int8,
    'fumble_not_forced':   pl.Int8,
    'fumble_lost':         pl.Int8,
    'fumble_out_of_bounds': pl.Int8,
}

# Helper functions
def assert_expected_columns(df: pl.DataFrame, expected: list[str]) -> None:
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f'Bronze missing expected columns: {missing}')


def enforce_schema(df: pl.DataFrame, schema: dict[str, pl.DataType]) -> pl.DataFrame:
    exprs = []
    for col, dtype in schema.items():
        if col in df.columns:
            exprs.append(pl.col(col).cast(dtype, strict=False).alias(col))
    return df.with_columns(exprs)


def add_features(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns([
        # Success by EPA
        pl.when(pl.col('epa') > 0)
            .then(1)
            .otherwise(0)
            .cast(pl.Int8)
            .alias('is_success'),

        # Redzone (yard_line <= 20 in opponent territory)
        pl.when(
            (pl.col('yard_line').str.extract(r'([A-Za-z]+)') == pl.col('opponent_team')) &
            (pl.col('yard_line').str.extract(r'(\d+)').cast(pl.Int32, strict=False) <= 20)
        )
            .then(1)
            .otherwise(0)
            .cast(pl.Int8)
            .alias('is_redzone'),

        # Two point conversion result
        pl.when(pl.col('play_description').str.contains('TWO-POINT CONVERSION SUCCEEDS', literal=False))
            .then(pl.lit('success'))
            .when(pl.col('play_description').str.contains('ATTEMPT FAILS', literal=False))
            .then(pl.lit('failure'))
            .otherwise(pl.lit(None))
            .alias('two_point_conv_result'),

        # Load timestamp
        pl.lit(datetime.now(timezone.utc)).alias('silver_loaded_at'),
    ])


# ── Main pipeline ─────────────────────────────────────────────────────────────
def run_silver():
    load_dotenv()
    logger = setup_logger('etl_silver')

    db_url = os.getenv('DB_URL')
    if not db_url:
        raise EnvironmentError('Missing DB_URL in .env')

    engine = create_engine(db_url)

    logger.info('Reading bronze data')
    select_cols = ', '.join([
        f'"{col}"' for col in EXPECTED_COLUMNS
        if col != 'two_point_conv_result'
    ])

    df_bronze = pl.read_database(
        f'SELECT {select_cols} FROM raw_maye_plays',
        connection=engine
    )

    if df_bronze.is_empty():
        logger.warning('Bronze is empty, nothing to process')
        return

    logger.info('Validating expected columns')
    assert_expected_columns(df_bronze, EXPECTED_COLUMNS)

    logger.info('Enforcing schema')
    df = enforce_schema(df_bronze, SCHEMA_CAST)

    logger.info('Renaming columns')
    df = df.rename({
        'defteam':           'opponent_team',
        'qtr':               'quarter',
        'yrdln':             'yard_line',
        'desc':              'play_description',
        'score_differential': 'score_diff',
        'posteam_score':     'own_score',
        'defteam_score':     'opp_score',
    })

    logger.info('Removing duplicates')
    df = df.unique(subset=['game_id', 'play_id'], keep='last')

    logger.info('Adding features')
    df_silver = add_features(df)

    logger.info('Saving to postgres')
    df_silver.write_database(
        table_name='silver_maye_plays',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )

    logger.info('Silver pipeline completed successfully')

if __name__ == '__main__':
    run_silver()

