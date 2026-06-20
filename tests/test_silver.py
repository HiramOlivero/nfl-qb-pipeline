import pytest
import polars as pl

from src.silver.silver import assert_expected_columns, add_features
def test_raises_when_missing_column():
    df = pl.DataFrame({
        'game_id' : ['2025_01_NE_BUF'],
        'week' : [1],
    })

    expected = ['game_id', 'week', 'season'] # Season is missing
    with pytest.raises(ValueError):
        assert_expected_columns(df, expected)

def test_passes_when_complete():
    df = pl.DataFrame({
        'game_id' : ['2025_01_NE_BUF'],
        'week' : [1],
        'season' : [2025],
    })
    expected = ['game_id', 'week', 'season']

    assert_expected_columns(df, expected)

def test_add_features_success_positive_epa():
    df = pl.DataFrame({
        'game_id' : ['2025_01_NE_BUF'],
        'opponent_team' : ['BUF'],
        'week' : [1],
        'season' : [2025],
        'epa': [1.25],
        'yard_line' : ['BUF 1'],
        'play_description' : ['Touchdwon NE'],
    })
    result = add_features(df)

    assert result['is_success'][0] == 1

def test_add_features_success_negative_epa():
    df = pl.DataFrame({
        'game_id': ['2025_01_NE_BUF'],
        'opponent_team': ['BUF'],
        'week': [1],
        'season': [2025],
        'epa': [-0.5],
        'yard_line': ['NE 30'],
        'play_description': ['Incomplete pass'],
    })

    result = add_features(df)

    assert result['is_success'][0] == 0




