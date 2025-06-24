from pydantic import BaseModel
from typing import Optional

class ActionIn(BaseModel):
    game_id: int
    frame_id: int
    action_type: str
    player_track_id: int
    target_track_id: Optional[int]
    team: str
    game_time: str  # "00:04:21"
