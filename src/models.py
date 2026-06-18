from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base

# This file documents the Bronze layer schema.
# Tables are created automatically by the Bronze pipeline.
# Run this script only to reset the schema in a new environment.

load_dotenv()

engine = create_engine(os.getenv('DB_URL'))
Base = declarative_base()


class RawMayePlays(Base):
    __tablename__ = 'raw_maye_plays'

    # id's
    play_id = Column(Integer, primary_key=True)
    game_id = Column(String, primary_key=True)

    # Game context
    season = Column(Integer)
    season_type = Column(String(20))
    game_date = Column(Date)
    week = Column(Integer)
    home_team = Column(String)
    away_team = Column(String)
    defteam = Column(String)

    # Game situation
    drive = Column(Integer)
    qtr = Column(Integer)
    down = Column(Integer)
    yrdln = Column(String)
    desc = Column(Text)
    play_type = Column(String)

    # Advanced metrics
    yards_gained = Column(Float)
    epa = Column(Float)
    qb_epa = Column(Float)
    air_epa = Column(Float)
    yac_epa = Column(Float)
    xyac_epa = Column(Float)
    cpoe = Column(Float)

    # Passing stats
    pass_attempt = Column(Integer)
    complete_pass = Column(Integer)
    passing_yards = Column(Float)
    air_yards = Column(Float)
    yards_after_catch = Column(Float)
    pass_touchdown = Column(Integer)
    interception = Column(Integer)
    sack = Column(Integer)
    pass_location = Column(String)
    pass_length = Column(String)
    td_team = Column(String)
    td_player_name = Column(String)
    receiver_player_name = Column(String)

    # QB metrics
    qb_hit = Column(Integer)
    qb_scramble = Column(Integer)
    qb_dropback = Column(Integer)

    # Rushing stats
    rush_attempt = Column(Integer)
    rushing_yards = Column(Float)
    rush_touchdown = Column(Integer)

    # Fubmles & conversions
    fumble = Column(Integer)
    fumble_lost = Column(Integer)
    fumble_forced = Column(Integer)
    fumble_not_forced = Column(Integer)
    fumble_out_of_bounds = Column(Integer)
    two_point_conv_result = Column(String)

    # Scoreboard
    score_differential = Column(Integer)
    posteam_score =  Column(Integer)
    defteam_score = Column(Integer)

    # Audit
    bronze_loaded_at = Column(DateTime(timezone=True))

if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print('Schema updated succesfully ')
