import pytest
import polars as pl


from src.gold.qb_performance import build_qb_performance
from src.gold.efficiency import build_efficiency_gold
from src.gold.situational_splits import build_situational_splits



@pytest.fixture
def make_play():
    def _make_play(**overrides):

        base ={
        'game_id' : '2025_01-NE_BUF',
        'season' : 2025,
        'week' : 1,
        'season_type' : 'REG',
        'home_team' : 'NE',
        'away_team' : 'BUF',
        'opponent_team' : 'BUF',
        'pass_attempt' : 1,
        'complete_pass' : 1,
        'passing_yards' : 10,
        'pass_touchdown' : 0,
        'interception' : 0,
        'rushing_yards' : 30,
        'rush_touchdown' : 0,
        'rush_attempt' : 5,
        'sack' : 0,
        'fumble' : 0,
        'fumble_lost' : 0,
        'fumble_forced' : 0,
        'fumble_not_forced' : 0,
        'air_yards' : 180,
        'epa' : 0.25,
        'cpoe' : 5.2,
        'two_point_conv_result' : None,
    }
        base.update(overrides)
        return base
    return _make_play


@pytest.fixture
def make_silver_play():
    def _make_play(**overrides):
        base = {
            'game_id' : '2025_01_NE_BUF',
            'pass_attempt' : 1,
            'pass_length' : 'short',
            'pass_location' : 'right',
            'passing_yards' : 10,
            'rush_attempt' : 0,
            'rushing_yards' : 0,
            'rush_touchdown' : 0,
            'complete_pass' : 1,
            'air_yards' : 8,
            'yards_after_catch' : 4,
            'pass_touchdown' : 0,
            'interception' : 0,
            'epa' : 0.5,
            'cpoe' : 5.2,
            'sack' : 0,
            'fumble' : 0,
            'two_point_conv_result' : None,
            'score_diff' : 0,
            'down' : 1,
            'quarter' : 1,
            'home_team' : 'NE',
        }
        base.update(overrides)
        return base
    return _make_play


def test_passer_rating_range(make_play):
    df = pl.DataFrame([make_play()])
    result = build_qb_performance(df)
    assert result ['passer_rating'].max() <= 158.3
    assert result ['completion_pct'].min() >= 0

def test_completion_pct_range(make_play):
    df = pl.DataFrame([make_play()])
    result = build_qb_performance(df)
    assert result['completion_pct'].max() <= 100
    assert  result['completion_pct'].min() >= 0

def test_exlcudes_sack(make_play):
    df = pl.DataFrame([
        make_play(),
        make_play(sack=1, complete_pass=0, passing_yards=0, epa=-1.5 ),
    ])
    result = build_qb_performance(df)
    assert result['pass_attempt'][0] == 1


def test_efficiency_aggregation(make_silver_play):
    df_silver = pl.DataFrame([
        make_silver_play(air_yards=10, yards_after_catch=5, epa=1.0, cpoe= 10.0),
        make_silver_play(air_yards=6, yards_after_catch=3, epa= 0.0, cpoe= 0.0),
        make_silver_play(pass_length='deep', pass_location='middle', air_yards=30, yards_after_catch=0)

    ])

    result = build_efficiency_gold(df_silver)
    assert result.height == 2

def test_efficiency_zero_division(make_silver_play):
    df_silver = pl.DataFrame([
        make_silver_play(complete_pass = 0, air_yards =15, yards_after_catch=0)

    ])
    result = build_efficiency_gold(df_silver)
    assert result['yac_per_reception'][0] == 0.0
    assert result['completion_pct'][0] == 0.0

def test_efficiency_drop_nulls(make_silver_play):
    df_silver = pl.DataFrame([
        make_silver_play(pass_length='short'),
        make_silver_play(pass_length=None)
    ])

    result = build_efficiency_gold(df_silver)
    assert result.height == 1

def test_score_bucket_categorization(make_silver_play):
    df = pl.DataFrame([
        make_silver_play(score_diff =-20, down =1, quarter =1, home_team='NE'),
        make_silver_play(score_diff=-7, down=1, quarter=1, home_team= 'NE'),
        make_silver_play(score_diff=0, down=1, quarter=1, home_team='NE'),
        make_silver_play(score_diff=7, down=1, quarter=1, home_team='NE'),
        make_silver_play(score_diff=21, down=1, quarter=1,home_team='NE'),

    ])
    result = build_situational_splits(df)
    buckets = result['score_bucket'].to_list()

    assert 'Losing big' in buckets
    assert 'Losing' in buckets
    assert 'Tied' in buckets
    assert 'Winning' in buckets
    assert 'Winning big' in buckets





