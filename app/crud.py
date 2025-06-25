from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from datetime import time, datetime
from typing import List, Optional

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

def get_all_games(db: Session) -> List[models.Game]:
    """모든 게임과 점수 정보를 조회합니다."""
    return db.query(models.Game).options(
        joinedload(models.Game.scores)
    ).all()

def get_game_by_id(db: Session, game_id: int) -> Optional[models.Game]:
    """특정 게임의 상세 정보를 조회합니다 (점수 + 플레이어 정보 + 액션 정보)."""
    return db.query(models.Game).options(
        joinedload(models.Game.scores),
        joinedload(models.Game.players).joinedload(models.GamePlayer.player),
        joinedload(models.Game.actions)
    ).filter(models.Game.id == game_id).first()
