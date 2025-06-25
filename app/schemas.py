from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time, datetime

class ActionIn(BaseModel):
    game_id: int
    frame_id: int
    action_type: str
    player_track_id: int
    target_track_id: Optional[int]
    team: str
    game_time: str  # "00:04:21"


class ActionSchema(BaseModel):
    id: int
    game_id: int
    frame_id: int
    action_type: str
    player_id: int
    target_player_id: Optional[int] = None
    team: str
    game_time: Optional[time] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlayerSchema(BaseModel):
    id: int
    name: str
    jersey_number: Optional[int] = None
    team: Optional[str] = None
    position: Optional[str] = None

    class Config:
        from_attributes = True


class GameScoreSchema(BaseModel):
    team: str
    current_score: int

    class Config:
        from_attributes = True


class GameSchema(BaseModel):
    id: int
    date: date
    location: str
    team_a: str
    team_b: str
    scores: List[GameScoreSchema]

    class Config:
        from_attributes = True


class GamePlayerSchema(BaseModel):
    id: int
    player_id: int
    track_id: int
    team: str

    class Config:
        from_attributes = True


class GamePlayerDetailSchema(BaseModel):
    id: int
    player_id: int
    track_id: int
    team: str
    player: Optional[PlayerSchema] = None

    class Config:
        from_attributes = True


class GameDetailSchema(GameSchema):
    players: List[GamePlayerDetailSchema]
    actions: List[ActionSchema]

    class Config:
        from_attributes = True