
import polars as pl

from src.bronze.bronze import filter_plays


def test_passer_player_name_or_not():
    df = pl.DataFrame({
        'game_id' : ['g1', 'g1', 'g1'],
        'play_id' : [1, 2, 3],
        'passer_player_name' : ['D.Maye', None, None],
        'rusher_player_name' : [None, 'D.Maye', None],
        'receiver_player_name' : [None, None, 'D.Maye'],

    })

    result = filter_plays(df, 'D.Maye')

    assert result.height == 2
