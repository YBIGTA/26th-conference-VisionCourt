from sqlalchemy import Column, Integer, String, Date, ForeignKey, Time, Text, JSON
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
    
    # 관계 설정
    scores = relationship("GameScore", back_populates="game")
    players = relationship("GamePlayer", back_populates="game")
    actions = relationship("Action", back_populates="game")

class GameScore(Base):
    __tablename__ = "game_scores"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    team = Column(String)
    current_score = Column(Integer, default=0)
    
    # 관계 설정
    game = relationship("Game", back_populates="scores")

class GamePlayer(Base):
    __tablename__ = "game_players"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    track_id = Column(Integer)
    team = Column(String)
    
    # 관계 설정
    game = relationship("Game", back_populates="players")
    player = relationship("Player")

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
    
    # 관계 설정
    game = relationship("Game", back_populates="actions")
