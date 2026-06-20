from unittest import result

import pytest
import polars as pl


from src.gold.gold_qb_performance import build_qb_performance


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





