from sqlalchemy.orm import Session
from app import models, schemas
from datetime import time, datetime

def insert_action_from_json(db: Session, action_data: schemas.ActionIn):
    player = db.query(models.GamePlayer).filter(
        models.GamePlayer.game_id == action_data.game_id,
        models.GamePlayer.track_id == action_data.player_track_id
    ).first()

    target = None
    if action_data.target_track_id is not None:
        target = db.query(models.GamePlayer).filter(
            models.GamePlayer.game_id == action_data.game_id,
            models.GamePlayer.track_id == action_data.target_track_id
        ).first()

    if not player:
        raise Exception("player_track_id not found")

    new_action = models.Action(
        game_id=action_data.game_id,
        frame_id=action_data.frame_id,
        action_type=action_data.action_type,
        player_id=player.player_id,
        target_player_id=target.player_id if target else None,
        team=action_data.team,
        game_time=time.fromisoformat(action_data.game_time),
        created_at=datetime.utcnow().isoformat()
    )

    db.add(new_action)
    db.commit()
    db.refresh(new_action)
    return new_action
