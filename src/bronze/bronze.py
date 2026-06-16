from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import nflreadpy as nfl
import polars as pl
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from src.utils import setup_logger

PLAYER_NAME = 'D.Maye'
TABLE_NAME = 'raw_maye_plays'
PERIOD = [2025]

COLUMNAS = [
# Id'S
    'game_id', 'play_id', 'season',
    'season_type','game_date', 'week',
    'home_team', 'away_team', 'defteam',
    'receiver_player_name',

    # Game situation
    'drive', 'qtr', 'down', 'yrdln', 'desc',

    # General
    'play_type', 'yards_gained', 'yards_after_catch',

    # advance metrics
    'epa', 'qb_epa', 'air_epa', 'yac_epa', 'xyac_epa',

    # Pase
    'pass_attempt', 'complete_pass', 'passing_yards', 'air_yards',
    'pass_touchdown', 'interception', 'sack', 'cpoe',
    'pass_location', 'td_team', 'td_player_name', 'pass_length',

    # QB
    'qb_hit', 'qb_scramble', 'qb_dropback',

    # Rush
    'rush_attempt', 'rushing_yards', 'rush_touchdown',

    # Fumbles & conv
    'fumble', 'fumble_forced', 'fumble_not_forced',
    'fumble_lost', 'fumble_out_of_bounds', 'two_point_conv_result',

    # Scoreboard
    'score_differential', 'posteam_score', 'defteam_score',

]

FLOAT_COLS = [
    'epa',
    'qb_epa',
    'air_epa',
    'yac_epa',
    'xyac_epa',
    'cpoe',
    'passing_yards',
    'rushing_yards',
    'yards_gained',
    'air_yards',
    'yards_after_catch',
]

INT_COLS = [
    'pass_attempt',
    'complete_pass',
    'pass_touchdown',
    'rush_attempt',
    'rush_touchdown',
    'interception',
    'sack',
    'fumble',
    'fumble_lost',
    'fumble_forced',
    'fumble_not_forced',
    'fumble_out_of_bounds',
    'score_differential',
    'posteam_score',
    'defteam_score',
    'qb_hit',
    'qb_scramble',
    'qb_dropback',
]


def get_recorded_plays(engine) -> set[str]:
    try:
        query = text(f"SELECT DISTINCT game_id, play_id FROM {TABLE_NAME}")
        with engine.connect() as conn:
            existing_df = pl.read_database(query, connection=conn)

            # retornamos la lista de IDs combinados
            return set(
                existing_df.select(
                    pl.concat_str(["game_id", "play_id"], separator="-")
                ).to_series().to_list()

            )
    except Exception:
        return set()


def filter_plays(df: pl.DataFrame, player: str) -> pl.DataFrame:
    return df.filter(
        (pl.col('passer_player_name') == player) |
        (pl.col('rusher_player_name') == player)
    ).unique(subset=['play_id', 'game_id'])


def clean_plays(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.select(COLUMNAS)
        .with_columns([
            pl.col(FLOAT_COLS).fill_null(0.0),
            pl.col(INT_COLS).fill_null(0),
            pl.col('td_player_name').fill_null(('No TD')),
            pl.lit(datetime.now(timezone.utc)).alias('bronze_loaded_at')
        ])
    )


def validate_plays(df: pl.DataFrame, logger: logging.Logger) -> bool:
    if df.is_empty():
        logger.warning('No new plays to insert')
        return False

    nulls = df.select(['game_id', 'play_id', 'epa']).null_count()
    total_nulls = nulls.to_pandas().values.sum()
    if total_nulls > 0:
        logger.warning(f'Nulls in critical columns:\n{nulls}')

    logger.info(f'New plays validated: {df.height}')
    return True


# Main ETL
def run_etl():
    load_dotenv()
    logger = setup_logger('etl_bronze')

    db_url = os.getenv('DB_URL')
    if not db_url:
        raise EnvironmentError('Falta DB_URL en .env')

    engine = create_engine(db_url)

    # 1. Existing IDs
    old_ids = get_recorded_plays(engine)
    logger.info(f'Existing records in bronze: {len(old_ids)}')

    # 2. Download
    logger.info(f'Downloading play_by_play {PERIOD}')
    df_raw = nfl.load_pbp(PERIOD)
    logger.info(f'Total plays downloaded: {df_raw.height}')

    # 3. Filter plays
    df_player = filter_plays(df_raw, PLAYER_NAME)
    logger.info(f'plays for {PLAYER_NAME}: {df_player.height}')

    # 4. Deduplicate
    df_new = (
        df_player
        .with_columns(
            pl.concat_str(['game_id', 'play_id'], separator='-').alias('_temp_id')
        )
        .filter(~pl.col('_temp_id').is_in(old_ids))
        .drop('_temp_id')
    )
    logger.info(f'New plays to insert: {df_new.height}')

    # 5. Clean
    df_clean = clean_plays(df_new)

    # 6. Validate
    if not validate_plays(df_clean, logger):
        return

    # 7. Insert

    df_clean.write_database(
        table_name=TABLE_NAME,
        connection=os.getenv('DB_URL'),
        if_table_exists='append',
    )

    logger.info(f'Bronze updated - {df_clean.height} plays inserted')


if __name__ == '__main__':
    run_etl()
