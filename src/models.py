import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DB_URL'))
Base = declarative_base()


class RawMayePlays(Base):
    __tablename__ = 'raw_maye_plays'
    # id = Column(Integer, primary_key=True)
    play_id = Column(Integer, primary_key=True)
    game_id = Column(String, primary_key=True)

    # Contexto
    season = Column(Integer)
    season_type = Column(String(20))
    game_date = Column(Date)
    week = Column(Integer)
    home_team = Column(String)
    away_team = Column(String)
    defteam = Column(String)

    # Situacion del juego
    drive = Column(Integer)
    qtr = Column(Integer)
    down = Column(Integer)
    yrdln = Column(String)
    desc = Column(Text)
    play_type = Column(String)

    # Meticas
    yards_gained = Column(Float)
    epa = Column(Float)
    qb_epa = Column(Float)
    air_epa = Column(Float)
    yac_epa = Column(Float)
    xyac_epa = Column(Float)
    cpoe = Column(Float)

    # Estadisticas de pase
    pass_attempt = Column(Integer)
    complete_pass = Column(Integer)
    passing_yards = Column(Float)
    air_yards = Column(Float)
    pass_touchdown = Column(Integer)
    interception = Column(Integer)
    sack = Column(Integer)
    pass_location = Column(String)
    td_team = Column(String)
    td_player_name = Column(String)

    # Estadisticas de carrera
    rush_attempt = Column(Integer)
    rushing_yards = Column(Float)
    rush_touchdown = Column(Integer)

    # Eventos
    fumble = Column(Integer)
    fumble_lost = Column(Integer)
    fumble_forced = Column(Integer)
    fumble_not_forced = Column(Integer)
    fumble_out_of_bounds = Column(Integer)
    two_point_conv_result = Column(String)


if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print('Esquema actualizado, la tabla ya tiene todo sobre drake maye. ')
