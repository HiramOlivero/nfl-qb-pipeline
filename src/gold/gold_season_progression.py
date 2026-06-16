from utils import setup_logger
import os
import polars as pl
from sqlalchemy import create_engine
from dotenv import load_dotenv


def build_season_progression(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df
        .sort('week')
        .select([
            'game_id',
            'player_name',
            'week',
            'season_type',
            'opponent_team',
            'home_or_away',

            # Advance metrics
            'epa',
            'cpoe',
            'passer_rating',
            'yards_per_attempt',

            # Pass
            'pass_attempt',
            'complete_pass',
            'completion_pct',
            'passing_yards',
            'pass_touchdown',
            'interception',
            'air_yards',
            'sack',

            # Rush
            'rushing_yards',
            'rush_touchdown',

            # Audit
            'gold_loaded_at'
        ])
        .with_columns([
            pl.col('passing_yards').cum_sum().alias('passing_yards_cumulative'),
            pl.col('rushing_yards').cum_sum().alias('rushing_yards_cumulative'),
            pl.col('pass_touchdown').cum_sum().alias('pass_td_cumulative'),
            pl.col('rush_touchdown').cum_sum().alias('rush_td_cumulative'),
            pl.col('interception').cum_sum().alias('interceptions_cumulative'),
            pl.col('complete_pass').cum_sum().alias('completions_cumulative'),
            pl.col('pass_attempt').cum_sum().alias('attempts_cumulative'),
    ])
    )

def run_gold():
    load_dotenv()
    logger = setup_logger('season_progression_gold')

    db_url = os.getenv('DB_URL')
    if not db_url:
        raise EnvironmentError('Missing DB_URL in env')

    engine = create_engine(db_url)
    logger.info('Reading gold_qb_performance')

    df_gold = pl.read_database(
        'SELECT * FROM gold_qb_performance',
        connection=engine,
        infer_schema_length=None
    )
    if df_gold.is_empty():
        logger.warning('gold_qb_performance is empty, nothing to process')
        return

    df_progression = build_season_progression(df_gold)

    logger.info('Saving to postgres')
    df_progression.write_database(
        table_name= 'gold_season_progression',
        connection=os.getenv('DB_URL'),
        if_table_exists='replace',
    )

    logger.info(f'Gold finished - {df_progression.height} weeks processed')

if __name__ == '__main__':
    run_gold()