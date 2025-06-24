from sqlalchemy import Column, Integer, String, Date, ForeignKey, Time, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    jersey_number = Column(Integer)
    team = Column(String)
    position = Column(String)

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    location = Column(String)
    team_a = Column(String)
    team_b = Column(String)

class GamePlayer(Base):
    __tablename__ = "game_players"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    track_id = Column(Integer)
    team = Column(String)

class Frame(Base):
    __tablename__ = "frames"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    frame_num = Column(Integer)
    saved_at = Column(String)
    raw_detections = Column(JSONB)

class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    frame_id = Column(Integer, ForeignKey("frames.id"))
    action_type = Column(String)
    player_id = Column(Integer, ForeignKey("players.id"))
    target_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    team = Column(String)
    game_time = Column(Time)
    created_at = Column(String)
